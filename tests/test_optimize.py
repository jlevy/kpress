from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

from kpress.errors import KPressMissingOptionalDependencyError, KPressOptimizerError
from kpress.format import DocumentInput, RenderOptions, render_page
from kpress.publish import BuildOptions, build_html
from kpress.publish.optimize import (
    full_optimizer_available,
    get_optimizer,
    optimize_file,
    optimize_text,
    precompress_file,
)

needs_full = pytest.mark.skipif(
    not full_optimizer_available(), reason="full optimizer requires Node/npx"
)


def _stub_which(name: str) -> None:
    _ = name
    return


# --- Two modes only: none and full. ---


def test_none_mode_publishes_content_unchanged() -> None:
    optimizer = get_optimizer("none")
    assert optimizer.name == "none"
    html = "<main>\n  <p>x</p>\n</main>\n"
    result = optimizer.optimize(html, kind="html")
    assert result.content == html
    assert result.changed is False
    assert optimize_text(".x {\n  color: red;\n}\n", kind="css") == ".x {\n  color: red;\n}\n"


def test_default_optimizer_is_none() -> None:
    assert get_optimizer().name == "none"
    assert get_optimizer(None).name == "none"


def test_full_mode_resolves_to_full_optimizer() -> None:
    optimizer = get_optimizer("full")
    assert optimizer.name == "full"


def test_unknown_optimizer_mode_raises() -> None:
    with pytest.raises(KPressOptimizerError, match="Unknown"):
        get_optimizer("builtin")
    with pytest.raises(KPressOptimizerError, match="Unknown"):
        get_optimizer("sminify")


def test_full_optimizer_errors_when_node_unavailable_no_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(shutil, "which", _stub_which)
    with pytest.raises(KPressMissingOptionalDependencyError, match=r"html-minifier-next|npx"):
        get_optimizer("full").optimize("<p>  x  </p>", kind="html")


@needs_full
def test_full_optimizer_minifies_deterministically() -> None:
    optimizer = get_optimizer("full")
    first = optimizer.optimize("<main>\n  <p>x</p>\n</main>\n", kind="html")
    second = optimizer.optimize("<main>\n  <p>x</p>\n</main>\n", kind="html")
    assert first.content == second.content
    assert first.backend == "full"
    assert first.changed is True
    assert "  " not in first.content.replace("\n", "")


def test_full_optimizer_skips_non_web_content() -> None:
    result = get_optimizer("full").optimize("plain text", kind="other")
    assert result.changed is False
    assert result.content == "plain text"


def test_strip_exact_wrapper_requires_exact_wrapper_tags() -> None:
    from kpress.publish.optimize import strip_exact_wrapper

    assert strip_exact_wrapper("<style>.x{}</style>", "style") == ".x{}"
    assert strip_exact_wrapper("<script>x()</script>", "script") == "x()"
    assert strip_exact_wrapper("anything", None) == "anything"
    # A rewritten wrapper (attributes, case, or missing) is a hard error, never
    # a silent slice of the payload.
    for mangled in (
        '<style media="all">.x{}</style>',
        "<STYLE>.x{}</STYLE>",
        ".x{}",
        "<style>.x{}",
    ):
        with pytest.raises(KPressOptimizerError):
            strip_exact_wrapper(mangled, "style")


def test_dynamic_rendering_does_not_import_optimizer() -> None:
    sys.modules.pop("kpress.publish.optimize", None)
    render_page(
        DocumentInput(
            title="Doc",
            source_text="# Doc\n",
            body_markdown="# Doc\n",
            source_path="doc.md",
        ),
        RenderOptions(),
    )
    assert "kpress.publish.optimize" not in sys.modules


# --- build_html with the optimizer modes ---


def test_build_html_none_keeps_content_and_omits_optimizer_metadata(tmp_path: Path) -> None:
    report = build_html(
        "<main>\n  <p>x</p>\n</main>\n",
        tmp_path / "page.html",
        BuildOptions(optimizer="none", precompress=["gzip"]),
    )
    assert (tmp_path / "page.html").read_text(encoding="utf-8") == "<main>\n  <p>x</p>\n</main>\n"
    assert any(file.path == "page.html.gz" for file in report.files)
    manifest = report.as_dict()
    assert manifest["pipeline"] == []
    html_files = [f for f in manifest["files"] if f["kind"] == "html"]
    assert html_files[0]["applied_pipeline"] == []
    assert html_files[0].get("original_size") is None


@needs_full
def test_build_html_full_minifies_and_records_metadata(tmp_path: Path) -> None:
    report = build_html(
        "<main>\n  <p>x</p>\n</main>\n",
        tmp_path / "page.html",
        BuildOptions(optimizer="full", precompress=["gzip"]),
    )
    assert (tmp_path / "page.html").read_text(encoding="utf-8") == "<main><p>x</p></main>\n"
    manifest = report.as_dict()
    assert manifest["pipeline"] == ["full"]
    assert "gzip" in manifest["precompress"]
    html_files = [f for f in manifest["files"] if f["kind"] == "html"]
    assert "original_size" in html_files[0]
    assert html_files[0]["applied_pipeline"] == ["full"]
    gz_files = [f for f in manifest["files"] if f["kind"] == "gz"]
    assert gz_files[0]["compression"] == "gzip"
    assert gz_files[0]["source_path"] == "page.html"


# --- Precompression is independent of the optimizer and needs no Node. ---


def test_precompression_writes_deterministic_gzip(tmp_path: Path) -> None:
    source = tmp_path / "page.html"
    source.write_text("<p>x</p>\n", encoding="utf-8")
    outputs = precompress_file(source, methods=["gzip"])
    assert outputs[0].path == "page.html.gz"
    assert (tmp_path / "page.html.gz").exists()
    assert outputs[0].content_hash
    assert outputs[0].compression == "gzip"
    assert outputs[0].source_path == "page.html"
    # RFC 1952 byte 9 is the OS byte. python-build-standalone's zlib stamps
    # 0x03 (Linux) on some hosts and 0xff (Unknown) on others, which would
    # otherwise yield different bytes for identical inputs across CI hosts.
    raw = (tmp_path / "page.html.gz").read_bytes()
    assert raw[9:10] == b"\xff", f"non-deterministic OS byte: {raw[9]:#04x}"
    # MTIME bytes (4..8) must also be zeroed for reproducibility.
    assert raw[4:8] == b"\x00\x00\x00\x00"


def test_brotli_missing_extra_error_is_clear(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "page.html"
    source.write_text("<p>x</p>\n", encoding="utf-8")
    real_import_module = importlib.import_module

    def import_without_brotli(name: str, package: str | None = None) -> Any:
        if name == "brotli":
            raise ModuleNotFoundError("brotli")
        return real_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", import_without_brotli)
    with pytest.raises(KPressMissingOptionalDependencyError, match=r"kpress\[optimize\]"):
        precompress_file(source, methods=["br"])


def test_precompress_brotli_records_compression_method(tmp_path: Path) -> None:
    source = tmp_path / "page.html"
    source.write_text("<p>hello world</p>\n", encoding="utf-8")
    try:
        outputs = precompress_file(source, methods=["br"])
    except KPressMissingOptionalDependencyError:
        pytest.skip("brotli not installed")
    assert outputs[0].compression == "br"
    assert outputs[0].source_path == "page.html"


# --- optimize_file metadata ---


def test_optimize_file_none_records_metadata(tmp_path: Path) -> None:
    source = tmp_path / "data.txt"
    source.write_text("unchanged content", encoding="utf-8")
    original_size = source.stat().st_size
    output = optimize_file(source, kind="other", backend="none")
    assert output.original_size == original_size
    assert output.applied_pipeline == []
    assert output.size == original_size


def test_output_file_serialization_includes_optimizer_metadata() -> None:
    from kpress.publish.manifest import OutputFile

    optimized = OutputFile(
        path="page.html",
        kind="html",
        content_hash="abc123",
        size=100,
        original_size=150,
        applied_pipeline=["full"],
    )
    d = optimized.as_dict()
    assert d["original_size"] == 150
    assert d["applied_pipeline"] == ["full"]

    plain = OutputFile(path="page.html", kind="html", content_hash="abc123", size=100)
    d = plain.as_dict()
    assert "original_size" not in d
    assert d["applied_pipeline"] == []


def test_output_file_serialization_includes_compression_metadata() -> None:
    from kpress.publish.manifest import OutputFile

    compressed = OutputFile(
        path="page.html.gz",
        kind="gz",
        content_hash="def456",
        size=50,
        compression="gzip",
        source_path="page.html",
    )
    d = compressed.as_dict()
    assert d["compression"] == "gzip"
    assert d["source_path"] == "page.html"

    plain = OutputFile(path="page.html", kind="html", content_hash="abc123", size=100)
    d = plain.as_dict()
    assert "compression" not in d
    assert "source_path" not in d
