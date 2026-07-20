from __future__ import annotations

import pytest

from kpress.format import (
    DocumentInput,
    RenderOptions,
    parse_markdown,
    read_package_text,
    render_fragment,
    render_page,
)
from kpress.format.markdown import _is_numeric_cell_text  # pyright: ignore[reportPrivateUsage]


@pytest.mark.parametrize(
    "text",
    [
        # Plain integers
        "0",
        "1000",
        "-12",
        "+12",
        # Comma-grouped thousands
        "1,000",
        "1,000,000",
        "12,345",
        # Decimals
        "1.000",
        "123.45",
        "0.5",
        # Leading-dot decimals (no integer part)
        ".5",
        ".25",
        ".001",
        "-.5",
        "+.25",
        # Percent
        "50%",
        "12.45%",
        ".5%",
        "1,000%",
        # Currency: $ (USD and other dollar currencies)
        "$12.4",
        "$ 12.45",
        "$1,000",
        "$.5",
        "-$12.45",
        "+$100",
        "$12%",
        # Currency: € (EUR)
        "€1.000",
        "€ 500",
        "€.99",
        "-€12.45",
        # Currency: ¥ (JPY and CNY — same glyph)
        "¥100",
        "¥ 1,000",
        "¥.50",
        "-¥500",
        # Currency: £ (GBP)
        "£12.45",
        "£ 3.50",
        "£.99",
        "-£7",
        # Currency: ₹ (INR)
        "₹1,000",
        "₹ 500",
        "₹.50",
        "-₹100",
        # Currency: ₩ (KRW)
        "₩10,000",
        "₩ 500",
        "₩.50",
        "-₩1,000",
        # Currency: ¢ (cents)
        "¢50",
        "¢.99",
        "-¢5",
        # Currency: ₽ (RUB)
        "₽1,000",
        "₽ 500",
        "₽.50",
        "-₽100",
    ],
)
def test_numeric_cell_accepts_numbers_and_currency(text: str) -> None:
    assert _is_numeric_cell_text(text)


@pytest.mark.parametrize(
    "text",
    [
        # Letters and words
        "abc",
        "N/A",
        "12abc",
        "USD",
        "EUR",
        # Symbol alone (no digits)
        "$",
        "€",
        "¥",
        "£",
        "₹",
        "₩",
        "¢",
        "₽",
        # Empty / whitespace
        "",
        "  ",
        # Dot alone (no digits)
        ".",
        "$.",
        # Multiple dots
        "1.2.3",
        # Comma not in thousands position (bad grouping)
        "1,00",
        ",000",
        "1,00,000",
    ],
)
def test_numeric_cell_rejects_non_numbers(text: str) -> None:
    assert not _is_numeric_cell_text(text)


def test_markdown_renders_rich_document_contract() -> None:
    tree = parse_markdown(
        """# Title

Intro with [link](#details) and footnote.[^a]

| A | B |
| - | - |
| 1 | 2 |

- [x] Done

```mermaid
graph TD
```

[^a]: Footnote text.
""",
        title="Title",
    )

    assert tree.headings[0].id == "title"
    assert '<div class="kpress-table-wrap">' in tree.html
    assert "kpress-task" in tree.html
    assert "kpress-mermaid" in tree.html
    assert "kpress-footnotes" in tree.html


def _table_markdown(columns: int, cell: str, rows: int = 2) -> str:
    header = "| " + " | ".join(f"H{i} {cell}" for i in range(columns)) + " |"
    divider = "| " + " | ".join("---" for _ in range(columns)) + " |"
    body = "| " + " | ".join(f"{cell} {i}" for i in range(columns)) + " |"
    return "\n".join([header, divider, *([body] * rows)])


def test_large_tables_are_marked_wide() -> None:
    # 6 columns x ~20 chars per cell: over the cutoff on both axes.
    tree = parse_markdown(_table_markdown(6, "verbose cell text"), title="T")
    assert '<div class="kpress-table-wrap" data-kpress-table-scale="wide">' in tree.html


def test_small_tables_are_not_marked_wide() -> None:
    # Two short columns: under the cutoff on both axes.
    tree = parse_markdown(_table_markdown(2, "x"), title="T")
    assert "data-kpress-table-scale" not in tree.html


def test_wide_cutoff_is_host_tunable() -> None:
    # Hosts lower (or raise) the cutoff per render; a table small under the
    # defaults qualifies under a permissive threshold.
    tree = parse_markdown(
        _table_markdown(2, "moderately sized cell"),
        title="T",
        table_wide_min_columns=2,
        table_wide_min_row_chars=10,
    )
    assert 'data-kpress-table-scale="wide"' in tree.html


def test_resolved_wide_cutoff_is_stamped_on_the_article_root() -> None:
    # The client runtime re-classifies tables, so the server's resolved cutoff
    # must travel with the document: js/tables.js reads these stamps as its
    # default thresholds (explicit runtime config still wins). Without them a
    # custom cutoff's wide marks would be undone on browser startup.
    markdown = _table_markdown(2, "moderately sized cell")
    document = DocumentInput(
        title="T",
        source_text=markdown,
        source_path="t.md",
        body_markdown=markdown,
        trust_mode="sanitized",
    )
    default_render = render_fragment(document, RenderOptions())
    assert 'data-kpress-table-wide-min-columns="6"' in default_render.html
    assert 'data-kpress-table-wide-min-row-chars="100"' in default_render.html
    custom = render_fragment(
        document,
        RenderOptions(table_wide_min_columns=2, table_wide_min_row_chars=10),
    )
    assert 'data-kpress-table-wide-min-columns="2"' in custom.html
    assert 'data-kpress-table-wide-min-row-chars="10"' in custom.html
    assert 'data-kpress-table-scale="wide"' in custom.html


def test_wide_mark_requires_both_axes() -> None:
    # Many columns but terse rows (6 cols x ~3 chars): column cutoff alone
    # must not qualify.
    narrow_rows = parse_markdown(_table_markdown(6, "x"), title="T")
    assert "data-kpress-table-scale" not in narrow_rows.html
    # Long rows but few columns (2 cols x ~60 chars): char cutoff alone must
    # not qualify either.
    few_columns = parse_markdown(
        _table_markdown(2, "an exhaustively verbose description of the cell contents here"),
        title="T",
    )
    assert "data-kpress-table-scale" not in few_columns.html


def test_footnote_refs_render_sequential_numbers() -> None:
    tree = parse_markdown(
        "First.[^one] Second.[^two]\n\n[^one]: One.\n[^two]: Two.\n",
        title="Footnotes",
    )

    # Visible markers are sequential numbers, not the authored labels...
    assert 'data-kpress-footnote-ref="one">1</a></sup>' in tree.html
    assert 'data-kpress-footnote-ref="two">2</a></sup>' in tree.html
    # ...while the labels still back the anchor ids.
    assert 'href="#fn-one"' in tree.html
    assert 'id="fn-two"' in tree.html


def test_render_page_includes_assets_theme_and_toc() -> None:
    page = render_page(
        DocumentInput(
            title="Doc",
            source_text="# One\n\n## Two\n\n### Three\n",
            source_path="doc.md",
            body_markdown="# One\n\n## Two\n\n### Three\n",
        ),
        RenderOptions(include_toc="on", asset_url_prefix="/assets/"),
    )

    assert page.html.startswith("<!doctype html>")
    assert 'data-kpress-theme="system"' in page.html
    assert "kpress.theme" in page.html
    assert "<script>" in page.html.partition("/assets/js/theme.js")[0]
    # The settings widget is client-rendered (no-JS rule): the server emits only
    # its positioned mount, never the menu markup or chooser segments.
    assert (
        '<div class="kpress-widget kpress-settings kpress-no-print" '
        'id="kpress-settings" data-kpress-widget="settings"></div>'
    ) in page.html
    assert "kpress-settings-menu" not in page.html
    assert "data-kpress-theme-choice" not in page.html
    assert 'class="kpress-toc kpress-no-print"' in page.html
    assert "/assets/css/document.css" in page.html
    assert "/assets/js/theme.js" in page.html


def test_enabled_widgets_each_get_a_mount_element() -> None:
    page = render_page(
        DocumentInput(
            title="Doc", source_text="# Body", source_path="doc.md", body_markdown="# Body"
        ),
        RenderOptions(include_toc="off", widgets={"minimap": {"depth": 2}}),
    )

    assert (
        '<div class="kpress-widget kpress-minimap kpress-no-print" '
        'id="kpress-minimap" data-kpress-widget="minimap"></div>'
    ) in page.html
    # The default settings mount is still present alongside.
    assert 'data-kpress-widget="settings"' in page.html


def test_render_page_ports_standalone_social_metadata() -> None:
    page = render_page(
        DocumentInput(
            title="Social Doc",
            source_text="# Social Doc\n\nBody",
            source_path="social.md",
            body_markdown="# Social Doc\n\nBody",
            metadata={
                "description": "A readable KPress document.",
                "image": "images/card.png",
                "url": "https://example.test/social",
                "site_name": "KPress",
                "twitter_handle": "kpressdocs",
            },
        )
    )

    assert '<meta property="og:title" content="Social Doc">' in page.html
    assert '<meta property="og:description" content="A readable KPress document.">' in page.html
    assert '<meta property="og:image" content="images/card.png">' in page.html
    assert '<meta property="og:url" content="https://example.test/social">' in page.html
    assert '<meta property="og:site_name" content="KPress">' in page.html
    assert '<meta name="twitter:site" content="@kpressdocs">' in page.html
    assert '<main class="kpress-page-main kpress-viewport" data-kpress-viewport>' in page.html
    # The body is the non-scrolling frame that pins floating UI (TOC toggle/drawer,
    # settings); the scrolling viewport itself must never be a fixed containing block.
    assert '<body class="kpress-frame" data-kpress-frame>' in page.html


def test_render_page_outputs_document_thumbnail_when_available() -> None:
    page = render_page(
        DocumentInput(
            title="With Thumbnail",
            source_text="# With Thumbnail\n\nBody",
            source_path="thumb.md",
            body_markdown="# With Thumbnail\n\nBody",
            metadata={
                "thumbnail_url": "assets/thumb.png",
                "thumbnail_alt": "Preview image",
            },
        ),
        RenderOptions(include_toc="off"),
    )

    assert (
        '<img class="thumbnail kpress-image" src="assets/thumb.png" '
        'alt="Preview image" data-kpress-image="true" loading="lazy">'
    ) in page.html
    assert page.html.index('class="thumbnail kpress-image"') < page.html.index(
        '<div class="kpress-prose'
    )


def test_public_static_sanitizes_unsafe_html() -> None:
    page = render_page(
        DocumentInput(
            title="Unsafe",
            source_text='<script>alert("x")</script>\n# Safe',
            source_path="unsafe.md",
            body_markdown='<script>alert("x")</script>\n# Safe',
            trust_mode="sanitized",
        )
    )

    assert "<script>alert" not in page.html
    assert "html_sanitized" in str(page.diagnostics)


def test_render_page_surfaces_frontmatter_parse_errors() -> None:
    page = render_page(
        DocumentInput(
            title="Bad frontmatter",
            source_text="# Body",
            source_path="bad.md",
            body_markdown="# Body",
            frontmatter_error="YAML: expected ':' near <tag>",
        ),
        RenderOptions(include_toc="off"),
    )

    assert 'class="kpress-frontmatter-error"' in page.html
    assert 'role="alert"' in page.html
    assert "Frontmatter error" in page.html
    assert "YAML: expected &#x27;:&#x27; near &lt;tag&gt;" in page.html
    assert page.diagnostics == [
        {
            "message": "YAML: expected ':' near <tag>",
            "severity": "warning",
            "type": "frontmatter_error",
        }
    ]


def test_show_frontmatter_toggles_the_frontmatter_disclosure() -> None:
    doc = DocumentInput(
        title="Doc",
        source_text="# Body",
        source_path="doc.md",
        body_markdown="# Body",
        frontmatter={"title": "Doc", "draft": True},
    )

    shown = render_page(doc, RenderOptions(include_toc="off")).html
    assert "<summary>Frontmatter</summary>" in shown
    assert "<dt>draft</dt>" in shown

    hidden = render_page(doc, RenderOptions(include_toc="off", show_frontmatter=False)).html
    assert "<summary>Frontmatter</summary>" not in hidden


def test_widgets_map_toggles_the_settings_chrome() -> None:
    doc = DocumentInput(
        title="Doc",
        source_text="# Body",
        source_path="doc.md",
        body_markdown="# Body",
        frontmatter={"title": "Doc"},
    )

    shown = render_page(doc, RenderOptions(include_toc="off")).html
    assert 'id="kpress-settings"' in shown

    hidden = render_page(doc, RenderOptions(include_toc="off", widgets={"settings": "off"})).html
    assert "kpress-settings" not in hidden


def _page_model(html: str):  # -> dict[str, Any]: keep Any so tests index freely
    import json
    import re

    match = re.search(
        r'<script type="application/json" id="kpress-page-model">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match, "page-model block missing"
    return json.loads(match.group(1))


def test_page_model_block_carries_contract_keys() -> None:
    doc = DocumentInput(
        title="Doc",
        source_text="# Alpha\n\nText.\n\n## Beta\n\nMore.",
        source_path="doc.md",
        body_markdown="# Alpha\n\nText.\n\n## Beta\n\nMore.",
        logical_path="/notes/doc",
        frontmatter={"title": "Doc"},
    )
    model = _page_model(
        render_page(
            doc,
            RenderOptions(
                include_toc="on",
                toc_min_headings=1,
                widgets={"settings": {"choosers": ["theme", "reading-font"]}},
            ),
        ).html
    )
    assert model["version"] == 1
    assert model["title"] == "Doc"
    assert model["route"] == "/notes/doc"
    assert model["profile"] == "document"
    from typing import Any, cast

    headings = cast("list[dict[str, Any]]", model["headings"])
    assert isinstance(headings, list) and headings
    assert {"level", "title", "href"} <= set(headings[0])
    # Widget config is opaque: passed through verbatim.
    assert model["widgets"] == {"settings": {"choosers": ["theme", "reading-font"]}}


def test_page_model_defaults_settings_on_and_off_removes_it() -> None:
    doc = DocumentInput(
        title="Doc", source_text="# Body", source_path="doc.md", body_markdown="# Body"
    )
    default_model = _page_model(render_page(doc, RenderOptions(include_toc="off")).html)
    assert "settings" in default_model["widgets"]

    off_model = _page_model(
        render_page(doc, RenderOptions(include_toc="off", widgets={"settings": "off"})).html
    )
    assert "settings" not in off_model["widgets"]


def test_page_model_block_is_script_safe() -> None:
    doc = DocumentInput(
        title='</script><script>alert("x")&',
        source_text="# Body",
        source_path="doc.md",
        body_markdown="# Body",
    )
    html = render_page(doc, RenderOptions(include_toc="off")).html
    model = _page_model(html)
    assert model["title"] == '</script><script>alert("x")&'
    # The raw payload must not contain an unescaped closing tag.
    import re

    block = re.search(r'id="kpress-page-model">(.*?)</script>', html, re.DOTALL)
    assert block and "</script" not in block.group(1)


def test_diagnostics_script_block_is_valid_json_and_script_safe() -> None:
    import json
    import re

    page = render_page(
        DocumentInput(
            title="Bad frontmatter",
            source_text="# Body",
            source_path="bad.md",
            body_markdown="# Body",
            frontmatter_error="YAML: expected ':' near </script><tag>",
        ),
        RenderOptions(include_toc="off"),
    )

    match = re.search(
        r'<script type="application/json" id="kpress-diagnostics">(.*?)</script>',
        page.html,
        re.DOTALL,
    )
    assert match is not None
    payload = match.group(1)
    # No raw "</script>" can appear inside the block (breakout safety).
    assert "</script>" not in payload
    # The advertised application/json content really parses as JSON and
    # round-trips to the stable diagnostic dicts.
    assert json.loads(payload) == page.diagnostics


def test_source_profile_truncates_large_source_with_visible_warning() -> None:
    source_text = ("0123456789abcdef" * 40000) + "tail"

    fragment = render_fragment(
        DocumentInput(
            title="large.log",
            source_text=source_text,
            source_path="large.log",
            metadata={"size": len(source_text.encode("utf-8"))},
        ),
        RenderOptions(print_profile="source", asset_policy="none"),
    )

    assert 'class="kpress-source-truncation-warning"' in fragment.html
    assert "Source preview truncated." in fragment.html
    assert "512 KiB" in fragment.html
    assert "tail" not in fragment.html
    assert len(fragment.html) < len(source_text)


def test_template_resource_is_packaged() -> None:
    assert "<!doctype html>" in read_package_text("templates/page.html.jinja")


def test_show_doc_header_toggles_rendered_doc_header() -> None:
    # No body H1, so the title is not otherwise on the page and the header
    # renders when enabled; the toggle still removes it.
    md = "## Section A\n\nbody\n\n## Section B\n\nmore"
    doc = DocumentInput(title="Title", source_text=md, source_path="d.md", body_markdown=md)

    with_header = render_fragment(doc, RenderOptions())
    without_header = render_fragment(doc, RenderOptions(show_doc_header=False))

    assert "kpress-doc-header" in with_header.html
    assert 'aria-labelledby="kpress-title-title"' in with_header.html

    assert "kpress-doc-header" not in without_header.html
    # With no header to name, the article falls back to an aria-label.
    assert 'aria-label="Title"' in without_header.html


def test_doc_header_suppressed_when_single_h1_matches_title() -> None:
    # One leading H1 equal to the title: that H1 is the visible title, so a
    # separate header would duplicate it and is suppressed.
    md = "# Title\n\n## Section A\n\nbody"
    doc = DocumentInput(title="Title", source_text=md, source_path="d.md", body_markdown=md)

    rendered = render_fragment(doc, RenderOptions())

    assert "kpress-doc-header" not in rendered.html
    assert "<h1" in rendered.html  # the lone body H1 still carries the title
    assert 'aria-label="Title"' in rendered.html


def test_doc_header_rendered_when_first_h1_differs_from_title() -> None:
    md = "# Different Heading\n\n## Section A\n\nbody"
    doc = DocumentInput(title="Title", source_text=md, source_path="d.md", body_markdown=md)

    rendered = render_fragment(doc, RenderOptions())

    assert "kpress-doc-header" in rendered.html


def test_doc_header_rendered_when_multiple_h1s() -> None:
    md = "# Title\n\nintro\n\n# Second Part\n\nbody"
    doc = DocumentInput(title="Title", source_text=md, source_path="d.md", body_markdown=md)

    rendered = render_fragment(doc, RenderOptions())

    assert "kpress-doc-header" in rendered.html


def test_resolve_widgets_removes_only_explicit_off_values() -> None:
    """Only `False` and `"off"` mean off. Integer 0 (`0 == False`) is not a
    presence marker and must not silently remove a widget; the normalizing
    parsers reject it upstream."""

    from kpress.format.model import resolve_widgets

    resolved = resolve_widgets({"minimap": 0, "gone": "off", "also-gone": False})
    assert "gone" not in resolved
    assert "also-gone" not in resolved
    assert resolved["minimap"] == 0
    assert resolved["settings"] == "on"
