"""A heading inside a sans block is set in the same face as the mathematics inside it.

The sans math composite is scoped by CONTAINER: `katex-init.js` resolves `SANS_CONTEXT`
with `closest()` from each node it renders, so a `.katex` anywhere inside `.sans-text`,
`.description`, `.key-claims`, `.summary`, `.concepts` or `.claim` is laid out from the
sans metric tables and stamped for the sans rules in `katex/katex-text-face.css` to draw
from `KPress Math Text Sans`. Headings are deliberately not roles of their own there --
a heading's sans weight is not the weight the pinned tables were built at -- but
`closest()` climbs straight past the heading to the block, so a heading INSIDE one of
those blocks gets sans mathematics whether or not its own letters are sans.

That is the whole hazard this file exists for, and it is one the cascade reaches
quietly. `document.css` re-declares the prose face directly on `h1`, `h2`, `h5` and `h6`
(`.kpress-prose h1` and its siblings), and a declaration on the heading itself beats the
sans family a container sets on an ancestor, which reaches the heading only by
inheritance. Before this test existed, an `h2` inside `:::description` therefore drew PT
Serif words wrapped around a Source Sans formula -- Chromium-verified -- which is the
exact disagreement the sans composite was built to remove. `.sans-text` had escaped the
`h1`/`h2` half of it by re-declaring those two, and had NOT escaped the `h5`/`h6` half.

So the invariant here is not "some rule exists". It is the cascade's own answer: for
every block and every heading level, resolve `font-family` the way a browser does --
every rule in the two stylesheets that reaches that heading, ranked by specificity and
then by source order -- and require the winner to be the sans face, declared by a rule
that names the block. The second half matters as much as the first: it keeps the
agreement anchored to the block rather than resting on `.kpress-prose h1..h6` happening
to stay sans for the levels that do not re-declare.

The other sans-math roles -- captions, footnotes, tables, tab buttons, `details` -- are
not covered: none of them is a container kpress renders author headings into, and giving
their headings a face is a design question rather than a cascade accident.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from kpress.format.assets import read_package_text

from .test_math_text_face_css import (
    _COMMENT_RE,  # pyright: ignore[reportPrivateUsage]
)

#: The sans blocks that can carry an author heading, as the class the container wears.
#: Every one of them is in the sans role list of `katex/katex-text-face.css`, which is
#: what puts sans mathematics inside them and makes their heading's face load-bearing.
SANS_BLOCKS = (
    ".sans-text",
    ".description",
    ".key-claims",
    ".summary",
    ".concepts",
    ".claim",
)

HEADINGS = ("h1", "h2", "h3", "h4", "h5", "h6")

#: The two stylesheets that set a heading's face, in the order `page.html.jinja` links
#: them. Order is part of the answer: two rules of equal specificity are decided by it,
#: which is how a components.css rule can tie a rule here and still win.
STYLESHEETS = ("css/document.css", "css/components.css")

#: The reading face and the sans face, as the tokens the stylesheets name them by.
PROSE_FACE = "--kpress-font-prose"
SANS_FACE = "--kpress-font-sans"

#: Combinators the probe below does not model. A heading rule that used one would be
#: silently skipped rather than wrongly matched, so the collector refuses instead.
COMBINATORS = ("+", "~", ">")

#: The one place the sans role list lives, now that the stylesheet keys on the mark
#: `katex-init.js` stamps rather than spelling the roles a second time.
_SANS_CONTEXT = re.compile(r"const SANS_CONTEXT =\s*(?P<value>'[^']*'|\"[^\"]*\");", re.DOTALL)

_FUNCTIONAL = re.compile(r":(is|not|where|has)\(")
#: One simple selector: id, class, attribute, pseudo-element, pseudo-class, type, `*`.
#: Ordered so the longer forms win the alternation -- `::before` before `:before`.
_SIMPLE = re.compile(r"#[\w-]+|\.[\w-]+|\[[^\]]*\]|::[\w-]+|:[\w-]+|[\w-]+|\*")
_DECLARATION = re.compile(r"(?P<name>[\w-]+)\s*:\s*(?P<value>[^;]*)")


@dataclass(frozen=True)
class Element:
    """One node of the probe tree: the tag it is and the classes it carries.

    Deliberately attribute-free. Nothing in these two stylesheets sets a heading's
    family behind an attribute, and an attribute selector therefore reads as "does not
    match this probe", which is the truthful answer for the document shape below.
    """

    tag: str
    classes: frozenset[str]


@dataclass(frozen=True)
class Rule:
    """One style rule of one stylesheet: a single selector and its declarations."""

    selector: str
    body: str
    stylesheet: str
    order: int

    @property
    def font_family(self) -> str | None:
        values = [
            found.group("value").strip()
            for found in _DECLARATION.finditer(self.body)
            if found.group("name").strip() == "font-family"
        ]
        return values[-1] if values else None


def _arguments(text: str, opening: int) -> tuple[str, int]:
    """The text inside the parentheses that open at `opening`, and the index past them."""
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return text[opening + 1 : index], index + 1
    raise AssertionError(f"unbalanced parentheses in {text!r}")


def _split_top(text: str, on: str) -> list[str]:
    """Split on a top-level delimiter, ignoring anything nested inside `(...)`.

    `on` is either a literal character or `" "`, which splits on any whitespace run and
    so turns a complex selector into its compound selectors.
    """
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        splits = char.isspace() if on == " " else char == on
        if depth == 0 and splits:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    parts.append("".join(current))
    return [part for part in (raw.strip() for raw in parts) if part]


def _style_rules(css: str, stylesheet: str, start: int) -> list[Rule]:
    """Every style rule of a stylesheet, one per selector of a selector list.

    At-rule blocks (`@media`, `@supports`) are descended into rather than skipped, so a
    heading rule hidden inside a media query is still ranked; the at-rule prelude itself
    is not a selector and contributes nothing. These stylesheets use no CSS nesting, so
    a style rule's block is declarations only.
    """
    css = _COMMENT_RE.sub("", css)
    rules: list[Rule] = []
    index = 0
    prelude: list[str] = []
    while index < len(css):
        char = css[index]
        if char == "{":
            head = " ".join("".join(prelude).split())
            prelude = []
            if head.startswith("@"):
                index += 1
                continue
            body, after = _block(css, index)
            for selector in _split_top(head, ","):
                rules.append(
                    Rule(
                        selector=selector,
                        body=body,
                        stylesheet=stylesheet,
                        order=start + len(rules),
                    )
                )
            index = after
            continue
        if char == "}":
            prelude = []
            index += 1
            continue
        prelude.append(char)
        index += 1
    return rules


def _block(css: str, opening: int) -> tuple[str, int]:
    """The declarations of the block opening at `opening`, and the index past its close."""
    depth = 0
    for index in range(opening, len(css)):
        if css[index] == "{":
            depth += 1
        elif css[index] == "}":
            depth -= 1
            if depth == 0:
                return css[opening + 1 : index], index + 1
    raise AssertionError("unterminated block")


def _specificity(selector: str) -> tuple[int, int, int]:
    """Selectors 4 specificity, the part of it these stylesheets use.

    `:is()` and `:not()` take the specificity of their most specific argument, `:where()`
    contributes nothing, and everything else is the ordinary count of ids, of
    classes/attributes/pseudo-classes, and of types/pseudo-elements.
    """
    ids = classes = types = 0
    rest = selector
    while (found := _FUNCTIONAL.search(rest)) is not None:
        args, after = _arguments(rest, found.end() - 1)
        inner = (
            (0, 0, 0)
            if found.group(1) == "where"
            else max((_specificity(part) for part in _split_top(args, ",")), default=(0, 0, 0))
        )
        ids, classes, types = ids + inner[0], classes + inner[1], types + inner[2]
        rest = f"{rest[: found.start()]} {rest[after:]}"
    for token in _SIMPLE.findall(rest):
        if token.startswith("#"):
            ids += 1
        elif token.startswith("::"):
            types += 1
        elif token[0] in ".[:":
            classes += 1
        elif token != "*":
            types += 1
    return (ids, classes, types)


def _compound_matches(compound: str, element: Element) -> bool:
    """Whether one compound selector matches one probe element."""
    rest = compound
    while (found := _FUNCTIONAL.search(rest)) is not None:
        name = found.group(1)
        args, after = _arguments(rest, found.end() - 1)
        assert name in {"is", "not", "where"}, f"unmodelled `:{name}()` in {compound!r}"
        matched = any(_compound_matches(part, element) for part in _split_top(args, ","))
        if name == "not":
            matched = not matched
        if not matched:
            return False
        rest = f"{rest[: found.start()]}{rest[after:]}"
    for token in _SIMPLE.findall(rest):
        if token.startswith("."):
            if token[1:] not in element.classes:
                return False
        elif token.startswith("[") or token.startswith(":"):
            # The probe carries no attributes and is in no state.
            return False
        elif token not in {"*", element.tag}:
            return False
    return True


def _matches(selector: str, ancestors: tuple[Element, ...], subject: Element) -> bool:
    """Whether a descendant-only selector matches `subject` under `ancestors`.

    The ancestor compounds have to appear in order, which is what a chain of descendant
    combinators means; `_heading_face_rules` refuses any other combinator, so a selector
    that reaches this point is a plain chain.
    """
    compounds = _split_top(selector, " ")
    if not _compound_matches(compounds[-1], subject):
        return False
    depth = 0
    for compound in compounds[:-1]:
        while depth < len(ancestors) and not _compound_matches(compound, ancestors[depth]):
            depth += 1
        if depth == len(ancestors):
            return False
        depth += 1
    return True


def _ancestors(block: str) -> tuple[Element, ...]:
    """The chain kpress renders a semantic block's heading under.

    Read off `tests/golden/accepted/semantic-components/page.html`: the article wrapper,
    the layout, the prose column, then the block. `.claim` is nested one deeper again
    inside `.key-claims` in that golden; the shallower chain here is the harder case,
    since fewer ancestors can only mean fewer rules reach the heading.
    """
    return (
        Element("article", frozenset({"kpress", "kpress-doc", "kpress-print-surface"})),
        Element("div", frozenset({"kpress-doc-layout", "kpress-content-with-toc"})),
        Element("div", frozenset({"kpress-prose", "kpress-long-text"})),
        Element("div", frozenset({block.removeprefix(".")})),
    )


def _heading_face_rules() -> list[Rule]:
    """Every rule of the two stylesheets that declares a `font-family` on a heading.

    A rule that sets a heading's family through a combinator this probe cannot model
    would be dropped from the ranking and could hand the cascade back to the prose face
    unnoticed, so it fails the collection instead of being skipped.
    """
    rules: list[Rule] = []
    for stylesheet in STYLESHEETS:
        rules.extend(_style_rules(read_package_text(stylesheet), stylesheet, len(rules)))
    heading_probes = [Element(heading, frozenset()) for heading in HEADINGS]
    selected: list[Rule] = []
    for rule in rules:
        if rule.font_family is None:
            continue
        subject = _split_top(rule.selector, " ")[-1]
        if not any(_compound_matches(subject, probe) for probe in heading_probes):
            continue
        assert not any(mark in rule.selector for mark in COMBINATORS), (
            f"{rule.stylesheet} sets a heading face through an unmodelled combinator: "
            f"{rule.selector}"
        )
        selected.append(rule)
    assert selected, "no rule in either stylesheet sets a heading's face"
    return selected


def _winner(block: str, heading: str, rules: list[Rule]) -> Rule:
    """The rule whose `font-family` a heading in `block` actually gets."""
    ancestors = _ancestors(block)
    subject = Element(heading, frozenset())
    reaching = [rule for rule in rules if _matches(rule.selector, ancestors, subject)]
    assert reaching, f"nothing sets a face on {heading} inside {block}"
    return max(reaching, key=lambda rule: (_specificity(rule.selector), rule.order))


def test_every_heading_in_a_sans_block_resolves_to_the_sans_face() -> None:
    """The cascade's own answer, for all six blocks at all six levels.

    This is the assertion that fails on the shipped bug: with no heading rule of their
    own, `h1`, `h2`, `h5` and `h6` inside these blocks were won by `.kpress-prose h1`
    and its siblings at (0,1,1), which name the prose face -- serif words around sans
    mathematics. It fails for `.sans-text` too, whose own `h1`/`h2` rules stopped short
    of `h5` and `h6`.
    """
    rules = _heading_face_rules()

    for block in SANS_BLOCKS:
        for heading in HEADINGS:
            winner = _winner(block, heading, rules)
            family = winner.font_family
            assert family is not None
            assert SANS_FACE in family, (block, heading, winner.selector, family)
            assert PROSE_FACE not in family, (block, heading, winner.selector, family)


def test_the_winning_rule_names_the_block_it_wins_inside() -> None:
    """The agreement is anchored to the block, not borrowed from a general rule.

    `.kpress-prose h1..h6` sets the sans family too, so `h3` and `h4` would pass the
    test above on that rule alone -- and would start failing the day it changed, for a
    reason no one editing it would connect to mathematics. Requiring the winner to name
    the block keeps the two facts in one place: the block's mathematics is sans because
    the block is a sans math role, and the block's headings are sans for the same
    reason and by a rule that says so.
    """
    rules = _heading_face_rules()

    for block in SANS_BLOCKS:
        for heading in HEADINGS:
            winner = _winner(block, heading, rules)
            assert block in winner.selector, (block, heading, winner.selector)
            assert winner.stylesheet == "css/components.css", (block, heading, winner.stylesheet)


def test_no_rule_scoped_to_a_sans_block_puts_a_heading_back_on_the_prose_face() -> None:
    """The direct form of the same rule, stated where a future edit would break it.

    The cascade test above catches a prose face that WINS. This catches one that is
    merely declared -- a block-scoped heading rule reaching for the reading face, which
    is a decision to disagree with the mathematics whether or not it currently outranks
    anything.
    """
    for rule in _heading_face_rules():
        if not any(block in rule.selector for block in SANS_BLOCKS):
            continue
        family = rule.font_family
        assert family is not None
        assert PROSE_FACE not in family, (rule.stylesheet, rule.selector, family)


def test_the_blocks_here_are_the_sans_math_roles_they_claim_to_be() -> None:
    """Six names, spelled the same way in both places, or the pin above points nowhere.

    A heading's face only has to agree with anything because the mathematics inside
    these blocks is drawn from the sans composite: `katex-init.js` resolves `SANS_CONTEXT`
    with `closest()` from each rendered node, which reaches a `.katex` inside a heading
    exactly as it reaches one in a paragraph, and stamps the node so the sans rules in
    `katex-text-face.css` draw it. If a block leaves that list -- renamed, dropped --
    the heading rule in components.css is stale; if a new role that carries author
    headings joins it, `SANS_BLOCKS` is what has to grow with it.

    Only the containment is asserted, not the exact complement: the role list is meant
    to gain entries, and the ones it carries beyond these six (`.kpress-figcaption`,
    `.kpress-footnotes`, `.kpress-table`, `.para-caption`, the tab buttons, `details`,
    and the reader's own sans reading face) are not containers kpress renders author
    headings into.
    """
    script = read_package_text("katex/katex-init.js")
    declared = _SANS_CONTEXT.search(script)
    assert declared, "katex-init.js declares no SANS_CONTEXT"
    listed = {role.strip() for role in declared.group("value")[1:-1].split(",")}

    assert set(SANS_BLOCKS) <= listed, set(SANS_BLOCKS) - listed
