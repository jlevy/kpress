"""The KPress icon set lives in one SVG sprite (static/icons/icons.svg). Server chrome and
client JS reference its symbols via `<use>`; no SVG glyph markup is authored in Python or
JS (the design-system-in-front-end-files rule)."""

from __future__ import annotations

from pathlib import Path

from kpress.format.assets import read_package_text

_FORMAT_ROOT = Path(__file__).resolve().parents[1] / "src/kpress/format"

_REQUIRED_ICONS = (
    "settings",
    "monitor",
    "sun",
    "moon",
    "x",
    "copy",
    "check",
    "maximize",
    "external-link",
    "list",
    "triangle-alert",
)


def test_sprite_defines_the_named_glyphs_on_the_stroke_grid() -> None:
    sprite = read_package_text("icons/icons.svg")
    for name in _REQUIRED_ICONS:
        assert f'id="kpress-icon-{name}"' in sprite, name
    # Stroke icons on a 24x24 grid, colored by CSS `currentColor`.
    assert sprite.count('viewBox="0 0 24 24"') >= len(_REQUIRED_ICONS)
    assert 'stroke="currentColor"' in sprite


def test_no_icon_svg_geometry_is_authored_in_python_or_js() -> None:
    render_src = (_FORMAT_ROOT / "render.py").read_text(encoding="utf-8")
    # Chrome references the sprite; the Lucide glyph data is gone from Python.
    assert "#kpress-icon-" in render_src
    assert "M9.671 4.136" not in render_src  # the old inline gear path
    assert 'viewBox="0 0 24 24"' not in render_src
    for rel in ("static/js/icons.js", "static/js/code-copy.js"):
        text = (_FORMAT_ROOT / rel).read_text(encoding="utf-8")
        for geometry in ("<path", "<rect", "<circle", "<line", "<polygon"):
            assert geometry not in text, f"{rel} should not inline SVG geometry ({geometry})"


def test_code_copy_references_the_shared_icon_helper() -> None:
    code_copy = (_FORMAT_ROOT / "static/js/code-copy.js").read_text(encoding="utf-8")
    assert 'from "./icons.js"' in code_copy
    assert 'icon("copy")' in code_copy
    assert 'icon("check")' in code_copy
