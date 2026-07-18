"""KPress fragment and page rendering."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from html import escape
from pathlib import Path
from typing import Any

from kpress.errors import KPressPublishError
from kpress.format.assets import (
    AssetManifest,
    AssetRef,
    katex_asset_manifest,
    package_asset_manifest,
    read_package_text,
    resolve_package_asset_manifest,
)
from kpress.format.markdown import parse_markdown
from kpress.format.model import (
    AssetMode,
    Diagnostic,
    DocumentInput,
    DocumentTree,
    RenderedDocument,
    RenderedPage,
    RenderOptions,
    TocEntry,
    resolve_widgets,
)
from kpress.format.templating import render_template
from kpress.models import PrintProfile

SOURCE_PREVIEW_MAX_BYTES = 512 * 1024
# Widget ids that get a mount element: plain kebab-case slugs only, since the id
# lands in class/id/data attributes (a config key is host data, not trusted markup).
_WIDGET_ID_RE = re.compile(r"[a-z][a-z0-9-]*")
_CLASS_ATTRIBUTE_RE = re.compile(r"class=(?P<quote>['\"])(?P<classes>.*?)(?P=quote)")
_SAME_DOCUMENT_LINK_RE = re.compile(
    r"<a\b[^>]*\bhref=(?P<quote>['\"])#[^'\"]+(?P=quote)",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def _icon_sprite() -> str:
    """The KPress icon sprite, read from static/icons/icons.svg and inlined once per
    document so `<use href="#kpress-icon-*">` references resolve. The glyphs live in that
    file; this only includes it (no SVG is authored in Python)."""
    return read_package_text("icons/icons.svg")


def _icon(name: str, *, css_class: str = "", attrs: str = "") -> str:
    """A reference to a sprite symbol -- carries no SVG markup. The glyph is defined in
    static/icons/icons.svg as `#kpress-icon-<name>`; color comes from CSS `color`, size
    from CSS (or `attrs`)."""
    class_attr = f' class="{css_class}"' if css_class else ""
    return (
        f'<svg{class_attr}{attrs} aria-hidden="true"><use href="#kpress-icon-{name}"></use></svg>'
    )


def _slug_class(value: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    return safe or "document"


def _diagnostics(document: DocumentInput, tree: DocumentTree | None = None) -> list[dict[str, str]]:
    diagnostics: list[Diagnostic] = []
    if document.frontmatter_error:
        diagnostics.append(Diagnostic(type="frontmatter_error", message=document.frontmatter_error))
    if tree:
        diagnostics.extend(tree.diagnostics)
    return [item.as_dict() for item in diagnostics]


def _should_include_toc(tree: DocumentTree, options: RenderOptions) -> bool:
    if options.include_toc == "off":
        return False
    if options.include_toc == "on":
        return bool(tree.toc)
    return len(tree.toc) >= options.toc_min_headings


def _has_css_class(html: str, css_class: str) -> bool:
    """Return whether rendered HTML has a class token, independent of token order."""

    return any(
        css_class in match.group("classes").split() for match in _CLASS_ATTRIBUTE_RE.finditer(html)
    )


def _render_toc(tree: DocumentTree, options: RenderOptions) -> str:
    if not _should_include_toc(tree, options):
        return ""
    items = "".join(
        f'<li class="kpress-toc-level-{entry.level} toc-h{entry.level}">'
        f'<a class="toc-link" href="{escape(entry.href)}">{escape(entry.title)}</a></li>'
        for entry in tree.toc
    )
    # The toggle button and the backdrop are siblings of the <nav>, not children:
    # in the narrow drawer layout the nav animates/hides as a unit, and a nested
    # toggle would inherit that hidden state. toc.js groups them by walking to the
    # shared `[data-kpress-toc]` nav. The button carries the list icon plus a
    # visually-hidden label so the affordance reads the same everywhere and no
    # host has to inject an icon.
    return "".join(
        [
            '<button class="kpress-toc-toggle" type="button" data-kpress-toc-toggle ',
            'aria-expanded="false" aria-label="Table of contents">',
            _icon("list", css_class="kpress-toc-toggle-icon", attrs=' width="20" height="20"'),
            "</button>",
            '<div class="kpress-toc-backdrop" data-kpress-toc-backdrop aria-hidden="true"></div>',
            '<nav class="kpress-toc kpress-no-print" aria-label="Table of contents" ',
            "data-kpress-toc>",
            '<a href="#" class="kpress-toc-title toc-link toc-title" ',
            'data-kpress-toc-top>Contents</a><ol class="toc-list">',
            items,
            "</ol></nav>",
        ]
    )


def _render_frontmatter(document: DocumentInput) -> str:
    if not document.frontmatter:
        return ""
    rows = "".join(
        f"<dt>{escape(str(key))}</dt><dd>{escape(str(value))}</dd>"
        for key, value in sorted(document.frontmatter.items(), key=lambda item: str(item[0]))
    )
    return (
        '<details class="kpress-frontmatter kpress-no-print"><summary>Frontmatter</summary>'
        f"<dl>{rows}</dl></details>"
    )


def _render_frontmatter_error(document: DocumentInput) -> str:
    if not document.frontmatter_error:
        return ""
    message = escape(document.frontmatter_error)
    return (
        '<aside class="kpress-frontmatter-error" role="alert" '
        'aria-label="Frontmatter error">'
        "<strong>Frontmatter error</strong>"
        f"<span>{message}</span>"
        "</aside>"
    )


def _render_thumbnail(document: DocumentInput, title: str) -> str:
    thumbnail_url = _meta_value(document, "thumbnail_url")
    if not thumbnail_url:
        return ""
    alt = _meta_value(document, "thumbnail_alt") or title
    return (
        '<img class="thumbnail kpress-image" '
        f'src="{escape(thumbnail_url)}" alt="{escape(alt)}" '
        'data-kpress-image="true" loading="lazy">'
    )


def _body_h1_is_title(tree: DocumentTree, title: str) -> bool:
    """True when the body opens with one H1 that already shows the title.

    Such a document needs no separate title header: the lone leading H1 is the
    visible title. A differing first H1, multiple H1s, or no H1 means the title
    is not otherwise on the page, so a header should be rendered.
    """
    headings = tree.headings
    return (
        bool(headings)
        and headings[0].level == 1
        and sum(heading.level == 1 for heading in headings) == 1
        and headings[0].title.strip() == title.strip()
    )


def _render_document(document: DocumentInput, options: RenderOptions) -> tuple[str, DocumentTree]:
    title = document.frontmatter.get("title") or document.title
    header_id = f"kpress-title-{_slug_class(str(title))}"
    if document.body_html is not None:
        tree = DocumentTree(title=str(title), html=document.body_html, profile="document")
    else:
        tree = parse_markdown(
            document.body_markdown or document.source_text,
            title=str(title),
            trust_mode=document.trust_mode,
            math=options.math,
            diagrams=options.diagrams,
            extra_tags=options.extra_tags,
            extra_attributes=options.extra_attributes,
        )
    # Build-time tree transform (BuildExtensions.transform_tree): applied after
    # parse_markdown has already computed tree.toc, but before the TOC and page model
    # are rendered from the tree. A transform that adds or changes headings must rebuild
    # tree.toc itself (see RenderOptions.transform_tree).
    if options.transform_tree is not None:
        tree = options.transform_tree(tree)
    toc = _render_toc(tree, options)
    frontmatter_error = _render_frontmatter_error(document)
    frontmatter = _render_frontmatter(document) if options.show_frontmatter else ""
    thumbnail = _render_thumbnail(document, str(title))
    # Both `data-kpress-theme` (user preference: system|light|dark) and
    # `data-kpress-resolved-theme` (light|dark, the host's resolution of
    # `system`) are stamped on the article. The full-page shell mirrors
    # both on `<html>` so `:root[data-kpress-resolved-theme=...]` CSS
    # selectors engage there too; for the dynamic-host fragment, putting
    # the resolved theme on the article means `.kpress[data-kpress-...]`
    # selectors work regardless of whether the host shell stamps its own
    # root attribute.
    # Render the title header unless the body already opens with a single H1 that
    # matches the title: that lone H1 is the visible title, so a separate header
    # would duplicate it. A differing first H1, multiple H1s, or no H1 means the
    # title is not otherwise shown, so render it. (Same rule `_toc_entries` uses
    # to drop the leading title H1 from the TOC.)
    show_header = options.show_doc_header and not _body_h1_is_title(tree, str(title))
    doc_header = (
        f'<header class="kpress-doc-header kpress-metadata"><h1 id="{escape(header_id)}">'
        f"{escape(str(title))}</h1></header>"
        if show_header
        else ""
    )
    # `aria-labelledby` only resolves when the header it names is present; without
    # the header the article is labelled by the title text (the body's own H1, if
    # any, already carries the visible heading).
    label_attr = (
        f'aria-labelledby="{escape(header_id)}"'
        if show_header
        else f'aria-label="{escape(str(title))}"'
    )
    html = (
        '<article class="kpress kpress-doc kpress-print-surface" '
        f'data-kpress-profile="document" data-kpress-theme="{escape(options.theme_mode)}" '
        f'data-kpress-resolved-theme="{escape(options.resolved_theme)}" '
        f'data-kpress-fonts="{escape(options.font_mode)}" '
        f'data-kpress-palette="{escape(options.palette)}" '
        f'data-kpress-card="{"on" if options.content_card else "off"}" '
        f"{label_attr}>"
        f"{doc_header}"
        f"{frontmatter_error}"
        f"{frontmatter}"
        '<div class="kpress-doc-layout kpress-content-with-toc">'
        f"{toc}"
        f"{thumbnail}"
        f'<div class="kpress-prose kpress-long-text">{tree.html}</div>'
        "</div>"
        "</article>"
    )
    return html, tree


def _format_byte_size(size: int) -> str:
    if size >= 1024 * 1024:
        value = size / (1024 * 1024)
        return f"{value:.1f} MiB"
    if size >= 1024:
        value = size / 1024
        return f"{value:.0f} KiB"
    return f"{size} B"


def _metadata_size(document: DocumentInput, fallback: int) -> int:
    value = document.metadata.get("size") or document.metadata.get("logical_size")
    if isinstance(value, int):
        return max(value, fallback)
    if isinstance(value, str):
        try:
            return max(int(value), fallback)
        except ValueError:
            return fallback
    return fallback


def _truncate_source_preview(source_text: str) -> tuple[str, int, bool]:
    encoded = source_text.encode("utf-8")
    if len(encoded) <= SOURCE_PREVIEW_MAX_BYTES:
        return source_text, len(encoded), False
    preview = encoded[:SOURCE_PREVIEW_MAX_BYTES].decode("utf-8", errors="ignore")
    return preview, len(preview.encode("utf-8")), True


def _render_source_truncation_warning(*, shown_bytes: int, total_bytes: int) -> str:
    shown = escape(_format_byte_size(shown_bytes))
    total = escape(_format_byte_size(total_bytes))
    return (
        '<div class="kpress-source-truncation-warning" role="status">'
        "<strong>Source preview truncated.</strong> "
        f"Showing {shown} of {total}. "
        "Use the original source file for complete text before printing."
        "</div>"
    )


def _render_source(document: DocumentInput, profile: PrintProfile, options: RenderOptions) -> str:
    lang = Path(document.source_path).suffix.lstrip(".") or "text"
    preview, shown_bytes, clipped = _truncate_source_preview(document.source_text)
    total_bytes = _metadata_size(document, len(document.source_text.encode("utf-8")))
    body = escape(preview)
    title = escape(document.title)
    warning = (
        _render_source_truncation_warning(shown_bytes=shown_bytes, total_bytes=total_bytes)
        if clipped or total_bytes > shown_bytes
        else ""
    )
    return (
        f'<article class="kpress kpress-source kpress-{_slug_class(profile)} '
        f'kpress-print-surface" data-kpress-profile="source" '
        f'data-kpress-fonts="{escape(options.font_mode)}">'
        f'<header class="kpress-source-header"><h1>{title}</h1>'
        f'<p class="kpress-source-meta">{escape(document.source_path)}</p></header>'
        f"{warning}"
        '<div class="kpress-code-scroll">'
        f'<pre class="kpress-code"><code class="language-{escape(lang)}">{body}</code></pre>'
        "</div></article>"
    )


def render_fragment(
    document: DocumentInput, options: RenderOptions | None = None
) -> RenderedDocument:
    """Render a KPress document fragment for a dynamic host."""

    options = options or RenderOptions()
    profile = options.print_profile or document.document_profile or document.profile
    tree: DocumentTree | None = None

    if profile == "document":
        html, tree = _render_document(document, options)
    else:
        html = _render_source(document, profile, options)
    # Inline the icon sprite once so `<use href="#kpress-icon-*">` (server chrome + client
    # JS) resolve in every context: standalone page, static site, and host-injected embed.
    html = _icon_sprite() + html

    has_math = bool(tree and tree.has_math)
    assets = _render_asset_manifest(
        html=html,
        tree=tree,
        options=options,
        has_math=has_math,
    )
    return RenderedDocument(
        html=html,
        profile=profile,
        printable=options.printable,
        assets=assets,
        diagnostics=_diagnostics(document, tree),
        toc=tree.toc if tree else [],
        has_math=has_math,
    )


def _render_asset_manifest(
    *,
    html: str,
    tree: DocumentTree | None,
    options: RenderOptions,
    has_math: bool,
) -> AssetManifest:
    if options.asset_policy == "none":
        return AssetManifest()
    if options.asset_policy == "all":
        return package_asset_manifest(
            mode=options.asset_mode,
            prefix=options.asset_url_prefix,
        ).merged(
            katex_asset_manifest(
                mode=options.asset_mode,
                prefix=options.asset_url_prefix,
            )
        )
    if options.asset_policy != "auto":
        msg = (
            f"Invalid KPress asset policy {options.asset_policy!r}; "
            "expected 'none', 'auto', or 'all'"
        )
        raise KPressPublishError(msg)

    entry_points: set[str] = set()
    enabled_widgets = resolve_widgets(options.widgets)
    if options.theme_mode == "system":
        entry_points.add("js/theme.js")
    if "settings" in enabled_widgets:
        entry_points.add("js/settings-widget.js")
    if tree is not None and _should_include_toc(tree, options):
        entry_points.add("js/toc.js")
    if tree is not None and _SAME_DOCUMENT_LINK_RE.search(tree.html):
        entry_points.add("js/tooltips.js")
    # Any in-document hash navigation (TOC or same-document links) gets the
    # history behavior: viewport-aware scroll restoration on Back/Forward.
    if entry_points & {"js/toc.js", "js/tooltips.js"}:
        entry_points.add("js/history.js")
    if _has_css_class(html, "kpress-code"):
        entry_points.add("js/code-copy.js")
    if _has_css_class(html, "kpress-table"):
        entry_points.add("js/tables.js")
    if "data-kpress-tabs" in html:
        entry_points.add("js/tabs.js")
    if 'data-kpress-diagram="mermaid"' in html:
        entry_points.add("js/diagrams.js")
    if "data-kpress-video-id" in html:
        entry_points.add("js/video-popover.js")

    assets = resolve_package_asset_manifest(
        entry_points,
        mode=options.asset_mode,
        prefix=options.asset_url_prefix,
    )
    if has_math:
        assets = assets.merged(
            katex_asset_manifest(
                mode=options.asset_mode,
                prefix=options.asset_url_prefix,
            )
        )
    return assets


_INLINE_FONT_URL_RE = re.compile(
    r"url\(\s*(?P<quote>['\"]?)(?P<url>\.\./fonts/[^)'\"\s]+)(?P=quote)\s*\)"
)


def _inline_css_text(path: str, prefix: str) -> str:
    css = read_package_text(path)
    asset_root = prefix.rstrip("/") + "/"

    def replace_font_url(match: re.Match[str]) -> str:
        font_path = match.group("url").removeprefix("../")
        return f'url("{asset_root}{font_path}")'

    return _INLINE_FONT_URL_RE.sub(replace_font_url, css).replace("</style", "<\\/style")


def _inline_js_text(path: str) -> str:
    return read_package_text(path).replace("</script", "<\\/script")


def _is_katex_asset(path: str) -> bool:
    # KaTeX is vendored as a hashed bundle: its stylesheet keeps relative
    # `fonts/` URLs, so it is always linked (never inlined or hashed) to keep
    # those references resolvable offline.
    return path.startswith("katex/")


def _link_css(asset: AssetRef) -> str:
    return f'<link rel="stylesheet" href="{escape(asset.url)}">'


def _link_js(asset: AssetRef) -> str:
    src = escape(asset.url)
    if asset.loading == "classic":
        return f'<script defer src="{src}"></script>'
    return f'<script type="module" src="{src}"></script>'


def _import_map_tag(import_map: dict[str, str]) -> str:
    # The import map must precede every module <script> so the browser can remap each
    # module's `import "./x.js"` to its hashed URL. URLs are our own asset paths (no
    # untrusted content); escape `<` defensively so the JSON cannot close the element early.
    payload = json.dumps({"imports": import_map}, sort_keys=True).replace("<", "\\u003c")
    return f'<script type="importmap">{payload}</script>'


def _asset_tags(assets: AssetManifest, prefix: str, *, asset_mode: AssetMode) -> str:
    entry_points = assets.browser_entry_points()
    css_assets = [asset for asset in entry_points if asset.loading == "stylesheet"]
    js_assets = [asset for asset in entry_points if asset.loading in {"module", "classic"}]
    map_tag = _import_map_tag(assets.import_map) if assets.import_map else ""
    if asset_mode == "inline":
        css = "\n".join(
            _link_css(asset)
            if _is_katex_asset(asset.path)
            else f'<style data-kpress-asset="{escape(asset.path)}">\n'
            f"{_inline_css_text(asset.path, prefix)}</style>"
            for asset in css_assets
        )
        js = "\n".join(
            _link_js(asset)
            if asset.loading == "classic"
            else f'<script type="module" data-kpress-asset="{escape(asset.path)}">\n'
            f"{_inline_js_text(asset.path)}</script>"
            for asset in js_assets
        )
        return "\n".join(part for part in (map_tag, css, js) if part)

    css = "\n".join(_link_css(asset) for asset in css_assets)
    js = "\n".join(_link_js(asset) for asset in js_assets)
    return "\n".join(part for part in (map_tag, css, js) if part)


@lru_cache(maxsize=1)
def _theme_bootstrap_script() -> str:
    # Inlined render-blocking in <head> so the resolved theme is set before first paint (no
    # flash of the wrong theme). The JS source lives in js/theme-bootstrap.js and reads the
    # server-set data-kpress-theme attribute, so nothing is interpolated into it here.
    return f"<script>{read_package_text('js/theme-bootstrap.js')}</script>"


@lru_cache(maxsize=1)
def _standalone_page_reset() -> str:
    # Standalone-only page-shell reset, inlined render-blocking in <head>. Source lives in
    # css/page-reset.css (see docs/kpress-design.md "Standalone scroll model").
    return f"<style>{read_package_text('css/page-reset.css')}</style>"


def _widget_mounts(enabled_widgets: dict[str, Any]) -> str:
    """Emit the positioned mount element for each enabled chrome widget.

    Chrome widgets are client-rendered (no-JS rule): the server ships only an
    empty, CSS-positionable mount — `data-kpress-widget` is the registry id the
    client runtime resolves; the `kpress-<id>` class/id keep per-widget CSS
    hooks (e.g. the settings gear's `--kpress-settings-inset-*` position
    tokens) working unchanged. Widget ids come from config keys; only safe
    slug ids get a mount.
    """

    mounts: list[str] = []
    for widget_id in enabled_widgets:
        if not _WIDGET_ID_RE.fullmatch(widget_id):
            continue
        mounts.append(
            f'<div class="kpress-widget kpress-{widget_id} kpress-no-print" '
            f'id="kpress-{widget_id}" data-kpress-widget="{widget_id}"></div>'
        )
    return "".join(mounts)


def _json_script_payload(value: Any) -> str:
    """JSON for an application/json script block, unable to break out of it.

    The three HTML-significant characters are unicode-escaped (same discipline as
    the diagnostics block); keys sorted for deterministic output.
    """

    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def _meta_value(document: DocumentInput, key: str) -> str | None:
    value = document.metadata.get(key, document.frontmatter.get(key))
    return None if value is None or value == "" else str(value)


def _social_meta_tags(document: DocumentInput, title: str) -> str:
    description = _meta_value(document, "description")
    image = _meta_value(document, "image") or _meta_value(document, "thumbnail_url")
    url = _meta_value(document, "url") or _meta_value(document, "public_url")
    site_name = _meta_value(document, "site_name")
    card = _meta_value(document, "twitter_card") or "summary_large_image"
    twitter_handle = _meta_value(document, "twitter_handle")
    social_title = _meta_value(document, "social_title") or title
    parts = [
        f'<meta property="og:title" content="{escape(social_title)}">',
        '<meta property="og:type" content="website">',
        f'<meta name="twitter:card" content="{escape(card)}">',
        f'<meta name="twitter:title" content="{escape(social_title)}">',
    ]
    if description:
        parts.append(f'<meta property="og:description" content="{escape(description)}">')
        parts.append(f'<meta name="twitter:description" content="{escape(description)}">')
    if image:
        parts.append(f'<meta property="og:image" content="{escape(image)}">')
        parts.append(f'<meta name="twitter:image" content="{escape(image)}">')
    if url:
        parts.append(f'<meta property="og:url" content="{escape(url)}">')
        parts.append(f'<link rel="canonical" href="{escape(url)}">')
    if site_name:
        parts.append(f'<meta property="og:site_name" content="{escape(site_name)}">')
    if twitter_handle:
        handle = twitter_handle if str(twitter_handle).startswith("@") else f"@{twitter_handle}"
        parts.append(f'<meta name="twitter:site" content="{escape(handle)}">')
    return "\n  ".join(parts)


def page_title(document: DocumentInput) -> str:
    """The page-level title: a frontmatter ``title`` wins over the host-supplied one."""

    return str(document.frontmatter.get("title") or document.title)


def build_page_model(
    *,
    title: str,
    route: str,
    profile: str,
    toc: list[TocEntry],
    widgets: dict[str, Any],
) -> dict[str, Any]:
    """The page-model payload (keys pinned by contract.PUBLIC_PAGE_MODEL_KEYS).

    One builder serves both surfaces: ``render_page`` serializes it into the
    ``#kpress-page-model`` block; ``runtime.render_view`` echoes it in the
    dynamic payload so embeds read the same data (docs/kpress-design.md "Page model
    block and widget mounts").

    ``headings`` carries the post-processed TOC entries, not raw document heading
    levels: a lone leading H1 is stripped, and each level is the entry's
    structural TOC depth (one level under its nearest preceding shallower
    heading).
    """

    return {
        "version": 1,
        "title": title,
        "route": route,
        "profile": profile,
        "headings": [
            {"level": entry.level, "title": entry.title, "href": entry.href} for entry in toc
        ],
        "widgets": widgets,
    }


def render_page(document: DocumentInput, options: RenderOptions | None = None) -> RenderedPage:
    """Render a complete HTML page from a KPress document."""

    options = options or RenderOptions(asset_mode="linked")
    fragment = render_fragment(document, options)
    title = page_title(document)
    asset_tags = _asset_tags(
        fragment.assets, options.asset_url_prefix, asset_mode=options.asset_mode
    )
    theme_bootstrap = _theme_bootstrap_script()
    enabled_widgets = resolve_widgets(options.widgets)
    diagnostics_json = _json_script_payload(fragment.diagnostics)
    # The page model: published data client widgets compute from (layer A of the
    # extension model; keys pinned by contract.PUBLIC_PAGE_MODEL_KEYS). Widget
    # configs ride through verbatim; "off" widgets are absent entirely.
    page_model_json = _json_script_payload(
        build_page_model(
            title=title,
            route=document.logical_path or "",
            profile=fragment.profile,
            toc=fragment.toc,
            widgets=enabled_widgets,
        )
    )
    social_meta = _social_meta_tags(document, title)
    # The page shell is authored in templates/page.html.jinja and rendered through
    # the strict environment (see format/templating.py): markup lives in the
    # template, this function just supplies the slots. Plain values (title, the
    # theme/palette/font state) autoescape; kpress-generated and site-owned markup
    # (chrome slots, asset tags, scripts, the document fragment) ride `| safe`.
    html = render_template(
        "page.html.jinja",
        theme_mode=options.theme_mode,
        resolved_theme=options.resolved_theme,
        palette=options.palette,
        prose_font=options.prose_font,
        title=title,
        page_reset=_standalone_page_reset(),
        social_meta=social_meta,
        theme_bootstrap=theme_bootstrap,
        asset_tags=asset_tags,
        head_extra_html=options.head_extra_html,
        header_html=options.header_html,
        widget_mounts=_widget_mounts(enabled_widgets),
        fragment_html=fragment.html,
        footer_html=options.footer_html,
        video_close_icon=_icon("x"),
        page_model_json=page_model_json,
        diagnostics_json=diagnostics_json,
    )
    return RenderedPage(
        html=html,
        profile=fragment.profile,
        title=title,
        assets=fragment.assets,
        diagnostics=fragment.diagnostics,
        has_math=fragment.has_math,
    )


def render_document_from_text(
    source_text: str, *, title: str = "Document", source_path: str = "document.md"
) -> RenderedPage:
    """Convenience helper used by workflow and tests."""

    return render_page(
        DocumentInput(
            title=title, source_text=source_text, source_path=source_path, body_markdown=source_text
        ),
        RenderOptions(asset_mode="linked"),
    )
