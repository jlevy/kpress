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
from pathlib import Path
from typing import Any, Literal, cast

from kpress._version import __version__
from kpress.errors import (
    KPressMissingOptionalDependencyError,
    KPressOptimizerError,
)

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

    This performs a deterministic locked-cache bootstrap when needed. It is called
    at the start of build operations with optimizer=full, before any output is
    created, purged, or written.
    """

    from kpress.publish.optimize import ensure_tool_cache

    _ = ensure_tool_cache(allow_network=True)


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
    """Check whether Node and the locked html-minifier-next cache are ready.

    A warm-cache check never accesses the network. A cold cache is reported as skipped
    unless *allow_network* is true, in which case this probe performs the same reviewed
    ``npm ci`` bootstrap used by the build preflight.
    """

    from kpress.publish.optimize import ensure_tool_cache, optimizer_cache_ready

    if shutil.which("node") is None:
        return ProbeResult(status="unavailable", reason="node_not_found")
    if optimizer_cache_ready():
        return ProbeResult(status="ok")
    if shutil.which("npm") is None:
        return ProbeResult(status="unavailable", reason="npm_not_found")
    if not allow_network:
        return ProbeResult(status="skipped", reason="fetch_blocked")
    try:
        _ = ensure_tool_cache(allow_network=True)
        return ProbeResult(status="ok")
    except (KPressMissingOptionalDependencyError, KPressOptimizerError) as exc:
        return ProbeResult(status="fail", reason=f"bootstrap_failed: {exc}")


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
            executable = Path(player.chromium.executable_path)
            if not executable.is_file():
                return ProbeResult(
                    status="unavailable",
                    reason="chromium_not_installed: run playwright install chromium",
                )
            return ProbeResult(status="ok")
    except Exception as exc:
        # Do not eat the failure: surface why Chromium could not load so
        # `kpress doctor` says exactly what is wrong (missing browser binary,
        # launch error, sandbox issue, etc.).
        detail = f"{type(exc).__name__}: {exc}".strip().replace("\n", " ")
        return ProbeResult(status="unavailable", reason=f"chromium_not_available: {detail}")
