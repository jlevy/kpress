from __future__ import annotations

import json
from pathlib import Path

from kpress.format.assets import (
    KATEX_CSS_ASSETS,
    KATEX_FONT_ASSETS,
    KATEX_JS_ASSETS,
    KATEX_VERSION,
    read_package_text,
)
from kpress.publish import BuildOptions, build_site


def test_mathml_namespace_uri_is_emitted_for_inline_math(tmp_path: Path) -> None:
    """A document containing inline math emits the MathML namespace URI."""

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text(
        "# Math\n\nEinstein wrote $E = mc^2$ inline.\n",
        encoding="utf-8",
    )
    config = tmp_path / "kpress.yml"
    config.write_text(
        """sources:
  - path: docs

publish:
  asset_mode: hashed
  output_dir: public
""",
        encoding="utf-8",
    )

    build_site(config, BuildOptions(asset_mode="hashed"))

    html = (tmp_path / "public" / "index.html").read_text(encoding="utf-8")
    assert "http://www.w3.org/1998/Math/MathML" in html


def test_no_math_document_has_zero_math_assets(tmp_path: Path) -> None:
    """A document with no math must produce zero KaTeX/math assets in output.

    Lazy auto detection means a document without math delimiters never loads
    math CSS, JS, fonts, or any other math-related resource.
    """

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text(
        "# No Math Here\n\nJust plain text, no formulas.\n",
        encoding="utf-8",
    )
    config = tmp_path / "kpress.yml"
    config.write_text(
        """sources:
  - path: docs

publish:
  asset_mode: hashed
  output_dir: public

format:
  math: auto
""",
        encoding="utf-8",
    )

    build_site(config, BuildOptions(asset_mode="hashed"))

    output_dir = tmp_path / "public"
    html = (output_dir / "index.html").read_text(encoding="utf-8")

    assert "kpress-math" not in html
    assert "katex" not in html.lower()
    assert "<math " not in html

    all_files = [str(p.relative_to(output_dir)) for p in output_dir.rglob("*") if p.is_file()]
    katex_files = [f for f in all_files if "katex" in f.lower()]
    assert katex_files == [], f"KaTeX assets found in no-math output: {katex_files}"

    manifest_path = output_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        asset_ids = [str(a.get("path", "")) for a in manifest.get("assets", [])]
        math_assets = [a for a in asset_ids if "katex" in a.lower() or "math" in a.lower()]
        assert math_assets == [], f"Math assets in manifest for no-math doc: {math_assets}"


def test_math_document_emits_vendored_katex_bundle(tmp_path: Path) -> None:
    """A math document copies the vendored KaTeX bundle into the output tree.

    KaTeX is the only active renderer; the server-rendered MathML stays as the
    semantic/accessibility output.
    """

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text(
        "# Math\n\nInline $E = mc^2$ and display:\n\n$$\\int_0^1 x^2 dx$$\n",
        encoding="utf-8",
    )
    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: docs\n\n"
        "publish:\n  asset_mode: hashed\n  output_dir: public\n\n"
        "format:\n  math: auto\n",
        encoding="utf-8",
    )

    build_site(config, BuildOptions(asset_mode="hashed"))

    output_dir = tmp_path / "public"
    html = (output_dir / "index.html").read_text(encoding="utf-8")

    assert 'data-kpress-math-renderer="katex"' in html
    assert 'class="kpress-math-semantic"' in html
    assert "http://www.w3.org/1998/Math/MathML" in html
    assert "/_kpress/assets/katex/katex.min.css" in html
    assert "/_kpress/assets/katex/katex.min.js" in html
    assert "/_kpress/assets/katex/katex-init.js" in html

    assert KATEX_VERSION == "0.16.45"  # pinned: last KaTeX before the cutoff
    for rel in (*KATEX_CSS_ASSETS, *KATEX_JS_ASSETS, *KATEX_FONT_ASSETS):
        assert (output_dir / "_kpress" / "assets" / rel).is_file(), rel
    katex_root = output_dir / "_kpress" / "assets" / "katex"
    woff2 = sorted((katex_root / "fonts").glob("*.woff2"))
    assert len(woff2) == len(KATEX_FONT_ASSETS)
    css = (katex_root / "katex.min.css").read_text(encoding="utf-8")
    assert ".woff)" not in css and ".ttf)" not in css

    manifest = json.loads(
        (output_dir / "_kpress" / "kpress-manifest.json").read_text(encoding="utf-8")
    )
    katex_assets = [a for a in manifest["assets"] if str(a.get("path", "")).startswith("katex/")]
    katex_paths = sorted(str(a["path"]) for a in katex_assets)
    for expected in (*KATEX_CSS_ASSETS, *KATEX_JS_ASSETS, *KATEX_FONT_ASSETS):
        assert expected in katex_paths, f"missing KaTeX asset in manifest: {expected}"


def test_vendored_katex_css_uses_font_display_swap() -> None:
    """KaTeX @font-face must use ``swap`` so a late math face is a repaint, not an
    invisible-text gap. KaTeX lays out from precomputed metrics, so ``swap`` is
    safe.
    """
    css = read_package_text("katex/katex.min.css")
    assert "font-display:swap" in css
    assert "font-display:block" not in css
