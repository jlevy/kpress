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
# form on the host page, or `type="image"` loading a remote image, so an input whose
# `type` is not `checkbox` is removed (`_is_checkbox_type`), a missing `type` included,
# since that is a text field. The sanitizer cannot tell KPress's box from a checkbox an
# author typed, so every checkbox keeps only these attributes, each with this one value,
# and is written with them in this order, which is the order of KPress's own box: a
# sanitized input is byte for byte KPress's box. `class` survives only when it names the
# box class, and then as that class alone, so a forged input cannot take another KPress
# class.
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
# `type` is not one: an input without it is a text field, which nh3 must leave without
# `type` so that `_canonical_input` removes it.
_INPUT_SET_VALUES = {name: _INPUT_VALUES[name] for name in ("disabled",)}
# nh3 keeps an input's attributes in source order and adds the set values it finds
# missing in hash order; `_canonical_inputs` writes every checkbox in `_INPUT_VALUES`
# order and removes every other input. Inside nh3's output this pattern matches only a
# real tag: text escapes `<`, and an attribute value escapes `"`, so a value holding
# `<input>` cannot match, since every input nh3 keeps has a quoted `disabled`.
_SANITIZED_INPUT_RE = re.compile(
    "<input((?: (?:"
    + "|".join(re.escape(f'{name}="{value}"') for name, value in _INPUT_VALUES.items())
    + "))+)>"
)
# Where HTML may hold an `<input>` tag, which `_InputTags` then finds exactly.
_INPUT_TAG_OPEN_RE = re.compile("<input", re.IGNORECASE)
# A `<button>` is always `type="button"`: KPress's own buttons are, and any other type
# submits or resets a form, which a bare button inside a host page's form reaches
# without `form`. No sanitized element keeps `form`, which ties a control to a form
# anywhere on the host page by its id.
_BUTTON_SET_VALUES = {"type": "button"}
# A `<button>` in nh3's output, which always has `type`. As for inputs, an attribute value
# escapes `"`, so a value holding `<button ...>` cannot match.
_SANITIZED_BUTTON_RE = re.compile(r'<button((?: [^\s"\'>/=]+="[^"]*")+)>')
_ATTRIBUTE_NAME_RE = re.compile(r' ([^\s"\'>/=]+)="')
_SET_TAG_ATTRIBUTE_VALUES = {"input": _INPUT_SET_VALUES, "button": _BUTTON_SET_VALUES}
# Attributes whose presence is their meaning: `disabled=""` and `disabled="disabled"`
# are the same, so setting one over the other changes nothing a reader receives.
_BOOLEAN_ATTRIBUTES = frozenset({"checked", "disabled"})
# The class names in an attribute value: HTML splits it on ASCII whitespace.
_ASCII_WHITESPACE_RE = re.compile(r"[\t\n\f\r ]+")


def _class_names(value: str) -> list[str]:
    return [name for name in _ASCII_WHITESPACE_RE.split(value) if name]


def _is_checkbox_type(value: str | None) -> bool:
    """Whether an input's `type` value makes it a checkbox.

    HTML matches `type` ASCII case-insensitively; surrounding ASCII whitespace is
    trimmed too, which makes no input a checkbox that would be anything worse.
    """

    kind = (value or "").strip("\t\n\f\r ")
    return kind.isascii() and kind.lower() == "checkbox"


def _input_attribute(name: str, value: str) -> str | None:
    """The value an input keeps for attribute *name*, or None when it loses it."""

    if name == "class":
        return _TASK_CHECKBOX_CLASS if _TASK_CHECKBOX_CLASS in _class_names(value) else None
    if name == "type":
        return _INPUT_VALUES["type"] if _is_checkbox_type(value) else None
    return _INPUT_VALUES.get(name)


def _input_form(kept: Iterable[str]) -> str:
    """An input with the attributes named in *kept*, written in `_INPUT_VALUES` order."""

    names = set(kept)
    return (
        "<input"
        + "".join(f' {name}="{value}"' for name, value in _INPUT_VALUES.items() if name in names)
        + ">"
    )


def _canonical_inputs(sanitized: str) -> tuple[str, list[str]]:
    """Write each checkbox of nh3 output in `_INPUT_VALUES` order and remove any other input.

    Also return, in document order, the form of each input nh3 kept, checkbox or not.
    An input `_SANITIZED_INPUT_RE` does not match is removed too and not returned, so
    the audit finds it missing and adds the catch-all.
    """

    forms: list[str] = []
    boxes: set[str] = set()

    def canonical(match: re.Match[str]) -> str:
        present = set(match.group(1).split())
        form = _input_form(
            name for name, value in _INPUT_VALUES.items() if f'{name}="{value}"' in present
        )
        forms.append(form)
        if f'type="{_INPUT_VALUES["type"]}"' not in present:
            return ""
        boxes.add(form)
        return form

    canonical_html = _SANITIZED_INPUT_RE.sub(canonical, sanitized)
    return _without_other_inputs(canonical_html, boxes), forms


def _without_other_inputs(html: str, boxes: set[str]) -> str:
    """Remove from *html* each `<input>` tag that is not one of *boxes*.

    The pattern that rewrites inputs assumes nh3's spelling of one. An input it missed,
    say from a later nh3 that wrote `disabled` bare, would stay as nh3 wrote it, a text
    field among them; this removes it, failing closed. It removes rather than raises,
    as a filter error does: a filter error is a bug in KPress's own filter, while this
    would be a spelling change in an nh3 that `pyproject.toml` admits, and raising
    would fail every render holding an input on that version, where removing leaves
    safe HTML with the catch-all warning. The tests that pin the box's HTML still fail
    loudly on such a version.
    """

    if not _INPUT_TAG_OPEN_RE.search(html):
        return html
    tags = _InputTags(html)
    tags.feed(html)
    tags.close()
    pieces: list[str] = []
    position = 0
    for start, end in tags.spans:
        if html[start:end] in boxes:
            continue
        pieces.append(html[position:start])
        position = end
    if not pieces:
        return html
    pieces.append(html[position:])
    return "".join(pieces)


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
        "form",
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
# this set themselves, also after `<noscript/>`, since HTML ignores the slash there, and
# never in SVG or MathML, where each is an ordinary element.
_RAW_TEXT_ELEMENTS = ("script", "style", "xmp", "iframe", "noembed", "noframes", "noscript")
# The open elements that decide whether an input or a button survives
# (`_control_survives`): either in SVG or MathML is a foreign element, unless a MathML
# text element directly in MathML, where html5ever parses HTML again, encloses it, and
# a `<template>`'s content is never output.
_FOREIGN_ROOTS = frozenset({"math", "svg"})
_DROPS_INPUTS = _FOREIGN_ROOTS | {"template"}
_MATHML_TEXT_ELEMENTS = frozenset({"mi", "mn", "mo", "ms", "mtext"})
# The start tags that end SVG or MathML content where they appear, by HTML's rules for
# foreign content, which html5ever follows; `font` does only with one of the attributes
# below, and the end tags `</br>` and `</p>` do as well.
_BREAKS_OUT_OF_FOREIGN = frozenset(
    {
        "b",
        "big",
        "blockquote",
        "body",
        "br",
        "center",
        "code",
        "dd",
        "div",
        "dl",
        "dt",
        "em",
        "embed",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "head",
        "hr",
        "i",
        "img",
        "li",
        "listing",
        "menu",
        "meta",
        "nobr",
        "ol",
        "p",
        "pre",
        "ruby",
        "s",
        "small",
        "span",
        "strong",
        "strike",
        "sub",
        "sup",
        "table",
        "tt",
        "u",
        "ul",
        "var",
    }
)
_FONT_BREAKS_OUT_WITH = frozenset({"color", "face", "size"})
_END_TAGS_BREAKING_OUT = frozenset({"br", "p"})


class _Html5everContexts(HTMLParser):
    """Track the open elements that decide what html5ever makes of a tag.

    Those are SVG and MathML roots, a MathML text element directly in MathML, and a
    `<template>`, innermost last; every other element is left out, so an end tag costs
    amortized constant time however the document nests. The model leaves out, among
    other things, an HTML end tag that closes SVG open inside its element, so what it
    predicts is checked against nh3's output.
    """

    def __init__(self, *, convert_charrefs: bool) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self._contexts: list[str] = []
        self._context_counts: dict[str, int] = {}

    def _in_foreign_content(self) -> bool:
        return bool(self._contexts) and self._contexts[-1] in _FOREIGN_ROOTS

    def _pop_context(self) -> str:
        closed = self._contexts.pop()
        self._context_counts[closed] -= 1
        return closed

    def _leave_foreign_content(self) -> None:
        while self._in_foreign_content():
            self._pop_context()

    def _start(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Before a start tag is handled, leave the foreign content it ends."""

        if self._in_foreign_content() and (
            tag in _BREAKS_OUT_OF_FOREIGN
            or (tag == "font" and any(name in _FONT_BREAKS_OUT_WITH for name, _ in attrs))
        ):
            self._leave_foreign_content()

    def _opened(self, tag: str, *, self_closing: bool) -> None:
        """After a start tag is handled, enter what it opens."""

        foreign = self._in_foreign_content()
        if self_closing and (foreign or tag in _FOREIGN_ROOTS):
            return  # html5ever closes a self-closing foreign element at once
        if tag in _RAW_TEXT_ELEMENTS:
            self.set_cdata_mode(tag)
        if (
            tag in _FOREIGN_ROOTS
            or (tag == "template" and not foreign)
            or (tag in _MATHML_TEXT_ELEMENTS and self._contexts and self._contexts[-1] == "math")
        ):
            self._contexts.append(tag)
            self._context_counts[tag] = self._context_counts.get(tag, 0) + 1

    def set_cdata_mode(self, elem: str, **kwargs: bool) -> None:
        # In SVG or MathML html5ever reads no element's content as text, so neither the
        # elements HTMLParser enters text mode for itself nor `_RAW_TEXT_ELEMENTS` do.
        if not self._in_foreign_content():
            super().set_cdata_mode(elem, **kwargs)

    def parse_html_declaration(self, i: int) -> int:
        """Read `<![` as html5ever does: a bogus comment, which the first `>` ends, except
        a CDATA section in SVG or MathML, which is text up to `]]>`.

        HTMLParser reads a CDATA or marked section on to `]]>` wherever it is, which hid
        the tags after its first `>` from the audit though nh3 keeps them.
        """

        rawdata = self.rawdata
        if not rawdata.startswith("<![", i):
            return super().parse_html_declaration(i)
        if self._in_foreign_content() and rawdata.startswith("<![CDATA[", i):
            end = rawdata.find("]]>", i + 9)
            if end < 0:
                return -1
            self.handle_data(rawdata[i + 9 : end])
            return end + 3
        return self.parse_bogus_comment(i)

    def _end(self, tag: str) -> None:
        """Close the innermost open context of this name and every context inside it."""

        if self._in_foreign_content() and tag in _END_TAGS_BREAKING_OUT:
            self._leave_foreign_content()
            return
        if not self._context_counts.get(tag):
            return
        while self._contexts and self._pop_context() != tag:
            pass


class _InputTags(_Html5everContexts):
    """The span of each `<input>` start tag in HTML, as html5ever reads its tags.

    A tag is found by parsing, not by pattern, so an `<input>` written inside an
    attribute value, which nh3 0.3.5 leaves as it is, is not one.
    """

    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=False)
        self.spans: list[tuple[int, int]] = []
        self._line_starts = [0, *(match.end() for match in re.finditer("\n", html))]

    def _record(self, tag: str) -> None:
        if tag == "input":
            line, offset = self.getpos()
            start = self._line_starts[line - 1] + offset
            self.spans.append((start, start + len(self.get_starttag_text() or "")))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs)
        self._record(tag)
        self._opened(tag, self_closing=False)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs)
        self._record(tag)
        self._opened(tag, self_closing=True)

    def handle_endtag(self, tag: str) -> None:
        self._end(tag)


@dataclass(frozen=True)
class _InputAudit:
    """One `<input>` the audit saw: where, whether it survives parsing, the form nh3 keeps
    it in if it does, whether that is a checkbox, and how it changes when it is kept."""

    location: str
    survives: bool
    form: str
    diagnostics: list[Diagnostic]

    @property
    def box(self) -> bool:
        return f' type="{_INPUT_VALUES["type"]}"' in self.form


@dataclass(frozen=True)
class _ButtonAudit:
    """One `<button>` the audit saw: where, whether it survives parsing, the names of the
    attributes nh3 keeps on it, sorted, and how it changes when it is kept."""

    location: str
    survives: bool
    names: tuple[str, ...]
    diagnostics: list[Diagnostic]


def _expected_input_form(attrs: list[tuple[str, str | None]]) -> str:
    """The form nh3 keeps an input with *attrs* in, before `_canonical_inputs` runs."""

    values: dict[str, str | None] = {}
    for name, value in attrs:
        values.setdefault(name, value)  # the first of a repeated attribute wins
    kept = {
        name for name, value in values.items() if _input_attribute(name, value or "") is not None
    }
    return _input_form(kept | set(_INPUT_SET_VALUES))


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


class _SanitizerAudit(_Html5everContexts):
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
        self._entries: list[Diagnostic | _InputAudit | _ButtonAudit] = []

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
                    survives=self._control_survives(),
                    form=_expected_input_form(attrs),
                    diagnostics=_input_diagnostics(attrs, location),
                )
            )
            return
        found: list[Diagnostic] = []
        for name, value in attrs:
            if not self._attribute_allowed(tag, name, value):
                found.append(
                    Diagnostic(
                        type="html_sanitized_attribute",
                        message=f"Removed attribute {name!r} from <{tag}>.",
                        severity="warning",
                        location=location,
                    )
                )
        values = dict(reversed(attrs))  # the first of a repeated attribute wins
        set_values = _SET_TAG_ATTRIBUTE_VALUES.get(tag, {})
        for name, value in set_values.items():
            if values.get(name) != value:
                found.append(
                    Diagnostic(
                        type="html_sanitized_attribute",
                        message=f"Set attribute {name!r} to {value!r} on <{tag}>.",
                        severity="warning",
                        location=location,
                    )
                )
        if tag != "button":
            self._entries.extend(found)
            return
        kept = {name for name, value in values.items() if self._attribute_allowed(tag, name, value)}
        self._entries.append(
            _ButtonAudit(
                location=location,
                survives=self._control_survives(),
                names=tuple(sorted(kept | set(set_values))),
                diagnostics=found,
            )
        )

    def _control_survives(self) -> bool:
        """Whether an input or a button here survives, judged from the innermost open
        context.

        `sanitize_raw_html` trusts this only when the inputs and buttons it predicts kept
        are those in nh3's output, in order (`finish`).
        """

        return not self._contexts or self._contexts[-1] not in _DROPS_INPUTS

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs)
        self._audit_tag(tag, attrs)
        self._opened(tag, self_closing=False)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs)
        self._audit_tag(tag, attrs)
        self._opened(tag, self_closing=True)

    def handle_endtag(self, tag: str) -> None:
        self._end(tag)

    def finish(
        self, input_forms: list[str], button_names: list[tuple[str, ...]]
    ) -> tuple[list[Diagnostic], frozenset[str]]:
        """The diagnostics, given the form of each input nh3 kept and the sorted attribute
        names of each button it kept, in document order; and the tags, `input` or
        `button`, whose changes no diagnostic explains, for the caller's catch-all.

        An input or button that did not survive, or an input that is not a checkbox, is
        reported as removed, not edited. When the inputs predicted kept are not those nh3
        kept, in order and form, the inputs that went are unknown, so no input is
        reported and the catch-all covers them; buttons likewise. Two mispredictions that
        leave the same forms in the same order still pass, with each report at the
        other's location.
        """

        inputs = [entry for entry in self._entries if isinstance(entry, _InputAudit)]
        buttons = [entry for entry in self._entries if isinstance(entry, _ButtonAudit)]
        known = {
            "input": [entry.form for entry in inputs if entry.survives] == input_forms,
            "button": [entry.names for entry in buttons if entry.survives] == button_names,
        }
        diagnostics: list[Diagnostic] = []
        reported: set[str] = set()
        for entry in self._entries:
            if isinstance(entry, Diagnostic):
                diagnostics.append(entry)
                continue
            tag = "input" if isinstance(entry, _InputAudit) else "button"
            if not known[tag]:
                continue
            if entry.survives and (not isinstance(entry, _InputAudit) or entry.box):
                diagnostics.extend(entry.diagnostics)
                if entry.diagnostics:
                    reported.add(tag)
            else:
                diagnostics.append(self._removed_tag(tag, entry.location))
                reported.add(tag)
        present = {
            "input": bool(inputs or input_forms),
            "button": bool(buttons or button_names),
        }
        return diagnostics, frozenset(
            tag for tag, seen in present.items() if seen and tag not in reported
        )


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
    ``<input>`` survives only as the disabled checkbox of a task list item, a
    ``<button>`` only as ``type="button"``, and no element keeps ``form``.
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
        set_tag_attribute_values=_SET_TAG_ATTRIBUTE_VALUES,
        url_schemes=_ALLOWED_URL_SCHEMES,
        link_rel=None,
    )
    if filter_errors:
        raise filter_errors[0]
    button_names = [
        tuple(sorted(_ATTRIBUTE_NAME_RE.findall(match.group(1))))
        for match in _SANITIZED_BUTTON_RE.finditer(sanitized)
    ]
    sanitized, input_forms = _canonical_inputs(sanitized)
    diagnostics, unexplained_tags = audit.finish(input_forms, button_names)
    # Safety net for drift between the audit and the nh3 policy: report a change the
    # audit did not explain. Compare content, not strings, because nh3 also strips
    # comments and reserializes (a non-breaking space becomes `&nbsp;`), and neither
    # removes anything a reader would see. An input or button that changed is reported
    # even beside other diagnostics, since none of those explains it.
    if sanitized != html and (not diagnostics or unexplained_tags):
        before, after = _content_events(html), _content_events(sanitized)
        if diagnostics:
            before = _tag_events(before, unexplained_tags)
            after = _tag_events(after, unexplained_tags)
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


class _ContentEvents(_Html5everContexts):
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

    def _tag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._flush_text()
        values: dict[str, str] = {}
        for name, value in attrs:
            values.setdefault(name, "" if name in _BOOLEAN_ATTRIBUTES else value or "")
        self.events.append(("tag", tag, tuple(sorted(values.items()))))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs)
        self._tag(tag, attrs)
        self._opened(tag, self_closing=False)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs)
        self._tag(tag, attrs)
        self._opened(tag, self_closing=True)

    def handle_endtag(self, tag: str) -> None:
        self._end(tag)

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


def _tag_events(events: list[_ContentEvent], tags: frozenset[str]) -> list[_ContentEvent]:
    return [event for event in events if event[0] == "tag" and event[1] in tags]


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
    """Return KPress-generated inline SVG using the sanitized-mode nh3 profile.

    An SVG diagram has no task-list box, so `<input>` is dropped here outright rather
    than rewritten, and a `<button>` is `type="button"` as everywhere sanitized.
    """

    sanitized = nh3.clean(
        svg,
        tags=_ALLOWED_TAGS - {"input"},
        attributes=_ALLOWED_ATTRIBUTES,
        generic_attribute_prefixes=_GENERIC_ATTRIBUTE_PREFIXES,
        set_tag_attribute_values={"button": _BUTTON_SET_VALUES},
        url_schemes=_ALLOWED_URL_SCHEMES,
        link_rel=None,
    ).strip()
    # nh3 lower-cases attribute names; restore the SVG-spec camelCase only at
    # tag-attribute positions, never inside text content or quoted values. Each
    # entry maps the lowercased name to its canonical SVG form.
    return _restore_camelcase_at_attributes(sanitized)
