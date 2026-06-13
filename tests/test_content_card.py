from __future__ import annotations

from pathlib import Path

from kpress.format import DocumentInput, RenderOptions, render_page

STATIC_CSS = Path(__file__).resolve().parents[1] / "src/kpress/format/static/css"


def _render(content_card: bool | None) -> str:
    options = RenderOptions() if content_card is None else RenderOptions(content_card=content_card)
    return render_page(
        DocumentInput(
            title="Doc",
            source_text="# Doc\n\nBody\n",
            body_markdown="# Doc\n\nBody\n",
            source_path="doc.md",
        ),
        options,
    ).html


def test_content_card_defaults_on() -> None:
    assert 'data-kpress-card="on"' in _render(None)


def test_content_card_off_stamps_off() -> None:
    assert 'data-kpress-card="off"' in _render(False)


def test_components_css_keys_card_chrome_on_attribute() -> None:
    import re

    css = (STATIC_CSS / "components.css").read_text(encoding="utf-8")
    # Chrome engages only when the article opts in. Vertical padding is fine
    # (breathing room around the text); anything horizontal would disturb the
    # coupled TOC/table width system, so inline/width properties stay out.
    rule = css.split('.kpress[data-kpress-card="on"] .kpress-long-text', 1)[1].split("}", 1)[0]
    declarations = re.sub(r"/\*.*?\*/", "", rule, flags=re.DOTALL)
    assert "--kpress-card-border" in declarations
    assert "--kpress-card-shadow" in declarations
    assert "padding-block" in declarations
    for width_prop in ("padding-inline", "padding:", "margin", "width", "display", "position"):
        assert width_prop not in declarations


def test_card_tokens_defined_with_dark_shadow() -> None:
    css = (STATIC_CSS / "style-tokens.css").read_text(encoding="utf-8")
    assert "--kpress-card-border:" in css
    assert css.count("--kpress-card-shadow:") == 2  # base + dark override


def test_card_chrome_never_prints() -> None:
    css = (STATIC_CSS / "print.css").read_text(encoding="utf-8")
    long_text = css.split(".kpress-long-text", 1)[1].split("}", 1)[0]
    assert "border: none" in long_text
    assert "box-shadow: none" in long_text


def test_format_config_card_yaml_round_trip(tmp_path: Path) -> None:
    from kpress.publish.config import load_config

    config = tmp_path / "kpress.yml"
    config.write_text("sources:\n  - path: .\n", encoding="utf-8")
    assert load_config(config).format.content_card is True

    config.write_text("sources:\n  - path: .\nformat:\n  content_card: false\n", encoding="utf-8")
    assert load_config(config).format.content_card is False


def test_format_config_show_doc_header_yaml_round_trip(tmp_path: Path) -> None:
    from kpress.publish.config import load_config

    config = tmp_path / "kpress.yml"
    config.write_text("sources:\n  - path: .\n", encoding="utf-8")
    assert load_config(config).format.show_doc_header is True

    config.write_text(
        "sources:\n  - path: .\nformat:\n  show_doc_header: false\n", encoding="utf-8"
    )
    assert load_config(config).format.show_doc_header is False
