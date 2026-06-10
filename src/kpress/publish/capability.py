"""Shared capability-probe functions for KPress runtime readiness.

This module provides the single capability-probe function shared by the
``kpress doctor`` CLI subcommand and the ``optimizer=full`` preflight in
``build_site()``/``build_html()``.

Each probe checks whether a specific optional capability is available on the
current machine without performing network access (unless explicitly allowed).
"""

from __future__ import annotations

import importlib
import importlib.util
import platform
import shutil
from dataclasses import dataclass
from typing import Any, Literal, cast

from kpress._version import __version__
from kpress.errors import KPressMissingOptionalDependencyError

CapabilityStatus = Literal["ok", "unavailable", "skipped", "fail"]

CAPABILITY_NAMES = (
    "render",
    "publish",
    "optimizer_full",
    "precompress_brotli",
    "pdf_browser",
)


@dataclass(frozen=True)
class ProbeResult:
    """Result of probing one optional capability."""

    status: CapabilityStatus
    reason: str | None = None


def probe_capability(name: str, *, allow_network: bool = False) -> ProbeResult:
    """Probe one capability and return its status.

    This is the single source of truth for capability readiness, shared by
    ``kpress doctor`` and the ``optimizer=full`` preflight.

    No probe performs network access unless *allow_network* is True and the
    probe explicitly requires it (only the optimizer cold-cache smoke).
    """

    if name == "render":
        return _probe_render()
    if name == "publish":
        return _probe_publish()
    if name == "optimizer_full":
        return _probe_optimizer_full(allow_network=allow_network)
    if name == "precompress_brotli":
        return _probe_precompress_brotli()
    if name == "pdf_browser":
        return _probe_pdf_browser()
    return ProbeResult(status="unavailable", reason="unknown_capability")


def preflight_optimizer_full() -> None:
    """Preflight the full optimizer toolchain.

    Raises ``KPressMissingOptionalDependencyError`` if npx is not on PATH.
    This is called at the start of build operations with optimizer=full,
    before any output is written.
    """

    result = probe_capability("optimizer_full")
    if result.status not in {"ok", "skipped"}:
        from kpress.publish.optimize import MISSING_FULL_OPTIMIZER_MESSAGE

        raise KPressMissingOptionalDependencyError(MISSING_FULL_OPTIMIZER_MESSAGE)


def probe_all(*, allow_network: bool = False) -> dict[str, ProbeResult]:
    """Probe all capabilities and return a mapping of name to result."""

    return {name: probe_capability(name, allow_network=allow_network) for name in CAPABILITY_NAMES}


def platform_info() -> dict[str, str]:
    """Return version and platform information for doctor output."""

    return {
        "kpress_version": __version__,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
    }


# --- Individual probe implementations ---


def _probe_render() -> ProbeResult:
    """Core render is always available (pure Python, no optional deps)."""

    try:
        importlib.import_module("kpress.format")
        return ProbeResult(status="ok")
    except ImportError as exc:
        return ProbeResult(status="fail", reason=f"import_error: {exc}")


def _probe_publish() -> ProbeResult:
    """Static publish is always available (pure Python, no optional deps).

    Uses ``find_spec`` rather than importing ``kpress.publish.build`` so this
    readiness probe does not create a static import cycle with the build
    pipeline (which defers ``preflight_optimizer_full`` back into this module).
    """

    try:
        if importlib.util.find_spec("kpress.publish.build") is None:
            return ProbeResult(status="fail", reason="import_error: build spec missing")
        return ProbeResult(status="ok")
    except (ImportError, ValueError, ModuleNotFoundError) as exc:
        return ProbeResult(status="fail", reason=f"import_error: {exc}")


def _probe_optimizer_full(*, allow_network: bool = False) -> ProbeResult:
    """Check whether the full optimizer toolchain (npx + html-minifier-next) is present.

    The npx presence check is always no-network. The cold-cache package smoke
    (which may fetch html-minifier-next via npx) runs only when *allow_network*
    is True; otherwise the package-level check is skipped with reason
    ``fetch_blocked``.
    """

    _ = allow_network  # reserved for the cold-cache smoke in doctor
    if shutil.which("npx") is None:
        return ProbeResult(status="unavailable", reason="npx_not_found")
    return ProbeResult(status="ok")


def _probe_precompress_brotli() -> ProbeResult:
    """Check whether the brotli library is importable."""

    try:
        importlib.import_module("brotli")
        return ProbeResult(status="ok")
    except ModuleNotFoundError:
        return ProbeResult(status="unavailable", reason="brotli_not_installed")


def _probe_pdf_browser() -> ProbeResult:
    """Check whether Playwright and a browser are available for PDF export."""

    try:
        importlib.import_module("playwright")
    except ModuleNotFoundError:
        return ProbeResult(status="unavailable", reason="playwright_not_installed")

    # Playwright is importable; check for a browser binary. The Playwright
    # types are not resolvable when the optional dependency is absent (CI),
    # so access it through an explicitly Any-typed module handle.
    try:
        sync_api = cast(Any, importlib.import_module("playwright.sync_api"))
        with sync_api.sync_playwright() as player:
            _ = player.chromium.executable_path
            return ProbeResult(status="ok")
    except Exception as exc:  # noqa: BLE001
        # Do not eat the failure: surface why Chromium could not load so
        # `kpress doctor` says exactly what is wrong (missing browser binary,
        # launch error, sandbox issue, etc.).
        detail = f"{type(exc).__name__}: {exc}".strip().replace("\n", " ")
        return ProbeResult(status="unavailable", reason=f"chromium_not_available: {detail}")
