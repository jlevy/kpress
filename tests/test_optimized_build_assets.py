"""Optimized hashed/sealed builds: every emitted asset reference must resolve.

In hashed/sealed modes the page is rendered against raw-package-byte hashes,
the emitted files are hashed from their *optimized* bytes, and
``_rewrite_package_asset_urls`` reconciles the two across the final HTML —
import-map values included. These tests pin that reconciliation with a
deterministic byte-changing optimizer (no Node required): if the rewrite ever
misses a reference class, a published optimized site would 404 its assets.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import kpress.publish.build as build_module
from kpress.publish import build_site
from kpress.publish.optimize import optimize_text

_HASHED_REF = re.compile(r"_kpress/assets/(?P<rel>[\w./-]+\.[0-9a-f]{16}\.(?:js|css|woff2))")


def _fake_optimize_text(content: str, *, kind: str, backend: str | None = "none") -> str:
    """Byte-changing stand-in for the full optimizer (same signature)."""

    if backend == "none":
        return optimize_text(content, kind=kind, backend="none")
    if kind == "css":
        return content + "\n/* minified */\n"
    if kind == "js":
        return content + "\n// minified\n"
    if kind == "html":
        return content.replace("</body>", "<!-- minified --></body>")
    return content


@pytest.mark.parametrize("asset_mode", ["hashed", "sealed"])
def test_optimized_build_asset_refs_resolve_to_emitted_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, asset_mode: str
) -> None:
    monkeypatch.setattr(build_module, "optimize_text", _fake_optimize_text)
    import kpress.publish.capability as capability

    monkeypatch.setattr(capability, "preflight_optimizer_full", lambda: None)

    (tmp_path / "index.md").write_text(
        "# Home\n\nProse with `code` and a [link](about).\n", encoding="utf-8"
    )
    (tmp_path / "about.md").write_text("# About\n\nMore.\n", encoding="utf-8")
    config = tmp_path / "kpress.yml"
    config.write_text(
        f"sources:\n  - path: .\npublish:\n  output_dir: public\n  asset_mode: {asset_mode}\n"
        "optimizer:\n  mode: full\n",
        encoding="utf-8",
    )

    report = build_site(config)
    output_dir = tmp_path / "public"
    emitted = {
        path.relative_to(output_dir).as_posix() for path in output_dir.rglob("*") if path.is_file()
    }

    checked = 0
    for page in ("index.html", "about.html"):
        html = (output_dir / page).read_text(encoding="utf-8")
        assert '<script type="importmap">' in html
        refs = {match.group(0).lstrip("/") for match in _HASHED_REF.finditer(html)}
        assert refs, f"{page} references no hashed assets"
        dangling = sorted(ref for ref in refs if ref not in emitted)
        assert not dangling, f"{page} references files that were not emitted: {dangling}"
        checked += len(refs)
    # The reference set must cover both CSS links and the JS import map.
    assert checked >= 10
    assert report.optimizer_backend == "full"


def test_optimized_build_import_map_values_match_emitted_js(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    monkeypatch.setattr(build_module, "optimize_text", _fake_optimize_text)
    import kpress.publish.capability as capability

    monkeypatch.setattr(capability, "preflight_optimizer_full", lambda: None)

    (tmp_path / "index.md").write_text("# Home\n\n`code`\n", encoding="utf-8")
    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: .\npublish:\n  output_dir: public\n  asset_mode: sealed\n"
        "optimizer:\n  mode: full\n",
        encoding="utf-8",
    )
    build_site(config)
    output_dir = tmp_path / "public"
    html = (output_dir / "index.html").read_text(encoding="utf-8")
    raw = re.search(r'<script type="importmap">(.*?)</script>', html, re.DOTALL)
    assert raw is not None
    imports: dict[str, str] = json.loads(raw.group(1))["imports"]
    assert imports
    for target in imports.values():
        rel = target.lstrip("/")
        assert (output_dir / rel).is_file(), f"import map target {target} was not emitted"
