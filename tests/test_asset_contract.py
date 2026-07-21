from __future__ import annotations

import re
from pathlib import Path

from kpress.format.assets import package_asset_manifest, package_asset_refs
from kpress.runtime import get_static_asset

_KPRESS_ROOT = Path(__file__).resolve().parents[1]


def test_scroll_surfaces_share_the_minimal_scrollbar_token() -> None:
    """Every horizontally/vertically scrolling surface uses the one shared minimal
    scrollbar treatment (the --color-scrollbar token), so no default fat scrollbars
    remain and the look is consistent across tables, code, math, diagrams, and tabs."""
    css = get_static_asset("css/components.css").content.decode("utf-8")
    token = "scrollbar-color: var(--color-scrollbar) transparent"
    for selector in (
        ".kpress-table-wrap",
        ".kpress-math-display",
        ".kpress-diagram-source",
        ".kpress-diagram-rendered",
        ".kpress-tab-list",
        ".kpress-tab-panel",
    ):
        block = re.search(r"^" + re.escape(selector) + r"[^{}]*\{[^}]*\}", css, re.MULTILINE)
        assert block is not None, f"missing rule for {selector}"
        assert token in block.group(0), f"{selector} lacks the shared scrollbar token"


def test_hashed_js_imports_resolve_via_import_map() -> None:
    """In hashed/hashed builds JS files get content-hashed names, but their `./x.js` ESM
    imports are left byte-for-byte untouched -- the emitted import map remaps each specifier
    to its hashed file. This pins that contract: every `./x.js` a module imports has an
    import-map entry pointing at the actually-emitted hashed file (the same path the
    `<script src>` resolves to), and no hashed specifier is ever written into the JS source.
    This prevents 404s on hashed imports without rewriting the module source."""
    from kpress.format.assets import (
        DEFAULT_JS_ASSETS,
        TRANSITIVE_JS_ASSETS,
        package_asset_output_path,
        package_js_import_map,
        read_package_bytes,
    )

    prefix = "/_kpress/assets/"
    import_map = package_js_import_map(mode="hashed", prefix=prefix)
    specifier = re.compile(r"""['"]\./(?P<name>[A-Za-z0-9_.-]+\.js)['"]""")
    rewritten = re.compile(r"""['"]\./[\w-]+\.[0-9a-f]{16}\.js['"]""")

    for path in (*DEFAULT_JS_ASSETS, *TRANSITIVE_JS_ASSETS):
        source = read_package_bytes(path).decode("utf-8")
        directory = path.rsplit("/", 1)[0]  # all package JS modules live under "js/"
        # The source is never rewritten: only the import map carries the content hash.
        assert rewritten.search(source) is None, f"{path} has a hashed import specifier"
        for match in specifier.finditer(source):
            dep = f"{directory}/{match.group('name')}"
            key = prefix + dep
            assert key in import_map, f"{path} imports {dep} with no import-map entry"
            # The map points at the emitted hashed file -- the same URL the <script src> uses.
            assert import_map[key] == prefix + package_asset_output_path(dep, mode="hashed")

    # Every mapped value is a real content-hashed emitted JS filename (stem.<hash>.js).
    hashed = re.compile(r"\.[0-9a-f]{16}\.js$")
    for value in import_map.values():
        assert hashed.search(value), f"{value} is not a hashed JS filename"


def test_dark_mode_overrides_the_code_syntax_palette() -> None:
    """Dark mode re-tokens the code/source highlight palette (dair) so tokens stay legible
    on the dark surface instead of reusing the light-mode values as near-background grays."""
    css = get_static_asset("css/syntax.css").content.decode("utf-8")
    parts = css.split('[data-kpress-resolved-theme="dark"]', 1)
    assert len(parts) == 2, "no dark-mode syntax override block"
    dark_block = parts[1]
    for token in (
        "--kpress-syntax-comment",
        "--kpress-syntax-keyword",
        "--kpress-syntax-operator",
        "--kpress-syntax-output",
        "--kpress-syntax-prompt",
    ):
        assert token in dark_block, f"{token} not overridden for dark mode"


def test_document_css_contract_has_required_surfaces() -> None:
    css = "\n".join(
        get_static_asset(path).content.decode("utf-8")
        for path in [
            "css/style-tokens.css",
            "css/document.css",
            "css/components.css",
            "css/print.css",
        ]
    )

    for required in [
        "--kpress-font-body",
        "--kpress-font-prose",
        "--kpress-font-punctuation",
        "--kpress-font-size-mono",
        "--kpress-caps-heading-size-multiplier",
        "PT Serif",
        "Source Sans 3",
        "LocalPunct",
        "--kpress-print-page-margin",
        ".kpress-print-surface",
        ".kpress-toc",
        ".kpress-footnotes",
        ".kpress-figure",
        ".kpress-figcaption",
        ".kpress-tooltip-bottom::after",
        ".kpress-tooltip-bottom-left",
        ".kpress-tooltip-bottom-right",
        ".kpress-tooltip-left",
        ".kpress-tooltip-mobile-bottom",
        ".kpress-tooltip-right",
        ".kpress-tooltip-top::after",
        ".kpress-tooltip-top-left",
        ".kpress-tooltip-top-right",
        ".kpress-tooltip-wide-right",
        ".kpress-table-wrap",
        "data-kpress-numeric",
        "@media (prefers-reduced-motion: reduce)",
        "@media print",
    ]:
        assert required in css
    for forbidden in [".tree-pane", ".preview-pane", ".file-header", ".tab-bar"]:
        assert forbidden not in css


def test_syntax_highlighting_css_is_a_shipped_reader_asset() -> None:
    refs = package_asset_refs()
    css = get_static_asset("css/syntax.css").content.decode("utf-8")

    assert "css/syntax.css" in refs["css"]
    for required in [
        ".kpress-token-k",
        ".kpress-token-nf",
        ".kpress-token-s",
        ".kpress-token-c",
        ':root[data-kpress-resolved-theme="dark"] .kpress',
    ]:
        assert required in css


def test_host_embedding_protocol_is_a_shipped_reader_asset() -> None:
    refs = package_asset_refs()
    js = get_static_asset("js/host.js").content.decode("utf-8")

    assert "js/host.js" in refs["js"]
    for required in [
        "kpress:ready",
        "kpress:resize",
        "kpress:expand",
        "kpress:close",
    ]:
        assert required in js


def test_no_css_or_js_source_is_authored_in_render_py() -> None:
    """Front-end code lives in front-end files: render.py builds HTML and reads CSS/JS
    assets, but never authors CSS rules or JS bodies as Python strings. The standalone
    page-shell reset and the theme bootstrap moved to real assets (css/page-reset.css,
    js/theme-bootstrap.js), which render.py reads and inlines."""
    render_src = (_KPRESS_ROOT / "src/kpress/format/render.py").read_text(encoding="utf-8")
    for css_literal in ("html,body{", "html, body {", "margin:0", "overflow:hidden"):
        assert css_literal not in render_src, f"render.py authors CSS: {css_literal!r}"
    for js_literal in (
        "localStorage",
        "addEventListener",
        "dataset.kpressResolvedTheme",
        "matchMedia",
    ):
        assert js_literal not in render_src, f"render.py authors JS: {js_literal!r}"
    static = _KPRESS_ROOT / "src/kpress/format/static"
    assert (static / "css/page-reset.css").is_file()
    assert (static / "js/theme-bootstrap.js").is_file()
    assert "css/page-reset.css" in render_src
    assert "js/theme-bootstrap.js" in render_src


def test_code_copy_controls_have_reader_css_states() -> None:
    css = get_static_asset("css/components.css").content.decode("utf-8")

    for required in [
        ".kpress-code-copy",
        ".kpress-code-copy:hover",
        '.kpress-code-copy[data-kpress-copy-state="copied"]',
        '.kpress-code-copy[data-kpress-copy-state="error"]',
        ".kpress-code:has(.kpress-code-copy)",
    ]:
        assert required in css


def test_standalone_settings_menu_has_reader_css_states() -> None:
    css = get_static_asset("css/components.css").content.decode("utf-8")

    for required in [
        ".kpress-settings",
        ".kpress-settings-btn",
        ".kpress-settings-btn:focus-visible",
        '.kpress-settings[aria-expanded="true"] .kpress-settings-menu',
        '.kpress-menu-seg[aria-checked="true"]',
    ]:
        assert required in css


def test_doc_actions_widget_has_reader_css_states() -> None:
    css = get_static_asset("css/components.css").content.decode("utf-8")

    for required in [
        ".kpress-doc-actions",
        ".kpress-doc-actions-badge",
        ".kpress-doc-actions-btn",
        ".kpress-doc-actions-btn:hover",
        ".kpress-doc-actions-btn:focus-visible",
        ".kpress-long-text:has(.kpress-doc-actions):not(:has(> h1:first-child))",
    ]:
        assert required in css


def test_toc_and_footnote_transitions_are_property_scoped() -> None:
    css = get_static_asset("css/components.css").content.decode("utf-8")

    assert "transition: all" not in css
    toc_rule = css.partition(".kpress-toc a {")[2].partition("}")[0]
    footnote_rule = css.partition(".kpress-footnote-ref a,\n.kpress-footnote-backref {")[
        2
    ].partition("}")[0]
    assert toc_rule
    assert footnote_rule
    for rule in [toc_rule, footnote_rule]:
        assert "color var(--kpress-transition-fast)" in rule
        assert "background-color var(--kpress-transition-fast)" in rule
        assert "background var(--kpress-transition-fast)" not in rule
    assert "border-color var(--kpress-transition-fast)" in toc_rule


def test_table_css_contract_covers_responsive_reader_parity() -> None:
    css = get_static_asset("css/components.css").content.decode("utf-8")

    for required in [
        ".kpress-table th",
        "font-variant-caps: var(--kpress-caps-variant);",
        ".kpress-table tbody tr:nth-child(even)",
        ".kpress-content-with-toc.has-toc .kpress-table-wrap",
        ".kpress-content-with-toc:has(.kpress-toc) .kpress-table-wrap",
        "@container kpress-doc (max-width: 47.99rem)",
        ".kpress-table code",
        "font-size: var(--kpress-font-size-mono-small);",
    ]:
        assert required in css


def test_tab_css_contract_covers_authoring_and_print_policy() -> None:
    css = "\n".join(
        get_static_asset(path).content.decode("utf-8")
        for path in ["css/components.css", "css/print.css"]
    )

    for required in [
        ".kpress-tabs",
        ".kpress-tab-list",
        ".kpress-tab-panel",
        '.kpress-tab-button[aria-selected="true"]',
        '.kpress-tabs [role="tablist"]',
        ".kpress-tab-panel::before",
        "content: attr(data-kpress-tab-title);",
    ]:
        assert required in css


def test_math_css_contract_covers_native_mathml() -> None:
    css = "\n".join(
        get_static_asset(path).content.decode("utf-8")
        for path in ["css/components.css", "css/print.css"]
    )

    for required in [
        ".kpress-math",
        ".kpress-math math",
        ".kpress-math-display",
        ".kpress-math-inline",
        '.kpress-math[data-kpress-math-error="true"]',
    ]:
        assert required in css


def test_diagram_css_contract_covers_svg_and_mermaid_surfaces() -> None:
    css = "\n".join(
        get_static_asset(path).content.decode("utf-8")
        for path in ["css/components.css", "css/print.css"]
    )

    for required in [
        ".kpress-diagram",
        ".kpress-svg-diagram",
        ".kpress-mermaid",
        ".kpress-diagram-source",
        ".kpress-diagram-rendered",
        '.kpress-diagram[data-kpress-diagram-status="error"]',
    ]:
        assert required in css


def test_source_ported_reader_css_keeps_kash_semantic_surfaces() -> None:
    css = "\n".join(
        get_static_asset(path).content.decode("utf-8")
        for path in [
            "css/document.css",
            "css/components.css",
            "css/print.css",
        ]
    )

    for required in [
        ".highlight",
        ".citation::before",
        ".citation::after",
        ".debug",
        ".description",
        ".key-claims::before",
        ".claim::before",
        ".summary::before",
        ".concepts::before",
        ".annotated-para",
        ".para-caption",
        ".frame-capture",
        ".video-gallery",
        ".video-item",
        ".thumbnail",
        ".hero h1",
        ".hero h1 i",
        ".subtitle",
        ".boxed-text",
        ".shaded-text",
        ".centered-headers h1",
        ".justify p",
        ".tab-button-active",
        ".tab-button-inactive",
        ".hidden",
        ".kpress-print-only",
    ]:
        assert required in css


def test_print_css_contract_covers_reader_parity_surfaces() -> None:
    css = get_static_asset("css/print.css").content.decode("utf-8")

    assert (
        """.kpress-doc,
  .kpress-page-main {
    padding-inline: 0;
  }"""
        in css
    )
    for required in [
        "orphans: 3;",
        "widows: 3;",
        ".kpress ol",
        "counter-reset: kpress-print-list-item;",
        ".kpress ol > li",
        "grid-template-columns: 2.5rem minmax(0, 1fr);",
        "counter-increment: kpress-print-list-item;",
        ".kpress ol > li::before",
        'content: counter(kpress-print-list-item) ".";',
        ".kpress ol > li > *",
        ".kpress li > p:first-child",
        ".kpress .kpress-long-list",
        ".kpress .kpress-long-list > li",
        "break-inside: auto;",
        ".kpress thead",
        "display: table-header-group;",
        ".kpress tr",
        ".kpress details.metadata",
        ".kpress-footnote-ref a",
        ".kpress-footnote-backref",
        'a[href^="#fnref"]',
        "font-variant-caps: all-small-caps;",
        ".kpress-video-popover",
        ".kpress-video-backdrop",
        ".kpress-toc-backdrop",
    ]:
        assert required in css


def test_package_asset_manifest_includes_reader_font_assets() -> None:
    manifest = package_asset_manifest(mode="hashed")
    asset_ids = {asset.id for asset in manifest.assets}

    assert {
        "fonts/pt-serif-latin-400-normal.woff2",
        "fonts/pt-serif-latin-700-normal.woff2",
        "fonts/pt-serif-latin-400-italic.woff2",
        "fonts/pt-serif-latin-700-italic.woff2",
        "fonts/source-sans-3-latin-wght-normal.woff2",
        "fonts/source-sans-3-latin-wght-italic.woff2",
    } <= asset_ids
    assert all("latest" not in asset.path for asset in manifest.assets)


def test_browser_assets_are_native_esm() -> None:
    js_root = _KPRESS_ROOT / "src/kpress/format/static/js"
    # theme-bootstrap.js is the one deliberate exception: it is inlined render-blocking in
    # <head> as a classic IIFE (an ES module would be deferred and flash the wrong theme),
    # so it is never loaded as a module and carries no `export`.
    scripts = sorted(p for p in js_root.glob("*.js") if p.name != "theme-bootstrap.js")

    assert {path.name for path in scripts} >= {
        "theme.js",
        "toc.js",
        "tooltips.js",
        "tables.js",
        "code-copy.js",
        "diagrams.js",
        "video-popover.js",
        "tabs.js",
        "viewport.js",
    }
    for script in scripts:
        text = script.read_text(encoding="utf-8")
        assert "export " in text
        assert "@tailwindcss" not in text


def test_no_tailwind_runtime_in_kpress_assets() -> None:
    for path in Path("src/kpress/format/static").rglob("*"):
        if path.is_file() and path.suffix in {".css", ".js", ".json", ".html"}:
            assert "tailwind" not in path.read_text(encoding="utf-8").lower()


def test_warm_palette_selector_recipe_and_native_borders_are_pinned() -> None:
    css = get_static_asset("css/style-tokens.css").content.decode("utf-8")

    for selector in (
        ':root[data-kpress-palette="warm"]',
        ':root[data-kpress-palette="warm"] .kpress',
        '.kpress[data-kpress-palette="warm"]',
        ':root[data-kpress-resolved-theme="dark"][data-kpress-palette="warm"]',
        ':root[data-kpress-resolved-theme="dark"][data-kpress-palette="warm"] .kpress',
        '.kpress[data-kpress-resolved-theme="dark"][data-kpress-palette="warm"]',
    ):
        assert selector in css
    warm_light = css.split('data-kpress-palette="warm"] {', 1)[1].split("}", 1)[0]
    assert "--kpress-doc-border:" in warm_light
    assert "--kpress-doc-border-hairline:" in warm_light


def test_visual_parity_css_contract_pins_kash_reconciliation() -> None:
    """Pin the kash/textpress visual-parity reconciliation (plan-2026-06-01
    -kpress-visual-polish §3.x/§5.x) so the document visuals cannot silently
    drift back. Each substring is a reconciled rule from the parity audit."""

    css = "\n".join(
        get_static_asset(path).content.decode("utf-8")
        for path in [
            "css/style-tokens.css",
            "css/theme-light.css",
            "css/theme-dark.css",
            "css/document.css",
            "css/components.css",
        ]
    )
    for required in [
        # §3.2 inline code scoped so the border/padding does not leak into blocks
        "code:not(pre code)",
        # §3.4 footnote-ref / backref pill styling (was missing on screen)
        ".kpress-footnote-ref a",
        ".kpress-footnote-backref",
        # §3.7/§3.8 tooltip stacking above TOC + the fade-in visible class
        "z-index: 300",
        "kpress-tooltip-visible",
        # §3.6 TOC sidebar breakpoint (75rem ≈ kash 1200px). Both grid tracks are
        # FIXED widths (no cqw/vw/1fr) so the content column is a hard constant
        # 48rem at every pane width; the pair is left-aligned with justify-content
        # so extra pane width becomes a single trailing margin (no empty band left
        # of the TOC). A pane-coupled term in the column math (the old
        # clamp(.., 15cqw, ..) TOC under a fixed group cap) made the content shrink
        # as the pane widened.
        "@container kpress-doc (min-width: 75rem)",
        # 53rem = 48rem reading measure + 2×2.5rem inset (content-card inner
        # breathing room; was 51rem at 1.5rem inset).
        "grid-template-columns: 15rem 53rem;",
        "justify-content: start",
        # The grid wrapper carries its own reading-measure cap + margin:auto
        # (`.kpress-doc-layout`), so it must be uncapped alongside the article
        # `.kpress-doc` — otherwise the two-column grid stays centred at the
        # 48rem cap and its fixed tracks spill past it to the right.
        ".kpress-doc-layout:has(.kpress-toc)",
        # narrow drawer breakpoint + mobile scroll containment + scroll-gated toggle
        "@container kpress-doc (max-width: 74.99rem)",
        "overscroll-behavior",
        "show-toggle",
        # §5.1 the warm (kash/textpress) palette is selectable and warms the cream
        # code surface. (The --kpress-host-* COLOR fallback seam was retired when the
        # palette moved to the direct, per-theme×palette model; hosts now override the
        # resolved --kpress-doc-* tokens directly. See style-tokens.css "Palette options".)
        'data-kpress-palette="warm"',
        # serif prose face (kash reading look) is the prose default
        "PT Serif",
    ]:
        assert required in css, f"visual-parity rule missing from shipped CSS: {required!r}"


def test_footnote_backref_uses_literal_glyph_for_seal_equivalence() -> None:
    """The footnote backref must use literal NBSP+arrow chars, not &nbsp;/&uarr;
    entities — the seal/publish pipeline decodes entities, so entities would make
    the dynamic and hashed render paths diverge (see markdown.py)."""

    from kpress.format.markdown import parse_markdown

    tree = parse_markdown(
        "Body.[^a]\n\n[^a]: Note.\n",
        title="t",
        trust_mode="trusted",
    )
    assert "kpress-footnote-backref" in tree.html
    assert "&uarr;" not in tree.html
    assert "↑" in tree.html  # literal upwards arrow
