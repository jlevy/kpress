from __future__ import annotations

from textwrap import dedent

from kpress.format import DocumentInput, RenderOptions, parse_markdown, render_page


def test_gfm_markdown_document_tree_covers_nested_blocks_and_inline_features() -> None:
    tree = parse_markdown(
        dedent(
            """
            # Repeated

            ## Repeated

            > Quoted **strong** text

            1. Parent
               1. Child

            - [x] Done
            - [ ] Todo

            Visit <https://example.com> and ~~remove this~~.

            ![Chart](assets/chart.png)
            """
        ).strip(),
        title="Reader parity",
    )

    assert [heading.id for heading in tree.headings] == ["repeated", "repeated-2"]
    assert "<blockquote>\n<p>Quoted <strong>strong</strong> text</p>\n</blockquote>" in tree.html
    assert "<ol>" in tree.html
    assert "kpress-task" in tree.html
    assert 'type="checkbox"' in tree.html
    assert 'checked="checked"' in tree.html
    assert 'disabled="disabled"' in tree.html
    assert (
        '<a href="https://example.com" target="_blank" '
        'rel="noopener noreferrer">https://example.com</a>'
    ) in tree.html
    assert "<s>remove this</s>" in tree.html
    assert (
        '<figure class="kpress-figure" data-kpress-figure="image">\n'
        '<img src="assets/chart.png" alt="Chart" class="kpress-image" '
        'data-kpress-image="true" loading="lazy">\n'
        "</figure>"
    ) in tree.html


def test_standalone_markdown_images_render_as_figures_with_captions() -> None:
    tree = parse_markdown(
        dedent(
            """
            ![Revenue chart](assets/revenue.png "Quarterly revenue")

            Inline image ![Sparkline](assets/spark.png "Sparkline") stays inline.

            <figure id="raw"><img src="assets/raw.png"><figcaption>Raw caption</figcaption></figure>
            """
        ).strip(),
        title="Images",
    )

    assert (
        '<figure class="kpress-figure" data-kpress-figure="image">\n'
        '<img src="assets/revenue.png" alt="Revenue chart" class="kpress-image" '
        'data-kpress-image="true" loading="lazy">\n'
        '<figcaption class="kpress-figcaption">Quarterly revenue</figcaption>\n'
        "</figure>"
    ) in tree.html
    assert (
        'Inline image <img src="assets/spark.png" alt="Sparkline" title="Sparkline" '
        'class="kpress-image" data-kpress-image="true" loading="lazy"> stays inline.'
    ) in tree.html
    assert (
        '<figure id="raw" class="kpress-figure"><img src="assets/raw.png" '
        'class="kpress-image" data-kpress-image="true" loading="lazy">'
        '<figcaption class="kpress-figcaption">Raw caption</figcaption></figure>'
    ) in tree.html


def test_semantic_component_authoring_generates_kash_and_textpress_classes() -> None:
    tree = parse_markdown(
        dedent(
            """
            [Important]{.highlight} [Filing]{.citation}

            {.subtitle}
            A compact subtitle.

            {.debug}
            Parser hint.

            ::: hero
            # Hero Title
            :::

            :::: key-claims
            ::: claim
            First claim.
            :::
            ::::

            ::: summary
            Short summary.
            :::

            ::: concepts
            - Alpha
            - Beta
            :::

            :::: annotated-para
            ::: para-caption
            Caption.
            :::
            ::: para
            Body paragraph.
            :::
            ::::

            ![Frame](assets/frame.jpg){.frame-capture}

            {.shaded-text}
            ::: boxed-text
            Boxed copy.
            :::

            ::: centered-headers
            ## Centered
            :::

            ::: justify
            Paragraph text.
            :::

            {.kpress-long-list}
            1. First long-list item
            2. Second long-list item

            :::: video-gallery
            ::: video-item
            <iframe src="https://www.youtube.com/embed/demo" title="Demo"></iframe>
            :::
            ::::
            """
        ).strip(),
        title="Semantic",
    )

    for expected in [
        '<span class="highlight">Important</span>',
        '<span class="citation">Filing</span>',
        '<p class="subtitle">A compact subtitle.</p>',
        '<p class="debug">Parser hint.</p>',
        '<div class="hero">',
        '<div class="key-claims">',
        '<div class="claim">',
        '<div class="summary">',
        '<div class="concepts">',
        '<div class="annotated-para">',
        '<div class="para-caption">',
        '<div class="para">',
        'class="frame-capture kpress-image"',
        '<div class="shaded-text boxed-text">',
        '<div class="centered-headers">',
        '<div class="justify">',
        '<ol class="kpress-long-list">',
        '<div class="video-gallery">',
        '<div class="video-item">',
    ]:
        assert expected in tree.html
    assert ":::" not in tree.html


def test_youtube_iframes_render_as_no_network_video_placeholders() -> None:
    tree = parse_markdown(
        '<iframe src="https://www.youtube.com/embed/demo?start=12" title="Demo video"></iframe>',
        title="Video",
        trust_mode="public-static",
    )

    assert "https://www.youtube.com" not in tree.html
    assert "<iframe" not in tree.html
    assert (
        '<button type="button" class="kpress-video-placeholder" '
        'data-kpress-video-id="demo" data-kpress-video-start="12" '
        'data-kpress-video-title="Demo video" aria-label="Open video: Demo video">'
    ) in tree.html
    assert (
        '<span class="kpress-video-placeholder-action" aria-hidden="true">Play</span>' in tree.html
    )
    assert '<span class="kpress-video-placeholder-title">Demo video</span>' in tree.html


def test_heading_metadata_uses_plain_text_and_toc_skips_single_leading_h1() -> None:
    tree = parse_markdown(
        dedent(
            """
            # **Report** `Title`

            ## [Section](#details)

            ### Details
            """
        ).strip(),
        title="Headings",
    )

    assert [(item.level, item.title, item.id) for item in tree.headings] == [
        (1, "Report Title", "report-title"),
        (2, "Section", "section"),
        (3, "Details", "details"),
    ]
    assert [(item.title, item.href) for item in tree.toc] == [
        ("Section", "#section"),
        ("Details", "#details"),
    ]


def test_toc_normalizes_levels_when_top_levels_are_absent() -> None:
    # A document of only H3s (no H1/H2) should list flat at the TOC top level, not
    # indented three deep as if the missing H1/H2 ancestors existed. The rendered <h3>
    # tags are unchanged; this is a TOC-nesting concern only.
    tree = parse_markdown(
        dedent(
            """
            ### Finding Me

            ### Selected Work
            """
        ).strip(),
        title="Joshua Levy",
    )
    assert [(item.level, item.title) for item in tree.headings] == [
        (3, "Finding Me"),
        (3, "Selected Work"),
    ]
    assert [(item.level, item.title) for item in tree.toc] == [
        (1, "Finding Me"),
        (1, "Selected Work"),
    ]


def test_toc_compresses_an_interior_level_gap() -> None:
    # H2 then H4 with no H3 between: the H4 nests one level under the H2, not two.
    tree = parse_markdown(
        dedent(
            """
            ## Overview

            #### Detail
            """
        ).strip(),
        title="Doc",
    )
    assert [(item.level, item.title) for item in tree.toc] == [(1, "Overview"), (2, "Detail")]


def test_toc_preserves_relative_nesting_without_extra_indentation() -> None:
    # A gap-free hierarchy keeps its shape, and the shallowest shown heading sits at the
    # TOC top level (no leading indentation) — here H2/H3 map to TOC levels 1/2.
    tree = parse_markdown(
        dedent(
            """
            ## Section One

            ### Sub

            ## Section Two
            """
        ).strip(),
        title="Doc",
    )
    assert [(item.level, item.title) for item in tree.toc] == [
        (1, "Section One"),
        (2, "Sub"),
        (1, "Section Two"),
    ]


def test_internal_links_emit_diagnostics_for_missing_heading_targets_only() -> None:
    tree = parse_markdown(
        dedent(
            """
            ## Details

            [ok](#details)
            [missing](#missing-section)
            [top](#)
            [external](https://example.com)
            """
        ).strip(),
        title="Links",
    )

    broken = [item for item in tree.diagnostics if item.type == "broken_anchor"]
    assert [item.location for item in broken] == ["#missing-section"]
    assert "Internal link target '#missing-section' was not found." in broken[0].message


def test_loose_task_lists_keep_task_hooks_across_nested_paragraphs() -> None:
    tree = parse_markdown(
        dedent(
            """
            - [x] Done

              Extra paragraph.
            """
        ).strip(),
        title="Tasks",
    )

    assert '<li class="kpress-task task-list-item">' in tree.html
    assert '<input class="task-list-item-checkbox" checked="checked"' in tree.html
    assert "<p>Extra paragraph.</p>" in tree.html


def test_tables_preserve_attrs_and_get_static_reader_hooks() -> None:
    tree = parse_markdown(
        dedent(
            """
            | Label | Amount |
            | --- | ---: |
            | Revenue | 1,234.50 |

            <table id="raw" class="wide"><tr><td>42</td><td>note</td></tr></table>
            """
        ).strip(),
        title="Tables",
    )

    assert '<div class="kpress-table-wrap"><table class="kpress-table">' in tree.html
    # GFM header cells carry the data-col enrichment hook (column slug from the header).
    assert '<th data-col="label">Label</th>' in tree.html
    assert '<th style="text-align:right" data-col="amount">Amount</th>' in tree.html
    # Body cells map to their column's slug; numeric detection and alignment still apply.
    assert '<td data-col="label">Revenue</td>' in tree.html
    assert (
        '<td style="text-align:right" data-kpress-numeric="true" data-col="amount">1,234.50</td>'
        in tree.html
    )
    # A raw HTML table with no header row degrades gracefully: the numeric hook is still
    # set, but no data-col is invented.
    assert '<table id="raw" class="wide kpress-table">' in tree.html
    assert '<td data-kpress-numeric="true">42</td>' in tree.html
    assert "<td>note</td>" in tree.html
    assert "data-col" not in tree.html.split('id="raw"', 1)[1]


def test_table_cells_emit_data_col_from_header_slug() -> None:
    tree = parse_markdown(
        dedent(
            """
            | Ticker | Net Change % | Notes |
            | --- | ---: | --- |
            | ACME | 12.5 | up |
            """
        ).strip(),
        title="Cols",
    )

    # Header text is slugified: lowercased, non-alphanumeric runs -> a single hyphen.
    assert '<th data-col="ticker">Ticker</th>' in tree.html
    assert '<th style="text-align:right" data-col="net-change">Net Change %</th>' in tree.html
    assert '<th data-col="notes">Notes</th>' in tree.html
    # Body cells inherit their column's slug by position.
    assert '<td data-col="ticker">ACME</td>' in tree.html
    assert (
        '<td style="text-align:right" data-kpress-numeric="true" data-col="net-change">12.5</td>'
        in tree.html
    )
    assert '<td data-col="notes">up</td>' in tree.html


def test_tabbed_content_authoring_generates_stable_reader_panels() -> None:
    tree = parse_markdown(
        dedent(
            """
            :::: tabs
            ::: tab Overview
            Overview copy.
            :::

            ::: tab "Details"
            Details copy.
            :::
            ::::
            """
        ).strip(),
        title="Tabs",
    )

    for expected in [
        '<section class="kpress-tabs" data-kpress-tabs>',
        '<section class="kpress-tab-panel" data-kpress-tab-title="Overview">',
        '<section class="kpress-tab-panel" data-kpress-tab-title="Details">',
        "<p>Overview copy.</p>",
        "<p>Details copy.</p>",
    ]:
        assert expected in tree.html


def test_raw_html_trust_modes_preserve_safe_html_and_strip_unsafe_html() -> None:
    trusted = parse_markdown(
        '<section onclick="bad()"><em>Safe</em><script>alert("x")</script></section>',
        title="Trusted",
        trust_mode="trusted-local",
    )
    public = parse_markdown(
        '<section onclick="bad()"><em>Safe</em><script>alert("x")</script></section>',
        title="Public",
        trust_mode="public-static",
    )
    untrusted = parse_markdown(
        '<section onclick="bad()"><em>Safe</em><script>alert("x")</script></section>',
        title="Untrusted",
        trust_mode="untrusted",
    )

    assert 'onclick="bad()"' in trusted.html
    assert "<script>" in trusted.html
    assert "<em>Safe</em>" in public.html
    assert "onclick" not in public.html
    assert "<script>" not in public.html
    assert public.diagnostics[0].type == "html_sanitized"
    # Untrusted now runs the nh3 whitelist-only sanitizer (only the pass-through tags
    # survive) rather than escaping raw HTML. Non-whitelisted tags (<section>, <em>) are
    # stripped — their text content is kept — and <script>/event handlers are removed.
    assert "<section" not in untrusted.html
    assert "<em" not in untrusted.html
    assert "<script>" not in untrusted.html
    assert "onclick" not in untrusted.html
    assert "Safe" in untrusted.html
    assert untrusted.diagnostics[0].type == "html_sanitized"


def test_whitelisted_tag_survives_with_class_and_data_across_postures() -> None:
    source = '<st-device class="kind-x" data-st-kind="x">D</st-device>'
    for mode in ("public-static", "untrusted"):
        tree = parse_markdown(
            source,
            title="Whitelist",
            trust_mode=mode,  # pyright: ignore[reportArgumentType]
            extra_tags=("st-device",),
        )
        assert '<st-device class="kind-x" data-st-kind="x">D</st-device>' in tree.html


def test_non_whitelisted_tag_still_stripped_with_active_whitelist() -> None:
    for mode in ("public-static", "untrusted"):
        tree = parse_markdown(
            "<st-unknown>kept</st-unknown>",
            title="Whitelist",
            trust_mode=mode,  # pyright: ignore[reportArgumentType]
            extra_tags=("st-device",),
        )
        assert "<st-unknown" not in tree.html
        assert "kept" in tree.html


def test_unsafe_attributes_stripped_on_whitelisted_tag() -> None:
    source = '<st-device class="ok" data-k="v" style="color:red" onclick="bad()">D</st-device>'
    for mode in ("public-static", "untrusted"):
        tree = parse_markdown(
            source,
            title="Whitelist",
            trust_mode=mode,  # pyright: ignore[reportArgumentType]
            extra_tags=("st-device",),
        )
        assert 'class="ok"' in tree.html
        assert 'data-k="v"' in tree.html
        assert "style" not in tree.html
        assert "onclick" not in tree.html


def test_whitelisted_block_renders_inner_markdown() -> None:
    # A block-level whitelisted tag with blank lines around it lets the Markdown parser
    # process the inner content (standard HTML-block behavior): the inner link renders.
    source = "<st-device data-st-kind=note>\n\n[link](https://example.com)\n\n</st-device>"
    tree = parse_markdown(
        source,
        title="Whitelist",
        trust_mode="public-static",
        extra_tags=("st-device",),
    )
    assert "<st-device" in tree.html
    assert 'href="https://example.com"' in tree.html


def test_no_whitelist_output_unchanged() -> None:
    # With no extra_tags, a document with no whitelisted custom tags renders identically
    # whether or not the whitelist machinery is invoked (the byte-identical guarantee).
    source = '# Title\n\nA paragraph with <span class="hl">inline</span> markup.\n'
    baseline = parse_markdown(source, title="Doc", trust_mode="public-static")
    with_empty = parse_markdown(source, title="Doc", trust_mode="public-static", extra_tags=())
    assert with_empty.html == baseline.html


def test_whitelisted_tag_reaches_static_page_output() -> None:
    # Integration: the static publish path renders public-static; a whitelisted tag with
    # class/data-* reaches the full page output with its attributes intact.
    document = DocumentInput(
        title="Devices",
        source_text='<st-device class="kind-x" data-st-kind="x">Body</st-device>',
        body_markdown='<st-device class="kind-x" data-st-kind="x">Body</st-device>',
        source_path="devices.md",
        trust_mode="public-static",
    )
    page = render_page(document, RenderOptions(extra_tags=("st-device",)))
    assert '<st-device class="kind-x" data-st-kind="x">Body</st-device>' in page.html


def test_public_static_sanitizer_blocks_adversarial_html_bypasses() -> None:
    tree = parse_markdown(
        dedent(
            """
            <img src=x onerror=alert(1)>
            <svg onload=alert(1)><circle></circle></svg>
            <a href="javas\tcript:alert(1)">bad link</a>
            <a href="https://example.com/safe">safe link</a>
            """
        ).strip(),
        title="Unsafe",
        trust_mode="public-static",
    )

    assert "onerror" not in tree.html
    assert "onload" not in tree.html
    assert "<script" not in tree.html
    assert "<svg><circle></circle></svg>" in tree.html
    assert "javascript:" not in tree.html
    assert "javas\tcript" not in tree.html
    assert (
        '<a href="https://example.com/safe" target="_blank" rel="noopener noreferrer">safe link</a>'
    ) in tree.html
    assert any(item.type == "html_sanitized" for item in tree.diagnostics)


def test_sanitized_local_preserves_rendered_markdown_html() -> None:
    tree = parse_markdown(
        "# Title\n\n**bold** <script>alert(1)</script>",
        title="Sanitized",
        trust_mode="sanitized-local",
    )

    assert "<h1" in tree.html
    assert "<strong>bold</strong>" in tree.html
    assert "&lt;h1" not in tree.html
    assert "<script>" not in tree.html
    assert any(item.type == "html_sanitized" for item in tree.diagnostics)


def test_external_links_get_new_tab_safety_policy_without_changing_internal_links() -> None:
    tree = parse_markdown(
        dedent(
            """
            [external](https://example.com/report)
            [anchor](#local-section)
            [relative](docs/page.md)
            [mail](mailto:team@example.com)

            <a href="https://example.org/raw" rel="nofollow">raw external</a>
            """
        ).strip(),
        title="Links",
    )

    assert (
        '<a href="https://example.com/report" target="_blank" '
        'rel="noopener noreferrer">external</a>'
    ) in tree.html
    assert '<a href="#local-section">anchor</a>' in tree.html
    assert '<a href="docs/page.md">relative</a>' in tree.html
    assert '<a href="mailto:team@example.com">mail</a>' in tree.html
    assert (
        '<a href="https://example.org/raw" rel="nofollow noopener noreferrer" '
        'target="_blank">raw external</a>'
    ) in tree.html


def test_external_link_policy_preserves_non_link_raw_html() -> None:
    tree = parse_markdown(
        dedent(
            """
            <!-- keep this comment -->
            <?kpress processing?>
            <!doctype-marker>
            <a href="https://example.com/raw">external</a>
            """
        ).strip(),
        title="Raw HTML",
    )

    assert "<!-- keep this comment -->" in tree.html
    assert "<?kpress processing?>" in tree.html
    assert "<!doctype-marker>" in tree.html
    assert (
        '<a href="https://example.com/raw" target="_blank" rel="noopener noreferrer">external</a>'
    ) in tree.html


def test_code_math_and_diagram_markers_are_kpress_components() -> None:
    tree = parse_markdown(
        dedent(
            """
            ```python
            print("hello")
            ```

            Inline math $a^2 + b^2$.

            $$
            E = mc^2
            $$

            ```mermaid
            graph TD
            ```
            """
        ).strip(),
        title="Components",
    )

    assert '<pre class="kpress-code">' in tree.html
    assert 'class="language-python"' in tree.html
    assert "kpress-token" in tree.html
    assert 'class="kpress-math kpress-math-inline"' in tree.html
    # KaTeX is the active renderer; MathML is the semantic/accessibility output.
    assert 'data-kpress-math-renderer="katex"' in tree.html
    assert "data-kpress-math-provider" not in tree.html
    assert '<span class="kpress-math-render" aria-hidden="true">\\(' in tree.html
    assert '<span class="kpress-math-semantic">' in tree.html
    assert '<math xmlns="http://www.w3.org/1998/Math/MathML" display="inline">' in tree.html
    assert "<msup><mi>a</mi><mn>2</mn></msup>" in tree.html
    assert 'class="kpress-math kpress-math-display"' in tree.html
    assert '<div class="kpress-math-render" aria-hidden="true">\\[' in tree.html
    assert '<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">' in tree.html
    assert (
        '<figure class="kpress-diagram kpress-mermaid kpress-figure" data-kpress-diagram="mermaid" '
        'data-kpress-diagram-provider="mermaid" data-kpress-diagram-status="source">'
    ) in tree.html
    assert '<pre class="kpress-diagram-source"><code class="language-mermaid">' in tree.html


def test_svg_diagram_fences_render_sanitized_inline_svg() -> None:
    tree = parse_markdown(
        dedent(
            """
            ```svg
            <svg viewBox="0 0 10 10" role="img" onload="bad()">
              <title>Trend</title>
              <circle cx="5" cy="5" r="4"></circle>
              <script>alert(1)</script>
            </svg>
            ```
            """
        ).strip(),
        title="SVG",
    )

    assert (
        '<figure class="kpress-diagram kpress-svg-diagram kpress-figure" data-kpress-diagram="svg" '
        'data-kpress-diagram-provider="inline-svg">'
    ) in tree.html
    assert '<svg viewBox="0 0 10 10" role="img">' in tree.html
    assert "<title>Trend</title>" in tree.html
    assert '<circle cx="5" cy="5" r="4"></circle>' in tree.html
    assert "onload" not in tree.html
    assert "<script>" not in tree.html


def test_footnotes_and_math_inside_fenced_code_are_not_extracted() -> None:
    tree = parse_markdown(
        dedent(
            """
            ```
            [^code]: stays in code
            Inline $not_math$ also stays in code
            ```

            A real footnote.[^real]

            [^real]: Real footnote.
            """
        ).strip(),
        title="Fence safety",
    )

    assert "[^code]: stays in code" in tree.html
    assert "Inline $not_math$ also stays in code" in tree.html
    assert "fn-code" not in tree.html
    assert "kpress-math-inline" not in tree.html
    assert "fn-real" in tree.html
    assert [footnote.id for footnote in tree.footnotes] == ["real"]


def test_footnote_diagnostics_cover_missing_and_unused_definitions() -> None:
    tree = parse_markdown(
        dedent(
            """
            Missing footnote.[^ghost]
            Escaped literal \\[^escaped] and entity literal &#91;^entity] are prose.
            Inline code `[^code]` is not a footnote reference.

            ```
            [^fence]: fenced code is ignored
            ```

            [^orphan]: Orphan definition.
            """
        ).strip(),
        title="Footnotes",
    )

    missing = [item for item in tree.diagnostics if item.type == "missing_footnote"]
    unused = [item for item in tree.diagnostics if item.type == "unused_footnote"]
    assert [(item.location, item.message) for item in missing] == [
        ("[^ghost]", "Footnote reference '[^ghost]' has no matching definition.")
    ]
    assert [(item.location, item.message) for item in unused] == [
        ("[^orphan]", "Footnote definition '[^orphan]' is never referenced.")
    ]
    assert not any(
        item.location in {"[^code]", "[^entity]", "[^escaped]", "[^fence]"}
        for item in tree.diagnostics
    )


def test_inline_math_does_not_parse_plain_currency_ranges() -> None:
    tree = parse_markdown(
        "Revenue moved from $5 to $10 while formula $a^2$ stayed mathematical.",
        title="Math",
    )

    assert "from $5 to $10" in tree.html
    assert '<span class="kpress-math kpress-math-inline"' in tree.html
    assert "<msup><mi>a</mi><mn>2</mn></msup>" in tree.html


def test_math_mode_contract_accepts_only_off_and_auto() -> None:
    """MathMode is Literal["off", "auto"]; removed values must not type-check or render."""

    auto = parse_markdown("$x^2$", title="Auto math", math="auto")
    off = parse_markdown("$x^2$", title="Off math", math="off")

    assert 'data-kpress-math-renderer="katex"' in auto.html
    assert auto.has_math is True
    assert "kpress-math" not in off.html
    assert off.has_math is False
    assert "$x^2$" in off.html

    import typing

    from kpress.format.model import MathMode

    args = typing.get_args(MathMode)
    assert set(args) == {"off", "auto"}, f"MathMode must be exactly off|auto, got {args}"


def test_invalid_math_falls_back_to_source_with_diagnostic() -> None:
    tree = parse_markdown(r"Broken math $\badcommand{$ stays readable.", title="Bad math")

    assert 'data-kpress-math-error="true"' in tree.html
    assert r"\badcommand{" in tree.html
    assert any(item.type == "math_render_error" for item in tree.diagnostics)


def test_public_static_sanitizer_preserves_generated_mathml() -> None:
    tree = parse_markdown("$a^2$", title="Public math", trust_mode="public-static")

    assert "<math " in tree.html
    assert "<msup><mi>a</mi><mn>2</mn></msup>" in tree.html
    assert not any(item.type == "html_sanitized" for item in tree.diagnostics)


def test_render_page_respects_math_and_diagram_off_modes() -> None:
    page = render_page(
        DocumentInput(
            title="Off",
            source_text=dedent(
                """
                $x$

                ```mermaid
                graph TD
                ```
                """
            ).strip(),
            source_path="off.md",
            body_markdown=dedent(
                """
                $x$

                ```mermaid
                graph TD
                ```
                """
            ).strip(),
        ),
        RenderOptions(math="off", diagrams="off"),
    )

    assert "kpress-math" not in page.html
    assert "kpress-mermaid" not in page.html
    assert 'class="language-mermaid"' in page.html
