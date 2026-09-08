"""The math text face option, its root attribute, and its config key.

The face itself (the `KPress Math Text` composite and the metrics asset) is
pinned by the asset-contract tests; this file pins the Python surface: the
option, the attribute the CSS keys on, and the `format.math_text_font` config
key that feeds it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from kpress.contract import PUBLIC_FORMAT_API, PUBLIC_TEMPLATE_VARIABLES
from kpress.errors import KPressPublishError
from kpress.format import DocumentInput, RenderOptions, render_fragment, render_page
from kpress.format.model import MathTextFont

DOCUMENT = DocumentInput(
    title="Doc",
    source_text="# Doc\n\nBody with $x + 1$.\n",
    body_markdown="# Doc\n\nBody with $x + 1$.\n",
    source_path="doc.md",
)


def _render(math_text_font: MathTextFont | None) -> str:
    options = (
        RenderOptions() if math_text_font is None else RenderOptions(math_text_font=math_text_font)
    )
    return render_page(DOCUMENT, options).html


def test_default_math_text_font_is_prose() -> None:
    assert RenderOptions().math_text_font == "prose"
    assert 'data-kpress-math-text="prose"' in _render(None)


def test_katex_math_text_font_sets_root_attribute() -> None:
    # On <html>, beside the other reader-state attributes: the CSS scopes the
    # composite faces to the root attribute, and a host stamps its own root.
    html = _render("katex")
    assert '<html lang="en"' in html
    assert 'data-kpress-math-text="katex"' in html
    assert 'data-kpress-math-text="prose"' not in html


def test_fragment_bakes_no_math_text_attribute() -> None:
    # Fragments are host-state-agnostic, like theme and palette: the absence of
    # the attribute means "prose" to the CSS, so an embed gets the feature and
    # a host that wants KaTeX's faces stamps `katex` on its own root.
    fragment = render_fragment(DOCUMENT, RenderOptions(math_text_font="katex"))
    assert "data-kpress-math-text" not in fragment.html


def test_public_contract_lists_the_option() -> None:
    assert "math_text_font" in PUBLIC_TEMPLATE_VARIABLES["page.html.jinja"]
    assert "MathTextFont" in PUBLIC_FORMAT_API


def test_format_config_math_text_font_yaml_round_trip(tmp_path: Path) -> None:
    from kpress.publish.config import load_config

    config = tmp_path / "kpress.yml"
    config.write_text("sources:\n  - path: .\n", encoding="utf-8")
    assert load_config(config).format.math_text_font == "prose"

    config.write_text("sources:\n  - path: .\nformat:\n  math_text_font: katex\n", encoding="utf-8")
    assert load_config(config).format.math_text_font == "katex"


def test_invalid_math_text_font_fails_the_config(tmp_path: Path) -> None:
    from kpress.publish.config import load_config

    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: .\nformat:\n  math_text_font: pt-serif\n", encoding="utf-8"
    )
    with pytest.raises(KPressPublishError, match="format.math_text_font"):
        _ = load_config(config)


def test_invalid_programmatic_math_text_font_fails_validation() -> None:
    from typing import cast

    from kpress.publish import FormatConfig, KPressConfig, validate_config

    config = KPressConfig(format=FormatConfig(math_text_font=cast("MathTextFont", "pt-serif")))
    with pytest.raises(KPressPublishError, match="format.math_text_font"):
        _ = validate_config(config)


def test_build_site_threads_math_text_font(tmp_path: Path) -> None:
    # The config key must reach RenderOptions: a validated-but-unthreaded field
    # silently has no effect (see test_build_site_threads_color_mode_and_diagrams).
    from kpress.publish import FormatConfig, KPressConfig, PublishConfig, SourceConfig, build_site

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n\nBody with $x + 1$.\n", encoding="utf-8")

    def _build(out: str, **fmt: object) -> str:
        _ = build_site(
            KPressConfig(
                base_dir=tmp_path,
                sources=[SourceConfig(path=docs)],
                format=FormatConfig(**fmt),  # pyright: ignore[reportArgumentType]
                publish=PublishConfig(output_dir=tmp_path / out),
            )
        )
        return (tmp_path / out / "index.html").read_text(encoding="utf-8")

    assert 'data-kpress-math-text="prose"' in _build("default")
    assert 'data-kpress-math-text="katex"' in _build("katex", math_text_font="katex")
