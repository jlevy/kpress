"""Deterministic Markdown normalization for KPress fixtures and dynamic views."""

from __future__ import annotations

import re
from collections.abc import Mapping
from html import escape
from html.parser import HTMLParser
from typing import Any, Literal, cast
from urllib.parse import parse_qs, unquote, urlparse

from latex2mathml.converter import convert as convert_latex_math
from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.attrs import attrs_block_plugin, attrs_plugin
from mdit_py_plugins.container import container_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name  # pyright: ignore[reportUnknownVariableType]
from pygments.util import ClassNotFound

from kpress.format.model import (
    Diagnostic,
    DiagramMode,
    DocumentTree,
    Footnote,
    Heading,
    MathMode,
    TocEntry,
    TrustMode,
)
from kpress.format.sanitize import sanitize_generated_svg, sanitize_raw_html

_RAW_HTML_LINE_RE = re.compile(r"^(\s*)<([A-Za-z][A-Za-z0-9-]*)(\s|>|/>)")
_SLUG_RE = re.compile(r"[^a-z0-9]+")
# Optional leading sign and major currency symbol; _is_numeric_cell_text strips
# whitespace first, so "$ 12.45" is matched as "$12.45".
# Currency symbols (8): $ € ¥ £ ₹ ₩ ¢ ₽
#   ¥ covers both Japanese yen (JPY) and Chinese yuan/renminbi (CNY).
_NUMERIC_CELL_RE = re.compile(r"^[-+]?[$€¥£₹₩¢₽]?((\d{1,3}(,\d{3})+|\d+)(\.\d+)?|\.\d+)%?$")
_INLINE_CODE_SPAN_RE = re.compile(r"`+[^`]*`+")
_FOOTNOTE_REF_RE = re.compile(r"(?<!\\)\[\^([^\]\s]+)\]")
# Module-level singleton is safe to share across threads: Pygments'
# `HtmlFormatter.format()` reads instance config but does not mutate it,
# and writes into a per-call StringIO inside `pygments.highlight()`. The
# render-cache lock in runtime.py serializes most concurrent calls
# anyway. Constructing once at import keeps the highlight hot path
# alloc-free.
_HTML_FORMATTER: Any = cast(Any, HtmlFormatter(nowrap=True, classprefix="kpress-token-"))
_SVG_CASED_ATTRIBUTES = {
    "preserveaspectratio": "preserveAspectRatio",
    "refx": "refX",
    "refy": "refY",
    "viewbox": "viewBox",
}
_SEMANTIC_CONTAINER_CLASSES = (
    "annotated-para",
    "boxed-text",
    "centered-headers",
    "claim",
    "concepts",
    "description",
    "full-text",
    "hero",
    "justify",
    "key-claims",
    "para",
    "para-caption",
    "shaded-text",
    "summary",
    "video-gallery",
    "video-item",
)
_QUOTED_TAB_LABEL_RE = re.compile(r"""^(['"])(.*)\1$""")
_YOUTUBE_HOSTS = {
    "m.youtube.com",
    "www.youtube.com",
    "www.youtube-nocookie.com",
    "youtube.com",
    "youtube-nocookie.com",
}


def slugify(value: str, used: set[str] | None = None) -> str:
    """Create a stable heading ID."""

    used = used if used is not None else set()
    base = _SLUG_RE.sub("-", value.strip().lower()).strip("-") or "section"
    slug = base
    idx = 2
    while slug in used:
        slug = f"{base}-{idx}"
        idx += 1
    used.add(slug)
    return slug


def _highlight_code(code: str, language: str) -> str:
    if not language:
        return escape(code)
    try:
        lexer = get_lexer_by_name(language)
    except ClassNotFound:
        return escape(code)
    highlighted = cast(str, highlight(code, lexer, _HTML_FORMATTER))
    return highlighted.rstrip("\n")


def _render_mermaid_diagram(source: str) -> str:
    return (
        '<figure class="kpress-diagram kpress-mermaid" data-kpress-diagram="mermaid" '
        'data-kpress-diagram-provider="mermaid" data-kpress-diagram-status="source">'
        f'<pre class="kpress-diagram-source"><code class="language-mermaid">{escape(source)}</code></pre>'
        "</figure>\n"
    )


def _render_svg_diagram(source: str) -> str:
    svg = sanitize_generated_svg(source)
    return (
        '<figure class="kpress-diagram kpress-svg-diagram" data-kpress-diagram="svg" '
        f'data-kpress-diagram-provider="inline-svg">{svg}</figure>\n'
    )


def _render_fence(token: Token, *, diagrams: DiagramMode) -> str:
    language = token.info.strip().split(maxsplit=1)[0].lower() if token.info.strip() else ""
    if language == "mermaid" and diagrams != "off":
        return _render_mermaid_diagram(token.content)
    if language == "svg" and diagrams != "off":
        return _render_svg_diagram(token.content)
    class_attr = f' class="language-{escape(language)}"' if language else ""
    return f'<pre class="kpress-code"><code{class_attr}>{_highlight_code(token.content, language)}</code></pre>\n'


def _footnote_ident(token: Token) -> str:
    raw = token.meta.get("label") or str(int(token.meta.get("id", 0)) + 1)
    return _SLUG_RE.sub("-", str(raw).strip().lower()).strip("-") or "note"


def _footnote_ref_id(token: Token) -> str:
    ident = _footnote_ident(token)
    sub_id = int(token.meta.get("subId", 0))
    return f"{ident}-{sub_id + 1}" if sub_id else ident


def _render_footnote_ref(tokens: list[Token], idx: int, _options: Any, _env: Any) -> str:
    token = tokens[idx]
    ident = _footnote_ident(token)
    ref_id = _footnote_ref_id(token)
    # The visible marker is the sequential footnote number (1, 2, 3 …) matching the
    # ordered footnotes section, regardless of the authored label; the label still backs
    # the anchor ids (`#fn-<label>` / `#fnref-<label>`).
    caption = escape(str(int(token.meta.get("id", 0)) + 1))
    return (
        f'<sup class="kpress-footnote-ref"><a href="#fn-{ident}" id="fnref-{ref_id}" '
        f'data-kpress-footnote-ref="{ident}">{caption}</a></sup>'
    )


def _render_footnote_block_open(_tokens: list[Token], _idx: int, _options: Any, _env: Any) -> str:
    return '<section class="kpress-footnotes">\n<ol>\n'


def _render_footnote_block_close(_tokens: list[Token], _idx: int, _options: Any, _env: Any) -> str:
    return "</ol>\n</section>\n"


def _render_footnote_open(tokens: list[Token], idx: int, _options: Any, _env: Any) -> str:
    return f'<li id="fn-{_footnote_ident(tokens[idx])}" class="kpress-footnote-item">'


def _render_footnote_close(_tokens: list[Token], _idx: int, _options: Any, _env: Any) -> str:
    return "</li>\n"


def _render_footnote_anchor(tokens: list[Token], idx: int, _options: Any, _env: Any) -> str:
    ref_id = _footnote_ref_id(tokens[idx])
    # Literal NBSP + upwards-arrow + NBSP ( ↑ ), matching kash.
    # Using the literal characters rather than the &nbsp;/&uarr; entities keeps
    # the dynamic and sealed/published render paths byte-equivalent — the sealer
    # decodes entities, which would otherwise diverge from the dynamic output.
    return f' <a href="#fnref-{ref_id}" class="kpress-footnote-backref">&nbsp;↑&nbsp;</a>'


def _math_diagnostics(env: dict[str, Any]) -> list[Diagnostic]:
    diagnostics = env.setdefault("kpress_math_diagnostics", [])
    return cast(list[Diagnostic], diagnostics)


def _record_math_render_error(env: dict[str, Any], source: str, exc: Exception) -> None:
    _math_diagnostics(env).append(
        Diagnostic(
            type="math_render_error",
            message=f"Math expression could not be rendered as MathML: {type(exc).__name__}.",
            severity="warning",
            location=source,
        )
    )


def _mark_math_present(env: dict[str, Any]) -> None:
    env["kpress_has_math"] = True


def _render_math(
    source: str,
    *,
    display: Literal["inline", "display"],
    math: MathMode,
    env: dict[str, Any],
) -> str:
    # `auto` is lazy: math markup, KaTeX, and math assets exist only once a
    # document actually contains math. Reaching this renderer is that signal.
    _mark_math_present(env)
    tag = "div" if display == "display" else "span"
    class_name = f"kpress-math kpress-math-{display}"
    display_mode = "block" if display == "display" else "inline"
    open_delim, close_delim = (r"\[", r"\]") if display == "display" else (r"\(", r"\)")
    try:
        mathml = convert_latex_math(source, display=display_mode)
    except Exception as exc:  # noqa: BLE001 - keep invalid TeX readable in documents.
        _record_math_render_error(env, source, exc)
        return (
            f'<{tag} class="{class_name}" data-kpress-math="{display}" '
            f'data-kpress-math-renderer="katex" data-kpress-math-error="true">'
            f"{escape(source)}</{tag}>"
        )
    # KaTeX is the only active visual renderer: it enhances the TeX source
    # client-side. The server-rendered MathML is the semantic/accessibility
    # output and the no-JS fallback, not a public backend.
    return (
        f'<{tag} class="{class_name}" data-kpress-math="{display}" '
        f'data-kpress-math-renderer="katex">'
        f'<{tag} class="kpress-math-render" aria-hidden="true">'
        f"{open_delim}{escape(source)}{close_delim}</{tag}>"
        f'<{tag} class="kpress-math-semantic">{mathml}</{tag}>'
        f"</{tag}>"
    )


def _render_math_inline(
    tokens: list[Token],
    idx: int,
    _options: Any,
    env: dict[str, Any],
    *,
    math: MathMode,
) -> str:
    return _render_math(tokens[idx].content.strip(), display="inline", math=math, env=env)


def _render_math_block(
    tokens: list[Token],
    idx: int,
    _options: Any,
    env: dict[str, Any],
    *,
    math: MathMode,
) -> str:
    return f"{_render_math(tokens[idx].content.strip(), display='display', math=math, env=env)}\n"


def _tab_label(info: str) -> str:
    label = info.strip().partition(" ")[2].strip()
    quoted = _QUOTED_TAB_LABEL_RE.match(label)
    if quoted:
        label = quoted.group(2).strip()
    return label or "Tab"


def _render_tabs_container(
    _renderer: Any,
    tokens: list[Token],
    idx: int,
    _options: Any,
    _env: Any,
) -> str:
    if tokens[idx].nesting == 1:
        return '<section class="kpress-tabs" data-kpress-tabs>\n'
    return "</section>\n"


def _render_tab_container(
    _renderer: Any,
    tokens: list[Token],
    idx: int,
    _options: Any,
    _env: Any,
) -> str:
    if tokens[idx].nesting == 1:
        label = escape(_tab_label(tokens[idx].info), quote=True)
        return f'<section class="kpress-tab-panel" data-kpress-tab-title="{label}">\n'
    return "</section>\n"


def _token_attrs(token: Token) -> list[tuple[str, str | None]]:
    attrs = token.attrs or {}
    return [(str(name), str(value)) for name, value in attrs.items()]


def _image_caption(token: Token) -> str:
    return str(token.attrGet("title") or "").strip()


def _image_attrs(token: Token) -> list[tuple[str, str | None]]:
    standalone_figure = bool(token.meta.get("kpress_figure_image"))
    attrs: list[tuple[str, str | None]] = []
    saw_alt = False
    for name, value in _token_attrs(token):
        normalized = name.lower()
        if normalized == "title" and standalone_figure:
            continue
        if normalized == "alt":
            attrs.append((name, token.content))
            saw_alt = True
        else:
            attrs.append((name, value))
    if not saw_alt:
        attrs.append(("alt", token.content))
    attrs = _append_class(attrs, "kpress-image")
    attrs = _set_attr(attrs, "data-kpress-image", "true")
    if _attr_value(attrs, "loading") is None:
        attrs = _set_attr(attrs, "loading", "lazy")
    return attrs


def _render_image(tokens: list[Token], idx: int, _options: Any, _env: Any) -> str:
    return f"<img{_render_attrs(_image_attrs(tokens[idx]))}>"


def _render_paragraph_open(tokens: list[Token], idx: int, _options: Any, _env: Any) -> str:
    if tokens[idx].meta.get("kpress_figure_image"):
        return '<figure class="kpress-figure" data-kpress-figure="image">\n'
    if tokens[idx].hidden:
        return ""
    return f"<p{_render_attrs(_token_attrs(tokens[idx]))}>"


def _render_paragraph_close(tokens: list[Token], idx: int, _options: Any, _env: Any) -> str:
    if tokens[idx].meta.get("kpress_figure_image"):
        caption = str(tokens[idx].meta.get("kpress_figure_caption") or "").strip()
        figcaption = (
            f'\n<figcaption class="kpress-figcaption">{escape(caption)}</figcaption>'
            if caption
            else ""
        )
        return f"{figcaption}\n</figure>\n"
    if tokens[idx].hidden:
        return ""
    return "</p>\n"


def _standalone_image_child(token: Token) -> Token | None:
    children = token.children or []
    if len(children) != 1 or children[0].type != "image":
        return None
    return children[0]


def _mark_standalone_image_figures(tokens: list[Token]) -> None:
    for idx, token in enumerate(tokens[:-2]):
        if token.type != "paragraph_open":
            continue
        inline = tokens[idx + 1]
        close = tokens[idx + 2]
        if inline.type != "inline" or close.type != "paragraph_close":
            continue
        image = _standalone_image_child(inline)
        if image is None:
            continue
        caption = _image_caption(image)
        token.meta["kpress_figure_image"] = True
        image.meta["kpress_figure_image"] = True
        close.meta["kpress_figure_image"] = True
        if caption:
            close.meta["kpress_figure_caption"] = caption


def _markdown_it(*, trust_mode: TrustMode, diagrams: DiagramMode, math: MathMode) -> MarkdownIt:
    md = MarkdownIt("js-default", {"html": trust_mode != "untrusted"})
    md.use(tasklists_plugin, enabled=False)
    md.use(footnote_plugin)
    if math != "off":
        md.use(dollarmath_plugin, allow_space=False, allow_digits=False)
    md.use(container_plugin, name="tabs", render=_render_tabs_container)
    md.use(container_plugin, name="tab", render=_render_tab_container)
    for class_name in _SEMANTIC_CONTAINER_CLASSES:
        md.use(container_plugin, name=class_name)
    md.use(attrs_block_plugin)
    md.use(attrs_plugin, spans=True)

    def render_fence_rule(tokens: list[Token], idx: int, _options: Any, _env: Any) -> str:
        return _render_fence(tokens[idx], diagrams=diagrams)

    def render_math_inline_rule(tokens: list[Token], idx: int, options: Any, env: Any) -> str:
        return _render_math_inline(tokens, idx, options, cast(dict[str, Any], env), math=math)

    def render_math_block_rule(tokens: list[Token], idx: int, options: Any, env: Any) -> str:
        return _render_math_block(tokens, idx, options, cast(dict[str, Any], env), math=math)

    renderer_rules = cast(Any, md.renderer).rules
    renderer_rules["fence"] = render_fence_rule
    renderer_rules["footnote_ref"] = _render_footnote_ref
    renderer_rules["footnote_block_open"] = _render_footnote_block_open
    renderer_rules["footnote_block_close"] = _render_footnote_block_close
    renderer_rules["footnote_open"] = _render_footnote_open
    renderer_rules["footnote_close"] = _render_footnote_close
    renderer_rules["footnote_anchor"] = _render_footnote_anchor
    renderer_rules["math_inline"] = render_math_inline_rule
    renderer_rules["math_block"] = render_math_block_rule
    renderer_rules["image"] = _render_image
    renderer_rules["paragraph_open"] = _render_paragraph_open
    renderer_rules["paragraph_close"] = _render_paragraph_close
    return md


def _escape_untrusted_raw_html(markdown: str) -> str:
    escaped_lines: list[str] = []
    for line in markdown.splitlines():
        if _RAW_HTML_LINE_RE.match(line):
            escaped_lines.append(escape(line))
        else:
            escaped_lines.append(line)
    return "\n".join(escaped_lines)


def _plain_inline_text(token: Token) -> str:
    pieces: list[str] = []
    for child in token.children or []:
        if child.type in {"text", "code_inline", "html_inline"}:
            pieces.append(child.content)
        elif child.type in {"softbreak", "hardbreak"}:
            pieces.append(" ")
        elif child.type == "image":
            pieces.append(child.content)
    text = "".join(pieces).strip()
    return re.sub(r"\s+", " ", text) or token.content


def _add_heading_ids(tokens: list[Token]) -> tuple[list[Heading], set[str]]:
    headings: list[Heading] = []
    used_ids: set[str] = set()
    for idx, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        inline = tokens[idx + 1] if idx + 1 < len(tokens) else None
        title = _plain_inline_text(inline) if inline and inline.type == "inline" else ""
        level = int(token.tag.removeprefix("h"))
        heading_id = slugify(title, used_ids)
        token.attrSet("id", heading_id)
        headings.append(Heading(level=level, title=title, id=heading_id))
    return headings, used_ids


def _postprocess_tasks(html: str) -> str:
    return html.replace('class="task-list-item"', 'class="kpress-task task-list-item"')


def _is_external_http_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _protocol_safe_url(value: str | None) -> str:
    if not value:
        return ""
    return f"https:{value}" if value.startswith("//") else value


def _youtube_video_id(value: str | None) -> str | None:
    parsed = urlparse(_protocol_safe_url(value))
    host = parsed.hostname or ""
    normalized_host = host.removeprefix("www.")
    if normalized_host == "youtu.be":
        return next((part for part in parsed.path.split("/") if part), None)
    if host not in _YOUTUBE_HOSTS and normalized_host not in {
        "youtube.com",
        "youtube-nocookie.com",
    }:
        return None
    if parsed.path == "/watch":
        return next(iter(parse_qs(parsed.query).get("v", [])), None)
    if parsed.path.startswith(("/embed/", "/shorts/")):
        return next((part for part in parsed.path.split("/")[2:] if part), None)
    return None


def _youtube_start_seconds(value: str | None) -> str | None:
    parsed = urlparse(_protocol_safe_url(value))
    query = parse_qs(parsed.query)
    raw = next(iter(query.get("start", query.get("t", []))), "")
    if not raw and parsed.fragment.startswith("t="):
        raw = parsed.fragment[2:]
    cleaned = raw[:-1] if raw.endswith("s") else raw
    try:
        seconds = int(float(cleaned))
    except ValueError:
        return None
    return str(seconds) if seconds >= 0 else None


def _render_attrs(attrs: list[tuple[str, str | None]]) -> str:
    rendered: list[str] = []
    for name, value in attrs:
        if value is None:
            rendered.append(name)
        else:
            rendered.append(f'{name}="{escape(value, quote=True)}"')
    return "" if not rendered else " " + " ".join(rendered)


def _attr_value(attrs: list[tuple[str, str | None]], attr_name: str) -> str | None:
    normalized_attr = attr_name.lower()
    return next((value for name, value in attrs if name.lower() == normalized_attr), None)


def _set_attr(
    attrs: list[tuple[str, str | None]], attr_name: str, attr_value: str
) -> list[tuple[str, str | None]]:
    normalized_attr = attr_name.lower()
    updated: list[tuple[str, str | None]] = []
    replaced = False
    for name, value in attrs:
        if name.lower() == normalized_attr:
            updated.append((name, attr_value))
            replaced = True
        else:
            updated.append((name, value))
    if not replaced:
        updated.append((attr_name, attr_value))
    return updated


def _append_class(
    attrs: list[tuple[str, str | None]], class_name: str
) -> list[tuple[str, str | None]]:
    classes = (_attr_value(attrs, "class") or "").split()
    if class_name not in classes:
        classes.append(class_name)
    return _set_attr(attrs, "class", " ".join(classes))


def _apply_external_link_attrs(attrs: list[tuple[str, str | None]]) -> list[tuple[str, str | None]]:
    href = _attr_value(attrs, "href")
    if not _is_external_http_url(href):
        return attrs

    updated: list[tuple[str, str | None]] = []
    saw_target = False
    saw_rel = False
    for name, value in attrs:
        normalized = name.lower()
        if normalized == "target":
            updated.append((name, "_blank"))
            saw_target = True
            continue
        if normalized == "rel":
            tokens = [] if value is None else value.split()
            for required in ("noopener", "noreferrer"):
                if required not in tokens:
                    tokens.append(required)
            updated.append((name, " ".join(tokens)))
            saw_rel = True
            continue
        updated.append((name, value))
    if not saw_target:
        updated.append(("target", "_blank"))
    if not saw_rel:
        updated.append(("rel", "noopener noreferrer"))
    return updated


def _is_numeric_cell_text(value: str) -> bool:
    text = re.sub(r"\s+", "", value)
    return bool(_NUMERIC_CELL_RE.fullmatch(text))


def _slugify_column(text: str) -> str:
    """Stable column key derived from a table header cell's text: lowercased, with
    non-alphanumeric runs collapsed to single hyphens. Empty when the header carries no
    alphanumerics. This is the public ``data-col`` enrichment hook downstream decorators
    use to select a column by name; kpress emits it and never consumes it."""
    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")


class _BufferedCell:
    def __init__(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tag = tag
        self.attrs = attrs
        self.parts: list[str] = []
        self.text_parts: list[str] = []

    def text(self) -> str:
        return "".join(self.text_parts)


class _KpressHtmlPostprocessor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []
        self._table_depth = 0
        self._cell: _BufferedCell | None = None
        self._skip_iframe_depth = 0
        # Per-top-level-table column slugs (from the header row) + the current row's
        # column index, used to emit data-col on body cells. Only the top-level table is
        # tracked, matching the fact that only its cells are buffered.
        self._table_columns: list[str] = []
        self._table_col_index = 0

    def _append(self, value: str) -> None:
        if self._cell:
            self._cell.parts.append(value)
        else:
            self.parts.append(value)

    def _append_text(self, value: str) -> None:
        if self._cell:
            self._cell.text_parts.append(value)

    def _attrs_for_tag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> list[tuple[str, str | None]]:
        if tag in {
            "circle",
            "ellipse",
            "g",
            "line",
            "path",
            "polygon",
            "polyline",
            "rect",
            "svg",
            "text",
            "tspan",
            "use",
        }:
            return [(_SVG_CASED_ATTRIBUTES.get(name, name), value) for name, value in attrs]
        if tag == "a":
            return _apply_external_link_attrs(attrs)
        if tag == "figure":
            return _append_class(attrs, "kpress-figure")
        if tag == "figcaption":
            return _append_class(attrs, "kpress-figcaption")
        if tag == "table":
            return _append_class(attrs, "kpress-table")
        if tag == "img":
            updated = _append_class(attrs, "kpress-image")
            updated = _set_attr(updated, "data-kpress-image", "true")
            if _attr_value(updated, "loading") is None:
                updated = _set_attr(updated, "loading", "lazy")
            return updated
        return attrs

    def _video_placeholder(self, attrs: list[tuple[str, str | None]]) -> str | None:
        src = _attr_value(attrs, "src")
        video_id = _youtube_video_id(src)
        if not video_id:
            return None
        title = (_attr_value(attrs, "title") or "Video").strip() or "Video"
        placeholder_attrs: list[tuple[str, str | None]] = [
            ("type", "button"),
            ("class", "kpress-video-placeholder"),
            ("data-kpress-video-id", video_id),
            ("data-kpress-video-title", title),
            ("aria-label", f"Open video: {title}"),
        ]
        start_seconds = _youtube_start_seconds(src)
        if start_seconds is not None:
            placeholder_attrs.insert(3, ("data-kpress-video-start", start_seconds))
        return (
            f"<button{_render_attrs(placeholder_attrs)}>"
            '<span class="kpress-video-placeholder-action" aria-hidden="true">Play</span>'
            f'<span class="kpress-video-placeholder-title">{escape(title)}</span>'
            "</button>"
        )

    def _flush_cell(self) -> None:
        cell = self._cell
        if not cell:
            return
        attrs = cell.attrs
        if _is_numeric_cell_text(cell.text()):
            attrs = _set_attr(attrs, "data-kpress-numeric", "true")
        slug = self._column_slug_for_cell(cell)
        if slug:
            attrs = _set_attr(attrs, "data-col", slug)
        self._table_col_index += 1
        self._cell = None
        self._append(f"<{cell.tag}{_render_attrs(attrs)}>")
        self.parts.extend(cell.parts)
        self._append(f"</{cell.tag}>")

    def _column_slug_for_cell(self, cell: _BufferedCell) -> str:
        """Header cells (`th`) define the column slug positionally; body cells (`td`) map
        to the slug recorded for their column index. No header row -> no slug (graceful)."""
        index = self._table_col_index
        if cell.tag.lower() == "th":
            slug = _slugify_column(cell.text())
            if len(self._table_columns) <= index:
                self._table_columns.extend([""] * (index + 1 - len(self._table_columns)))
            self._table_columns[index] = slug
            return slug
        if index < len(self._table_columns):
            return self._table_columns[index]
        return ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        if self._skip_iframe_depth:
            if normalized_tag == "iframe":
                self._skip_iframe_depth += 1
            return
        if normalized_tag == "iframe":
            placeholder = self._video_placeholder(attrs)
            if placeholder:
                self._append(placeholder)
                self._skip_iframe_depth = 1
                return
        if not self._cell and normalized_tag in {"td", "th"}:
            self._cell = _BufferedCell(tag, attrs)
            return
        if normalized_tag == "table":
            if self._table_depth == 0:
                self._table_columns = []
                self._table_col_index = 0
            self._append('<div class="kpress-table-wrap">')
            self._table_depth += 1
        elif normalized_tag == "tr" and self._table_depth >= 1 and self._cell is None:
            self._table_col_index = 0
        normalized_attrs = self._attrs_for_tag(normalized_tag, attrs)
        self._append(f"<{tag}{_render_attrs(normalized_attrs)}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        if self._skip_iframe_depth:
            return
        if normalized_tag == "iframe":
            placeholder = self._video_placeholder(attrs)
            if placeholder:
                self._append(placeholder)
                return
        if normalized_tag == "table":
            self._append('<div class="kpress-table-wrap">')
        normalized_attrs = self._attrs_for_tag(normalized_tag, attrs)
        self._append(f"<{tag}{_render_attrs(normalized_attrs)} />")
        if normalized_tag == "table":
            self._append("</div>")

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if self._skip_iframe_depth:
            if normalized_tag == "iframe":
                self._skip_iframe_depth -= 1
            return
        if self._cell and normalized_tag == self._cell.tag.lower():
            self._flush_cell()
            return
        self._append(f"</{tag}>")
        if normalized_tag == "table" and self._table_depth > 0:
            self._table_depth -= 1
            self._append("</div>")

    def handle_data(self, data: str) -> None:
        if self._skip_iframe_depth:
            return
        self._append(data)
        self._append_text(data)

    def handle_entityref(self, name: str) -> None:
        if self._skip_iframe_depth:
            return
        self._append(f"&{name};")
        self._append_text(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._skip_iframe_depth:
            return
        self._append(f"&#{name};")
        self._append_text(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        if self._skip_iframe_depth:
            return
        self._append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        if self._skip_iframe_depth:
            return
        self._append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        if self._skip_iframe_depth:
            return
        self._append(f"<?{data}>")


def _postprocess_html(html: str) -> str:
    parser = _KpressHtmlPostprocessor()
    parser.feed(html)
    parser.close()
    return "".join(parser.parts)


class _AnchorAuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag
        self._collect(attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag
        self._collect(attrs)

    def _collect(self, attrs: list[tuple[str, str | None]]) -> None:
        element_id = _attr_value(attrs, "id")
        if element_id:
            self.ids.add(element_id)
        anchor_name = _attr_value(attrs, "name")
        if anchor_name:
            self.ids.add(anchor_name)
        href = _attr_value(attrs, "href")
        if href and href.startswith("#") and len(href) > 1 and not href.startswith("#:~:text="):
            self.hrefs.append(href)


def _broken_anchor_diagnostics(html: str) -> list[Diagnostic]:
    parser = _AnchorAuditParser()
    parser.feed(html)
    parser.close()
    diagnostics: list[Diagnostic] = []
    for href in parser.hrefs:
        target = unquote(href[1:])
        if target not in parser.ids:
            diagnostics.append(
                Diagnostic(
                    type="broken_anchor",
                    message=f"Internal link target '{href}' was not found.",
                    location=href,
                )
            )
    return diagnostics


def _footnote_definition_labels(env: dict[str, Any]) -> dict[str, int]:
    footnotes_raw = env.get("footnotes")
    if not isinstance(footnotes_raw, Mapping):
        return {}
    footnotes = cast(Mapping[str, object], footnotes_raw)
    refs_raw = footnotes.get("refs")
    if not isinstance(refs_raw, Mapping):
        return {}
    refs = cast(Mapping[object, object], refs_raw)

    labels: dict[str, int] = {}
    for raw_label, raw_index in refs.items():
        if not isinstance(raw_label, str) or not isinstance(raw_index, int):
            continue
        label = raw_label[1:] if raw_label.startswith(":") else raw_label
        labels[label] = raw_index
    return labels


def _literal_footnote_references(tokens: list[Token]) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token.type != "inline":
            continue
        content = _INLINE_CODE_SPAN_RE.sub("", token.content)
        for match in _FOOTNOTE_REF_RE.finditer(content):
            label = match.group(1)
            if label in seen:
                continue
            labels.append(label)
            seen.add(label)
    return labels


def _footnote_diagnostics(tokens: list[Token], env: dict[str, Any]) -> list[Diagnostic]:
    definition_labels = _footnote_definition_labels(env)
    diagnostics: list[Diagnostic] = []
    for label in _literal_footnote_references(tokens):
        if label in definition_labels:
            continue
        diagnostics.append(
            Diagnostic(
                type="missing_footnote",
                message=f"Footnote reference '[^{label}]' has no matching definition.",
                location=f"[^{label}]",
            )
        )
    for label, index in definition_labels.items():
        if index >= 0:
            continue
        diagnostics.append(
            Diagnostic(
                type="unused_footnote",
                message=f"Footnote definition '[^{label}]' is never referenced.",
                location=f"[^{label}]",
            )
        )
    return diagnostics


def _toc_entries(headings: list[Heading]) -> list[TocEntry]:
    toc_headings = headings
    if headings and headings[0].level == 1 and sum(item.level == 1 for item in headings) == 1:
        toc_headings = headings[1:]
    return [
        TocEntry(level=item.level, title=item.title, href=f"#{item.id}") for item in toc_headings
    ]


def _collect_footnotes(md: MarkdownIt, tokens: list[Token], env: dict[str, Any]) -> list[Footnote]:
    footnotes: list[Footnote] = []
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token.type != "footnote_open":
            idx += 1
            continue
        ident = _footnote_ident(token)
        content_tokens: list[Token] = []
        idx += 1
        while idx < len(tokens) and tokens[idx].type != "footnote_close":
            if tokens[idx].type != "footnote_anchor":
                content_tokens.append(tokens[idx])
            idx += 1
        html = md.renderer.render(content_tokens, md.options, env).strip()
        footnotes.append(Footnote(id=ident, html=html))
        idx += 1
    return footnotes


def parse_markdown(
    markdown: str,
    *,
    title: str,
    trust_mode: TrustMode = "trusted-local",
    math: MathMode = "auto",
    diagrams: DiagramMode = "auto",
) -> DocumentTree:
    """Parse KPress Markdown into stable, KPress-owned HTML."""

    if trust_mode == "untrusted":
        markdown = _escape_untrusted_raw_html(markdown)

    md = _markdown_it(trust_mode=trust_mode, diagrams=diagrams, math=math)
    env: dict[str, Any] = {}
    tokens = md.parse(markdown, env)
    _mark_standalone_image_figures(tokens)
    headings, _ = _add_heading_ids(tokens)
    footnotes = _collect_footnotes(md, tokens, env)
    html = md.renderer.render(tokens, md.options, env)
    html = _postprocess_tasks(html)
    html = _postprocess_html(html)

    diagnostics: list[Diagnostic] = []
    diagnostics.extend(_math_diagnostics(env))
    diagnostics.extend(_footnote_diagnostics(tokens, env))
    if trust_mode in {"public-static", "sanitized-local"}:
        html, html_diagnostics = sanitize_raw_html(html, trust_mode)
        diagnostics.extend(html_diagnostics)
    diagnostics.extend(_broken_anchor_diagnostics(html))

    toc = _toc_entries(headings)
    return DocumentTree(
        title=title,
        html=html.rstrip(),
        profile="document",
        headings=headings,
        toc=toc,
        footnotes=footnotes,
        diagnostics=diagnostics,
        has_math=bool(env.get("kpress_has_math")),
    )
