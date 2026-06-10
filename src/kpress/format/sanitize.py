"""HTML sanitizer policy for KPress render trust modes."""

from __future__ import annotations

import re

import nh3

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


def sanitize_raw_html(html: str, trust_mode: TrustMode) -> tuple[str, list[Diagnostic]]:
    """Return raw HTML according to the configured trust mode."""

    if trust_mode == "trusted-local":
        return html, []

    sanitized = nh3.clean(
        html,
        tags=_ALLOWED_TAGS,
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
