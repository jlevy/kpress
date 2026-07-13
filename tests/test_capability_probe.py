"""Tests for the shared capability-probe function and optimizer preflight."""

from __future__ import annotations

import importlib
import shutil
from pathlib import Path
from typing import Any

import pytest

from kpress.errors import KPressMissingOptionalDependencyError
from kpress.publish.optimize import full_optimizer_available

needs_full = pytest.mark.skipif(
    not full_optimizer_available(), reason="full optimizer requires Node/npm"
)


def _stub_which(name: str) -> None:
    _ = name
    return


def _tool_path(_name: str) -> str:
    return "/tool"


# --- Capability probe function ---


def test_probe_optimizer_full_reports_current_readiness() -> None:
    from kpress.publish.capability import probe_capability
    from kpress.publish.optimize import optimizer_cache_ready

    result = probe_capability("optimizer_full")
    if not full_optimizer_available():
        assert result.status in {"unavailable", "fail"}
    elif not optimizer_cache_ready():
        assert result.status == "skipped"
    else:
        assert result.status == "ok"


def test_probe_optimizer_full_unavailable_when_node_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kpress.publish.capability import probe_capability

    monkeypatch.setattr(shutil, "which", _stub_which)
    result = probe_capability("optimizer_full")
    assert result.status in {"unavailable", "fail"}
    assert result.reason is not None
    assert "node" in result.reason


def test_probe_optimizer_cold_cache_requires_network_permission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kpress.publish import capability, optimize

    monkeypatch.setattr(shutil, "which", _tool_path)
    monkeypatch.setattr(optimize, "optimizer_cache_ready", lambda: False)

    def unexpected_bootstrap(*, allow_network: bool) -> Path:
        raise AssertionError(f"bootstrap called with allow_network={allow_network}")

    monkeypatch.setattr(optimize, "ensure_tool_cache", unexpected_bootstrap)

    result = capability.probe_capability("optimizer_full", allow_network=False)

    assert result.status == "skipped"
    assert result.reason == "fetch_blocked"


def test_probe_optimizer_allow_network_bootstraps_cold_cache(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from kpress.publish import capability, optimize

    monkeypatch.setattr(shutil, "which", _tool_path)
    monkeypatch.setattr(optimize, "optimizer_cache_ready", lambda: False)
    calls: list[bool] = []

    def bootstrap(*, allow_network: bool) -> Path:
        calls.append(allow_network)
        return tmp_path

    monkeypatch.setattr(optimize, "ensure_tool_cache", bootstrap)

    result = capability.probe_capability("optimizer_full", allow_network=True)

    assert result.status == "ok"
    assert calls == [True]


def test_build_preflight_never_bootstraps_over_network(monkeypatch: pytest.MonkeyPatch) -> None:
    from kpress.publish import capability, optimize

    calls: list[bool] = []

    def ensure_cache(*, allow_network: bool) -> Path:
        calls.append(allow_network)
        return Path("/warm-cache")

    monkeypatch.setattr(optimize, "ensure_tool_cache", ensure_cache)

    capability.preflight_optimizer_full()

    assert calls == [False]


def test_probe_precompress_brotli_reports_availability() -> None:
    from kpress.publish.capability import probe_capability

    result = probe_capability("precompress_brotli")
    # brotli may or may not be installed, but the probe must return a valid status
    assert result.status in {"ok", "unavailable", "fail", "skipped"}


def test_probe_precompress_brotli_unavailable_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kpress.publish.capability import probe_capability

    real_import_module = importlib.import_module

    def import_without_brotli(name: str, package: str | None = None) -> Any:
        if name == "brotli":
            raise ModuleNotFoundError("brotli")
        return real_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", import_without_brotli)
    result = probe_capability("precompress_brotli")
    assert result.status in {"unavailable", "fail"}


def test_probe_pdf_browser_reports_availability() -> None:
    from kpress.publish.capability import probe_capability

    result = probe_capability("pdf_browser")
    assert result.status in {"ok", "unavailable", "fail", "skipped"}


def test_probe_render_always_ok() -> None:
    from kpress.publish.capability import probe_capability

    result = probe_capability("render")
    assert result.status == "ok"


def test_probe_publish_always_ok() -> None:
    from kpress.publish.capability import probe_capability

    result = probe_capability("publish")
    assert result.status == "ok"


def test_probe_status_is_closed_set() -> None:
    from kpress.publish.capability import CapabilityStatus

    # The status type should only allow these four values
    valid: set[CapabilityStatus] = {"ok", "unavailable", "skipped", "fail"}
    assert len(valid) == 4


def test_probe_result_has_stable_shape() -> None:
    from kpress.publish.capability import ProbeResult

    r = ProbeResult(status="ok")
    assert r.status == "ok"
    assert r.reason is None

    r2 = ProbeResult(status="fail", reason="node_not_found")
    assert r2.status == "fail"
    assert r2.reason == "node_not_found"


# --- Optimizer preflight in build_site / build_html ---


def test_build_html_full_preflight_fails_before_writing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When optimizer=full and Node is missing, build_html raises before writing output."""
    from kpress.publish import BuildOptions, build_html

    monkeypatch.setattr(shutil, "which", _stub_which)
    dest = tmp_path / "output" / "page.html"
    with pytest.raises(KPressMissingOptionalDependencyError, match=r"Node|html-minifier"):
        build_html("<p>hello</p>", dest, BuildOptions(optimizer="full"))
    # The output directory should not have been created
    assert not dest.exists()
    assert not dest.parent.exists()


def test_build_site_full_preflight_fails_with_untouched_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When optimizer=full and Node is missing, build_site raises with no output written."""
    from kpress.publish import BuildOptions, build_site

    monkeypatch.setattr(shutil, "which", _stub_which)

    # Create a minimal kpress site
    site_dir = tmp_path / "site"
    site_dir.mkdir()
    (site_dir / "index.md").write_text("# Hello\n\nWorld.\n", encoding="utf-8")
    config = site_dir / "kpress.yml"
    config.write_text(
        "site:\nsources:\n  - path: .\npublish:\n  output_dir: public\n",
        encoding="utf-8",
    )
    output_dir = site_dir / "public"

    with pytest.raises(KPressMissingOptionalDependencyError, match=r"Node|html-minifier"):
        build_site(config, BuildOptions(optimizer="full", output_dir=output_dir))

    # Output tree should be empty or non-existent
    if output_dir.exists():
        written = list(output_dir.rglob("*"))
        assert len(written) == 0, f"Output tree should be empty, found: {written}"


def test_build_html_none_mode_does_not_preflight(
    tmp_path: Path,
) -> None:
    """optimizer=none does not require Node and writes output normally."""
    from kpress.publish import BuildOptions, build_html

    dest = tmp_path / "page.html"
    report = build_html("<p>hello</p>", dest, BuildOptions(optimizer="none"))
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "<p>hello</p>"
    assert report.files


@needs_full
def test_build_html_full_preflight_passes_and_builds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicitly bootstrapped optimizer cache supports a network-free build."""
    from kpress.publish import BuildOptions, build_html
    from kpress.publish.capability import probe_capability

    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    assert probe_capability("optimizer_full", allow_network=True).status == "ok"

    dest = tmp_path / "page.html"
    report = build_html("<main>\n  <p>x</p>\n</main>\n", dest, BuildOptions(optimizer="full"))
    assert dest.exists()
    assert report.files
