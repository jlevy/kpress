from __future__ import annotations

from pathlib import Path
from typing import cast

from kpress.format import DocumentInput, RenderOptions, render_page
from kpress.format.model import FontMode, ProseFont

STYLE_TOKENS = Path(__file__).resolve().parents[1] / "src/kpress/format/static/css/style-tokens.css"


def _render(font_mode: FontMode | None) -> str:
    options = RenderOptions() if font_mode is None else RenderOptions(font_mode=font_mode)
    return render_page(
        DocumentInput(
            title="Doc",
            source_text="# Doc\n\nBody\n",
            body_markdown="# Doc\n\nBody\n",
            source_path="doc.md",
        ),
        options,
    ).html


def test_default_font_mode_is_custom() -> None:
    assert 'data-kpress-fonts="custom"' in _render(None)


def test_system_font_mode_sets_root_attribute() -> None:
    assert 'data-kpress-fonts="system"' in _render("system")


def test_style_tokens_define_system_font_override() -> None:
    css = STYLE_TOKENS.read_text(encoding="utf-8")
    assert '.kpress[data-kpress-fonts="system"]' in css
    # System mode must not pull in the vendored reader faces.
    override = css.split('.kpress[data-kpress-fonts="system"]', 1)[1].split("}", 1)[0]
    assert "PT Serif" not in override
    assert "Source Sans 3 Variable" not in override
    assert "system-ui" in override


def _render_prose_font(prose_font: str | None) -> str:
    options = (
        RenderOptions()
        if prose_font is None
        else RenderOptions(prose_font=cast(ProseFont, prose_font))
    )
    return render_page(
        DocumentInput(
            title="Doc",
            source_text="# Doc\n\nBody\n",
            body_markdown="# Doc\n\nBody\n",
            source_path="doc.md",
        ),
        options,
    ).html


def test_default_prose_font_is_serif() -> None:
    assert 'data-kpress-prose-font="serif"' in _render_prose_font(None)


def test_sans_prose_font_sets_root_attribute() -> None:
    # On <html>, not the .kpress wrapper: the reader's persisted choice
    # overrides the same root attribute, so the site default stays a default.
    html = _render_prose_font("sans")
    assert '<html lang="en"' in html
    assert 'data-kpress-prose-font="sans"' in html
    assert 'class="kpress kpress-doc kpress-print-surface" data-kpress-prose-font' not in html


def test_style_tokens_define_sans_prose_override() -> None:
    css = STYLE_TOKENS.read_text(encoding="utf-8")
    assert '[data-kpress-prose-font="sans"] .kpress' in css
