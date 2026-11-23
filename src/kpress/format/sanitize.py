"""HTML sanitizer policy for KPress render trust modes."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urlsplit

import nh3

from kpress.contract import (
    PUBLIC_PASS_THROUGH_ATTRIBUTE_PREFIXES,
    PUBLIC_PASS_THROUGH_ATTRIBUTES,
    PUBLIC_PASS_THROUGH_TAGS,
)
from kpress.errors import KPressInvalidRequestError
from kpress.format.model import Diagnostic, TrustMode

# This nh3 policy and `_SanitizerAudit` describe the same decisions: update both
# whenever tags, attributes, set values, URL schemes, or pass-through restrictions
# change.
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
# Presentational `align` on block containers and headings, as in a README's centered
# icon block. Its value is an enumerated keyword with no URL, script, or CSS channel;
# nh3 already admits it on `img`, `hr`, and table elements, and GitHub admits it here.
for _align_tag in ("div", "p", "h1", "h2", "h3", "h4", "h5", "h6"):
    _ALLOWED_ATTRIBUTES[_align_tag] = (
        _ALLOWED_ATTRIBUTES.get(_align_tag, set()) | _GLOBAL_ATTRIBUTES | {"align"}
    )
_ALLOWED_URL_SCHEMES = {"http", "https", "mailto", "tel"}
_GENERIC_ATTRIBUTE_PREFIXES = {"data-"}
# `<input>` is admitted only as the box of a task list item (`_TASK_CHECKBOX_TOKEN` in
# markdown.py): a disabled checkbox, ticked or not. Any other input is a live form
# control, such as a text or password field, a submit button that `form` can tie to a
# form on the host page, or `type="image"` loading a remote image. The sanitizer cannot
# tell KPress's box from an input an author typed, so every `<input>` keeps only these
# attributes, each with this one value, and is written with them in this order, which
# is the order of KPress's own box: a sanitized input is byte for byte KPress's box.
# `class` survives only when it names the box class, and then as that class alone, so a
# forged input cannot take another KPress class.
_TASK_CHECKBOX_CLASS = "task-list-item-checkbox"
_INPUT_VALUES = {
    "class": _TASK_CHECKBOX_CLASS,
    "checked": "checked",
    "disabled": "disabled",
    "type": "checkbox",
}
_INPUT_ATTRIBUTES = frozenset(_INPUT_VALUES)
# The attributes every input is given. nh3 runs `attribute_filter` after it sets these,
# so each must also be in `_INPUT_ATTRIBUTES`, or the filter would remove it again.
_INPUT_SET_VALUES = {name: _INPUT_VALUES[name] for name in ("disabled", "type")}
# nh3 adds the set values it finds missing in hash order, so `<input>` would come out
# with `disabled` and `type` in either order; `_canonical_inputs` writes every input it
# kept in `_INPUT_VALUES` order. Inside nh3's output this pattern matches only a real
# tag: text escapes `<`, and an attribute value escapes `"`.
_SANITIZED_INPUT_RE = re.compile(
    "<input((?: (?:"
    + "|".join(re.escape(f'{name}="{value}"') for name, value in _INPUT_VALUES.items())
    + "))*)>"
)
# Attributes whose presence is their meaning: `disabled=""` and `disabled="disabled"`
# are the same, so setting one over the other changes nothing a reader receives.
_BOOLEAN_ATTRIBUTES = frozenset({"checked", "disabled"})
# The class names in an attribute value: HTML splits it on ASCII whitespace.
_ASCII_WHITESPACE_RE = re.compile(r"[\t\n\f\r ]+")


def _class_names(value: str) -> list[str]:
    return [name for name in _ASCII_WHITESPACE_RE.split(value) if name]


def _input_attribute(name: str, value: str) -> str | None:
    """The value an input keeps for attribute *name*, or None when it loses it."""

    if name == "class":
        return _TASK_CHECKBOX_CLASS if _TASK_CHECKBOX_CLASS in _class_names(value) else None
    return _INPUT_VALUES.get(name)


def _canonical_input(match: re.Match[str]) -> str:
    present = set(match.group(1).split())
    return (
        "<input"
        + "".join(
            f' {name}="{value}"'
            for name, value in _INPUT_VALUES.items()
            if f'{name}="{value}"' in present
        )
        + ">"
    )


def _canonical_inputs(sanitized: str) -> tuple[str, int]:
    """Write each input of nh3 output in `_INPUT_VALUES` order; also count them."""

    return _SANITIZED_INPUT_RE.subn(_canonical_input, sanitized)


# Whitelisted pass-through tags always admitted (pinned in kpress.contract). A render
# unions any host `extra_tags` on top of this default set. `class`/`data-*` survive on
# them (class via _GLOBAL_ATTRIBUTES, data-* via _GENERIC_ATTRIBUTE_PREFIXES); `style`,
# `on*`, and unsafe-URL attributes stay sanitized — see PUBLIC_PASS_THROUGH_ATTRIBUTES.
_DEFAULT_PASS_THROUGH_TAGS = set(PUBLIC_PASS_THROUGH_TAGS)
_PASS_THROUGH_ATTRIBUTE_PREFIXES = set(PUBLIC_PASS_THROUGH_ATTRIBUTE_PREFIXES)


# The shape of an admissible pass-through tag name: a standard HTML element or a
# custom-element name — lowercase, starting with a letter, optionally containing
# digits/hyphens. The same shape markdown-it / nh3 accept.
EXTRA_TAG_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")

# Tag names that must NEVER be admitted as pass-through, even though they match the
# shape regex. `script`/`style` are in nh3's clean-content set: admitting either makes
# ammonia raise (a hard render-time failure). The rest are active/embedding/metadata
# elements that carry real risk (script execution, navigation, form capture, media
# embedding, parser-context confusion) and have no place in a *styling* whitelist.
# Custom elements (hyphenated) are inert by the HTML spec, so the escape hatch for
# genuinely custom markup stays open. Shared with kpress.publish.config, which reports
# violations as `format.html.extra_tags` errors at config time.
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
        "video",
        "audio",
        "source",
        "track",
        "picture",
    }
)


# Attribute names that must NEVER be admitted on pass-through tags, plus the `on*`
# handler prefix (rejected by pattern below). `style` reopens the CSS channel the
# policy exists to close; URL-bearing names (`href`, `src`, ...) turn an inert styling
# tag into a navigation/embedding vector; `id`/`name` enable DOM clobbering (the same
# hole the page-model fix closed); `is`/`slot` hook custom-element/shadow behavior;
# `http-equiv`/`srcdoc` are parser-context hazards. Shared with kpress.publish.config,
# which reports violations as `format.html.extra_attributes` errors at config time.
FORBIDDEN_EXTRA_ATTRIBUTES = frozenset(
    {
        "style",
        "href",
        "src",
        "srcset",
        "srcdoc",
        "action",
        "formaction",
        "background",
        "ping",
        "poster",
        "data",
        "cite",
        "usemap",
        "id",
        "name",
        "is",
        "slot",
        "http-equiv",
        "target",
        "download",
        "rel",
    }
)


def _pass_through_attributes(extra_attributes: Iterable[str] | None) -> frozenset[str]:
    """The extra attribute names admitted on whitelist-only tags for a render.

    Validated here as well as at config time, so the direct
    ``RenderOptions.extra_attributes`` path fails with a clear
    ``KPressInvalidRequestError`` instead of silently dropping the attribute.
    """

    names: set[str] = set()
    for name in extra_attributes or ():
        if not EXTRA_TAG_NAME_RE.match(name):
            msg = (
                f"Invalid extra_attributes entry {name!r}; expected a lowercase "
                f"attribute name (letters, digits, hyphens)"
            )
            raise KPressInvalidRequestError(msg)
        if name in FORBIDDEN_EXTRA_ATTRIBUTES or name.startswith("on"):
            msg = (
                f"Forbidden extra_attributes entry {name!r}: event handlers, style, "
                f"URL-bearing, and DOM-identity attributes cannot be admitted on "
                f"pass-through tags. Use a data-* attribute for open-ended payload."
            )
            raise KPressInvalidRequestError(msg)
        names.add(name)
    return frozenset(names)


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


# Elements whose content html5ever, which nh3 parses with, reads as text: the raw-text
# elements of the HTML standard, `noscript` among them because html5ever parses with
# scripting on. Python's HTMLParser reads only `script` and `style` this way before
# 3.14, and `noscript` only when asked to, so both parsers below enter text mode for
# this set themselves, also after `<noscript/>`, since HTML ignores the slash there.
_RAW_TEXT_ELEMENTS = ("script", "style", "xmp", "iframe", "noembed", "noframes", "noscript")
_VOID_ELEMENTS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "source",
        "track",
        "wbr",
    }
)
_FOREIGN_ROOTS = frozenset({"math", "svg"})
# MathML text integration points: html5ever parses HTML inside them again.
_MATHML_TEXT_ELEMENTS = frozenset({"mi", "mn", "mo", "ms", "mtext"})


@dataclass(frozen=True)
class _InputAudit:
    """One `<input>` the audit saw: where, whether it survives, and how it changes."""

    location: str
    survives: bool
    diagnostics: list[Diagnostic]


def _input_diagnostics(attrs: list[tuple[str, str | None]], location: str) -> list[Diagnostic]:
    """What sanitizing removes from and sets on an input with *attrs*, as nh3 does it."""

    def diagnostic(message: str) -> Diagnostic:
        return Diagnostic(
            type="html_sanitized_attribute",
            message=message,
            severity="warning",
            location=location,
        )

    # The first of a repeated attribute is the one HTML keeps.
    values: dict[str, str | None] = {}
    for name, value in attrs:
        values.setdefault(name, value)
    diagnostics: list[Diagnostic] = []
    for name, value in values.items():
        if _input_attribute(name, value or "") is None:
            diagnostics.append(diagnostic(f"Removed attribute {name!r} from <input>."))
    for name, value in _INPUT_VALUES.items():
        if name in _BOOLEAN_ATTRIBUTES:
            # Presence is the meaning, so only adding a missing one changes anything.
            changed = name in _INPUT_SET_VALUES and name not in values
        elif name in values:
            # A class without the box's name is reported as removed above.
            kept = _input_attribute(name, values[name] or "")
            changed = kept is not None and values[name] != value
        else:
            changed = name in _INPUT_SET_VALUES
        if changed:
            diagnostics.append(diagnostic(f"Set attribute {name!r} to {value!r} on <input>."))
    return diagnostics


class _SanitizerAudit(HTMLParser):
    """Mirror the nh3 policy to diagnose each removed tag and attribute and each set value.

    Keep this audit in sync with the policy constants above and the
    ``_restrict_pass_through`` filter and ``set_tag_attribute_values`` in
    ``sanitize_raw_html``.
    """

    def __init__(
        self,
        *,
        pass_through: set[str],
        extra_attributes: frozenset[str],
    ) -> None:
        super().__init__(convert_charrefs=False)
        self.allowed_tags = _ALLOWED_TAGS | pass_through
        self.restricted_tags = pass_through - _ALLOWED_TAGS
        self.extra_attributes = extra_attributes
        self._entries: list[Diagnostic | _InputAudit] = []
        self._open: list[str] = []

    def _location(self) -> str:
        line, offset = self.getpos()
        return f"line {line}, column {offset + 1}"

    def _attribute_allowed(self, tag: str, name: str, value: str | None) -> bool:
        if tag in self.restricted_tags:
            allowed = (
                name in PUBLIC_PASS_THROUGH_ATTRIBUTES
                or name in self.extra_attributes
                or any(name.startswith(prefix) for prefix in _PASS_THROUGH_ATTRIBUTE_PREFIXES)
            )
        else:
            allowed_names = _ALLOWED_ATTRIBUTES.get(tag, _GLOBAL_ATTRIBUTES)
            allowed = name in allowed_names or any(
                name.startswith(prefix) for prefix in _GENERIC_ATTRIBUTE_PREFIXES
            )
        if not allowed:
            return False
        if name in {"href", "src"} and value:
            scheme = urlsplit(value.strip()).scheme.lower()
            if scheme and scheme not in _ALLOWED_URL_SCHEMES:
                return False
        return True

    def _removed_tag(self, tag: str, location: str) -> Diagnostic:
        return Diagnostic(
            type="html_sanitized_tag",
            message=f"Removed raw HTML tag <{tag}>.",
            severity="warning",
            location=location,
        )

    def _audit_tag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        location = self._location()
        if tag not in self.allowed_tags:
            self._entries.append(self._removed_tag(tag, location))
            return
        if tag == "input":
            self._entries.append(
                _InputAudit(
                    location=location,
                    survives=self._input_survives(),
                    diagnostics=_input_diagnostics(attrs, location),
                )
            )
            return
        for name, value in attrs:
            if not self._attribute_allowed(tag, name, value):
                self._entries.append(
                    Diagnostic(
                        type="html_sanitized_attribute",
                        message=f"Removed attribute {name!r} from <{tag}>.",
                        severity="warning",
                        location=location,
                    )
                )

    def _input_survives(self) -> bool:
        """Whether an input at this point survives, judged from its open ancestors.

        html5ever makes an input in SVG or MathML a foreign element, which nh3 removes
        with its content, unless a MathML text element encloses it; a `<template>`'s
        content never reaches the output. This model leaves out how html5ever closes
        foreign content early, so `sanitize_raw_html` trusts it only when the number
        of inputs it predicts matches the output.
        """

        for tag in reversed(self._open):
            if tag in _MATHML_TEXT_ELEMENTS:
                return True
            if tag in _FOREIGN_ROOTS or tag == "template":
                return False
        return True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._audit_tag(tag, attrs)
        if tag in _RAW_TEXT_ELEMENTS:
            self.set_cdata_mode(tag)
        if tag not in _VOID_ELEMENTS:
            self._open.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._audit_tag(tag, attrs)
        if tag in _RAW_TEXT_ELEMENTS:
            self.set_cdata_mode(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in self._open:
            del self._open[len(self._open) - 1 - self._open[::-1].index(tag) :]

    @property
    def inputs_seen(self) -> int:
        return sum(isinstance(entry, _InputAudit) for entry in self._entries)

    def finish(self, survivors: int) -> tuple[list[Diagnostic], bool]:
        """The diagnostics, given how many inputs survived, and whether any is an input's.

        An input that did not survive is reported as removed, not edited. When the
        survival model disagrees with the output's count, the inputs that went are
        unknown, so no input is reported and the caller's catch-all covers them.
        """

        inputs = [entry for entry in self._entries if isinstance(entry, _InputAudit)]
        known = sum(entry.survives for entry in inputs) == survivors
        diagnostics: list[Diagnostic] = []
        reported_inputs = False
        for entry in self._entries:
            if isinstance(entry, Diagnostic):
                diagnostics.append(entry)
            elif not known:
                continue
            elif entry.survives:
                diagnostics.extend(entry.diagnostics)
                reported_inputs = reported_inputs or bool(entry.diagnostics)
            else:
                diagnostics.append(self._removed_tag("input", entry.location))
                reported_inputs = True
        return diagnostics, reported_inputs


def sanitize_raw_html(
    html: str,
    trust_mode: TrustMode,
    *,
    extra_tags: Iterable[str] | None = None,
    extra_attributes: Iterable[str] | None = None,
) -> tuple[str, list[Diagnostic]]:
    """Return raw HTML according to the configured trust mode.

    ``trusted`` skips sanitization entirely. ``sanitized`` applies the nh3 profile:
    the XSS-inert allow-set plus the pass-through whitelist (``<span>``/``<div>`` plus
    any ``extra_tags`` the host activates). Whitelist-only tags carry ``class``,
    ``data-*``, and any host-declared ``extra_attributes`` (inert semantic names like
    ``kind`` or ``term``, validated against a forbidden set) — never
    ``style``/``on*``/unsafe URLs. Standard HTML tags keep their fixed policy;
    ``extra_attributes`` widens only the whitelist-only (custom-element) tags. An
    ``<input>`` survives only as the disabled checkbox of a task list item.
    """

    if trust_mode == "trusted":
        return html, []

    pass_through = _pass_through_tags(extra_tags)
    extra_attrs = _pass_through_attributes(extra_attributes)
    # Tags admitted *only* via the pass-through whitelist carry the pass-through
    # attribute policy (class/data-*) — never id/href/src from _GLOBAL_ATTRIBUTES,
    # which the standard tags legitimately keep.
    # This also keeps content-authored ids off whitelisted custom elements
    # (DOM clobbering).
    restricted = pass_through - _ALLOWED_TAGS
    prefix_tuple = tuple(_PASS_THROUGH_ATTRIBUTE_PREFIXES)

    def _restrict_pass_through(element: str, attribute: str, value: str) -> str | None:
        if element == "input":
            return _input_attribute(attribute, value)
        if element not in restricted:
            # Standard tags keep their fixed policy: a host-declared extra attribute
            # rides only on whitelist-only tags, never widens standard HTML (unless
            # the name is independently allowed for this element anyway).
            if attribute in extra_attrs and attribute not in _ALLOWED_ATTRIBUTES.get(
                element, _GLOBAL_ATTRIBUTES
            ):
                return None
            return value
        if attribute in PUBLIC_PASS_THROUGH_ATTRIBUTES or attribute in extra_attrs:
            return value
        if attribute.startswith(prefix_tuple):
            return value
        return None

    filter_errors: list[Exception] = []

    def _attribute_filter(element: str, attribute: str, value: str) -> str | None:
        # nh3 keeps the attribute when its filter raises, so an error never reaches
        # nh3: the attribute goes, and the error is raised once nh3 returns.
        try:
            return _restrict_pass_through(element, attribute, value)
        except Exception as error:
            filter_errors.append(error)
            return None

    attributes = _ALLOWED_ATTRIBUTES
    if extra_attrs:
        # Extend the global allow-set so nh3 lets the names reach the filter; the
        # filter then confines them to whitelist-only tags.
        attributes = dict(_ALLOWED_ATTRIBUTES)
        attributes["*"] = _GLOBAL_ATTRIBUTES | extra_attrs

    audit = _SanitizerAudit(pass_through=pass_through, extra_attributes=extra_attrs)
    audit.feed(html)
    audit.close()

    sanitized = nh3.clean(
        html,
        tags=_ALLOWED_TAGS | pass_through,
        attributes=attributes,
        attribute_filter=_attribute_filter,
        generic_attribute_prefixes=_GENERIC_ATTRIBUTE_PREFIXES,
        set_tag_attribute_values={"input": _INPUT_SET_VALUES},
        url_schemes=_ALLOWED_URL_SCHEMES,
        link_rel=None,
    )
    if filter_errors:
        raise filter_errors[0]
    sanitized, survivors = _canonical_inputs(sanitized)
    diagnostics, reported_inputs = audit.finish(survivors)
    # Safety net for drift between the audit and the nh3 policy: report a change the
    # audit did not explain. Compare content, not strings, because nh3 also strips
    # comments and reserializes (a non-breaking space becomes `&nbsp;`), and neither
    # removes anything a reader would see. An input that changed is reported even beside
    # other diagnostics, since none of those explains it.
    check_inputs = not reported_inputs and bool(survivors or audit.inputs_seen)
    if sanitized != html and (not diagnostics or check_inputs):
        before, after = _content_events(html), _content_events(sanitized)
        if diagnostics:
            before, after = _input_events(before), _input_events(after)
        unexplained = before != after
    else:
        unexplained = False
    if unexplained:
        diagnostics.append(
            Diagnostic(
                type="html_sanitized",
                message="Raw HTML was removed or rewritten for this trust mode.",
                severity="warning",
            )
        )
    return sanitized, diagnostics


_ContentEvent = tuple[str, str, tuple[tuple[str, str], ...]]


class _ContentEvents(HTMLParser):
    """Reduce HTML to what a reader receives: start tags, their attributes, and text.

    Comments, declarations, end tags, attribute order and quoting, a boolean attribute's
    value, a repeated attribute after its first (HTML parsing drops it), entity spelling,
    and whitespace runs carry no content, so HTML that differs only there reduces to the
    same events. Removing an element always removes its start tag, so dropping end tags
    cannot hide a removal.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.events: list[_ContentEvent] = []
        self._text: list[str] = []

    def _flush_text(self) -> None:
        text = " ".join("".join(self._text).split())
        if text:
            self.events.append(("text", text, ()))
        self._text.clear()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._flush_text()
        values: dict[str, str] = {}
        for name, value in attrs:
            values.setdefault(name, "" if name in _BOOLEAN_ATTRIBUTES else value or "")
        self.events.append(("tag", tag, tuple(sorted(values.items()))))
        if tag in _RAW_TEXT_ELEMENTS:
            self.set_cdata_mode(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        self._text.append(data)

    def close(self) -> None:
        super().close()
        self._flush_text()


def _content_events(html: str) -> list[_ContentEvent]:
    parser = _ContentEvents()
    parser.feed(html)
    parser.close()
    return parser.events


def _input_events(events: list[_ContentEvent]) -> list[_ContentEvent]:
    return [event for event in events if event[:2] == ("tag", "input")]


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
    """Return KPress-generated inline SVG using the sanitized-mode nh3 profile."""

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
