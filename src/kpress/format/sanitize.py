"""HTML sanitizer policy for KPress render trust modes."""

from __future__ import annotations

import re
from collections.abc import Iterable

import nh3

from kpress.contract import (
    PUBLIC_PASS_THROUGH_ATTRIBUTE_PREFIXES,
    PUBLIC_PASS_THROUGH_ATTRIBUTES,
    PUBLIC_PASS_THROUGH_TAGS,
)
from kpress.errors import KPressInvalidRequestError
from kpress.format.model import Diagnostic, TrustMode

_ALLOWED_TAGS = nh3.ALLOWED_TAGS | {
    "annotation",
    "button",
    "circle",
    "defs",
    "desc",
    "ellipse",
    "g",
    "section",
    "main",
    "input",
    "link",
    "line",
    "linearGradient",
    "math",
    "menclose",
    "mfenced",
    "mfrac",
    "mi",
    "mmultiscripts",
    "mn",
    "mo",
    "mover",
    "mprescripts",
    "mroot",
    "mrow",
    "ms",
    "mspace",
    "msqrt",
    "mstyle",
    "msub",
    "msubsup",
    "msup",
    "mtable",
    "mtd",
    "mtext",
    "mtr",
    "munder",
    "munderover",
    "none",
    "path",
    "polygon",
    "polyline",
    "radialGradient",
    "rect",
    "semantics",
    "stop",
    "svg",
    "text",
    "title",
    "tspan",
    "use",
}
_GLOBAL_ATTRIBUTES = {
    "aria-controls",
    "aria-expanded",
    "aria-hidden",
    "aria-label",
    "aria-selected",
    "checked",
    "class",
    "columnalign",
    "columnspan",
    "cx",
    "cy",
    "d",
    "disabled",
    "display",
    "encoding",
    "fill",
    "form",
    "height",
    "href",
    "id",
    "marker-end",
    "marker-mid",
    "marker-start",
    "offset",
    "opacity",
    "points",
    "r",
    "linethickness",
    "loading",
    "mathsize",
    "mathvariant",
    "notation",
    "preserveAspectRatio",
    "preserveaspectratio",
    "refX",
    "refY",
    "refx",
    "refy",
    "rel",
    "rowalign",
    "rowspan",
    "separator",
    "role",
    "src",
    "stretchy",
    "stroke",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-width",
    "tabindex",
    "target",
    "title",
    "transform",
    "type",
    "viewBox",
    "viewbox",
    "width",
    "xmlns",
    "x",
    "x1",
    "x2",
    "y",
    "y1",
    "y2",
}
_ALLOWED_ATTRIBUTES = {
    tag: set(attrs) | _GLOBAL_ATTRIBUTES for tag, attrs in nh3.ALLOWED_ATTRIBUTES.items()
}
_ALLOWED_ATTRIBUTES["*"] = _GLOBAL_ATTRIBUTES
_ALLOWED_URL_SCHEMES = {"http", "https", "mailto", "tel"}
_GENERIC_ATTRIBUTE_PREFIXES = {"data-"}

# Whitelisted pass-through tags always admitted (pinned in kpress.contract). A render
# unions any host `extra_tags` on top of this default set. `class`/`data-*` survive on
# them (class via _GLOBAL_ATTRIBUTES, data-* via _GENERIC_ATTRIBUTE_PREFIXES); `style`,
# `on*`, and unsafe-URL attributes stay sanitized — see PUBLIC_PASS_THROUGH_ATTRIBUTES.
_DEFAULT_PASS_THROUGH_TAGS = set(PUBLIC_PASS_THROUGH_TAGS)
# Attribute policy for the untrusted whitelist-only profile (raw HTML otherwise stripped):
# only `class` plus the `data-*` prefix ride through on a whitelisted tag.
_PASS_THROUGH_ATTRIBUTES = {"*": set(PUBLIC_PASS_THROUGH_ATTRIBUTES)}
_PASS_THROUGH_ATTRIBUTE_PREFIXES = set(PUBLIC_PASS_THROUGH_ATTRIBUTE_PREFIXES)


# The shape of an admissible pass-through tag name: a standard HTML element or a
# custom-element name — lowercase, starting with a letter, optionally containing
# digits/hyphens. The same shape markdown-it / nh3 accept.
EXTRA_TAG_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")

# Tag names that must NEVER be admitted as pass-through, even though they match the
# shape regex. `script`/`style` are in nh3's clean-content set: admitting either makes
# ammonia raise (a hard render-time failure). The rest are active/embedding/metadata
# elements that carry real risk (script execution, navigation, form capture,
# parser-context confusion) and have no place in a *styling* whitelist. Custom elements
# (hyphenated) are inert by the HTML spec, so the escape hatch for genuinely custom
# markup stays open. Shared with kpress.publish.config, which reports violations as
# `format.html.extra_tags` errors at config time.
FORBIDDEN_EXTRA_TAGS = frozenset(
    {
        "script",
        "style",
        "iframe",
        "object",
        "embed",
        "base",
        "meta",
        "link",
        "noscript",
        "template",
        "textarea",
        "select",
        "option",
        "form",
        "title",
        "xmp",
        "plaintext",
        "noembed",
        "noframes",
        "frame",
        "frameset",
        "applet",
    }
)


def _pass_through_tags(extra_tags: Iterable[str] | None) -> set[str]:
    """The whitelist for a render: the always-on defaults unioned with host extras.

    Every extra tag is validated here as well as at config time, so the direct
    ``RenderOptions.extra_tags`` path (which never passes through config loading) fails
    with a clear ``KPressInvalidRequestError`` instead of an nh3 panic
    (``script``/``style``) or a silently ineffective entry.
    """

    tags: set[str] = set(_DEFAULT_PASS_THROUGH_TAGS)
    for tag in extra_tags or ():
        if not EXTRA_TAG_NAME_RE.match(tag):
            msg = (
                f"Invalid extra_tags entry {tag!r}; expected a lowercase HTML or "
                f"custom-element tag name (letters, digits, hyphens)"
            )
            raise KPressInvalidRequestError(msg)
        if tag in FORBIDDEN_EXTRA_TAGS:
            msg = (
                f"Forbidden extra_tags entry {tag!r}: active, embedding, and metadata "
                f"elements cannot be admitted as styleable pass-through tags. Use a "
                f"hyphenated custom-element name (e.g. 'x-callout') for custom markup."
            )
            raise KPressInvalidRequestError(msg)
        tags.add(tag)
    return tags


def sanitize_raw_html(
    html: str,
    trust_mode: TrustMode,
    *,
    extra_tags: Iterable[str] | None = None,
) -> tuple[str, list[Diagnostic]]:
    """Return raw HTML according to the configured trust mode.

    Whitelisted pass-through tags (``<span>``/``<div>`` plus any ``extra_tags`` the host
    activates) survive in every sanitizing mode, carrying ``class``/``data-*`` but never
    ``style``/``on*``/unsafe URLs. ``trusted-local`` skips sanitization entirely.
    ``untrusted`` uses a whitelist-only profile: ONLY the pass-through tags survive and
    every other tag is stripped (its text content is kept), so untrusted stays at least
    as strict as ``public-static`` while still admitting the styleable whitelist.
    """

    if trust_mode == "trusted-local":
        return html, []

    if trust_mode == "untrusted":
        sanitized = nh3.clean(
            html,
            tags=_pass_through_tags(extra_tags),
            attributes=_PASS_THROUGH_ATTRIBUTES,
            generic_attribute_prefixes=_PASS_THROUGH_ATTRIBUTE_PREFIXES,
            url_schemes=_ALLOWED_URL_SCHEMES,
            link_rel=None,
        )
    else:
        sanitized = nh3.clean(
            html,
            tags=_ALLOWED_TAGS | _pass_through_tags(extra_tags),
            attributes=_ALLOWED_ATTRIBUTES,
            generic_attribute_prefixes=_GENERIC_ATTRIBUTE_PREFIXES,
            url_schemes=_ALLOWED_URL_SCHEMES,
            link_rel=None,
        )
    diagnostics: list[Diagnostic] = []
    if sanitized != html:
        diagnostics.append(
            Diagnostic(
                type="html_sanitized",
                message="Unsafe raw HTML was removed for this trust mode.",
                severity="warning",
            )
        )
    return sanitized, diagnostics


_SVG_CAMELCASE = {
    "viewbox": "viewBox",
    "preserveaspectratio": "preserveAspectRatio",
    "refx": "refX",
    "refy": "refY",
}

# Match a whitespace boundary followed by one of the lowercased SVG attribute
# names followed immediately by `=`. The whitespace prefix alone is not a
# sufficient anchor (a quoted value such as an aria-label could contain
# ` viewbox=`), so the substitution is additionally restricted to tag interiors
# outside quoted attribute values (see `_restore_camelcase_at_attributes`).
_RESTORE_SVG_CAMELCASE = re.compile(
    r"(?:\s)(?P<name>" + "|".join(_SVG_CAMELCASE) + r")=",
)

# Tokens that delimit attribute position: a complete double-quoted attribute
# value (nh3 emits double quotes), or a tag open/close angle bracket. Quoted
# runs are matched first so a `<`/`>` inside a value cannot toggle tag state.
_TAG_OR_QUOTED_VALUE = re.compile(r'"[^"]*"|[<>]')


def _restore_camelcase_at_attributes(svg: str) -> str:
    """Apply the camelCase restore only at tag-attribute positions.

    Segments inside a tag and outside quoted values are rewritten; quoted
    attribute values and text content pass through verbatim.
    """

    def restore(segment: str) -> str:
        return _RESTORE_SVG_CAMELCASE.sub(
            lambda match: " " + _SVG_CAMELCASE[match.group("name")] + "=", segment
        )

    parts: list[str] = []
    pos = 0
    in_tag = False
    for token in _TAG_OR_QUOTED_VALUE.finditer(svg):
        segment = svg[pos : token.start()]
        parts.append(restore(segment) if in_tag else segment)
        text = token.group(0)
        if text == "<":
            in_tag = True
        elif text == ">":
            in_tag = False
        parts.append(text)
        pos = token.end()
    tail = svg[pos:]
    parts.append(restore(tail) if in_tag else tail)
    return "".join(parts)


def sanitize_generated_svg(svg: str) -> str:
    """Return KPress-generated inline SVG using the public-static sanitizer policy."""

    sanitized = nh3.clean(
        svg,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        generic_attribute_prefixes=_GENERIC_ATTRIBUTE_PREFIXES,
        url_schemes=_ALLOWED_URL_SCHEMES,
        link_rel=None,
    ).strip()
    # nh3 lower-cases attribute names; restore the SVG-spec camelCase only at
    # tag-attribute positions, never inside text content or quoted values. Each
    # entry maps the lowercased name to its canonical SVG form.
    return _restore_camelcase_at_attributes(sanitized)
