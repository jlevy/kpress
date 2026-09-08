"""Contract tests for the `KPress Math Text Sans` composite family.

The sans composite is the second half of the math text face: the same four style and
weight slots, drawing the Latin ranges from Source Sans 3 instead of PT Serif, applied
inside a document's sans roles and under the reader's sans reading face.

Four things here cannot be checked anywhere else and all four are load-bearing:

- each slot pins ONE weight, because a KaTeX metric table describes one weight and
  Source Sans's advances travel along the axis (see the research brief); the tables are
  built at those same two weights, so a slot that widened its range would hand KaTeX
  numbers for glyphs it is not drawing;
- the static instances are layered over the same ranges inside `@media print` and AFTER
  the variable faces, which is what CSS Fonts 4's last-defined-face rule turns into "the
  screen keeps the variable face and the PDF embeds a font";
- the role list the rules are scoped on is spelled a second time in `katex-init.js`,
  which picks the matching metric table set per node, and the two copies must agree or
  a caption is drawn in one face and laid out from the other;
- the footnote preview overlay takes the sans composite. It is the one place the two
  engines are decoupled -- the overlay carries a CLONE and nothing re-renders in it --
  so the cascade alone has to keep the drawn face and the metrics it was laid out from
  together.
"""

from __future__ import annotations

import re

from devtools.katex_text_metrics import (
    SANS_BOLD_WEIGHT,
    SANS_FACE_PLANS,
    SANS_REGULAR_WEIGHT,
    sans_font,
)
from kpress.format.assets import read_package_text

from .test_math_text_face_css import (
    _COMMENT_RE,  # pyright: ignore[reportPrivateUsage]
    GREEK_ITALIC,
    GREEK_UPRIGHT,
    LATIN_LETTERS,
    LATIN_UPRIGHT,
    SCOPE_EXCLUSIONS,
    FontFace,
    _parse_faces,  # pyright: ignore[reportPrivateUsage]
)

FAMILY = '"KPress Math Text Sans"'
VARIABLE_FACE = "source-sans-3-latin-wght-{style}.woff2"

#: slot -> (KaTeX woff2 whose Greek it scales, reading ranges, scaled Greek ranges)
SLOTS: dict[
    tuple[str, str], tuple[str, tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]
] = {
    ("normal", str(SANS_REGULAR_WEIGHT)): (
        "KaTeX_Main-Regular.woff2",
        LATIN_UPRIGHT,
        GREEK_UPRIGHT,
    ),
    ("italic", str(SANS_REGULAR_WEIGHT)): ("KaTeX_Math-Italic.woff2", LATIN_LETTERS, GREEK_ITALIC),
    ("normal", str(SANS_BOLD_WEIGHT)): ("KaTeX_Main-Bold.woff2", LATIN_UPRIGHT, GREEK_UPRIGHT),
    ("italic", str(SANS_BOLD_WEIGHT)): (
        "KaTeX_Math-BoldItalic.woff2",
        LATIN_LETTERS,
        GREEK_ITALIC,
    ),
}

#: The classes the sans rules re-point, and the KaTeX family each names after the
#: composite so the code points the composite does not claim keep their own face.
SANS_RULES = {
    ".katex": "KaTeX_Main",
    ".katex .mathnormal": "KaTeX_Math",
    ".katex .mathit": "KaTeX_Main",
    ".katex .mathbf": "KaTeX_Main",
    ".katex .boldsymbol": "KaTeX_Math",
    ".katex .textrm": "KaTeX_Main",
    ".katex .mainrm": "KaTeX_Main",
}

#: The reader's sans reading face, which is a scope of its own and the one entry of the
#: JS selector that is not a role.
PROSE_FONT_SANS = '[data-kpress-prose-font="sans"]'

#: The third scope: a footnote preview, which tooltips.js mounts outside every `.kpress`
#: and stamps with the originating wrapper's math mode. It is the only preview kind that
#: carries rendered math, and a footnote is a sans role in every mode, so the clone it
#: carries was laid out from the sans tables and has to be drawn from the sans composite.
#: There is no `:not()` here: the overlay opts in by the stamp, which tooltips.js has
#: already resolved against the same three opt-outs.
OVERLAY_SCOPE = '.kpress-tooltip[data-kpress-math-text="prose"].kpress-tooltip-footnote'

_PRINT_BLOCK = re.compile(r"@media print\s*\{")
_ROLE_LIST = re.compile(r"\)\s*:is\((?P<roles>[^)]*)\)\s*\.katex")
_JS_SANS_CONTEXT = re.compile(r"const SANS_CONTEXT =\s*(?P<value>'[^']*'|\"[^\"]*\");", re.DOTALL)
_NOT_LIST = re.compile(r":not\((?P<exclusions>[^)]*)\)")
#: Selector budget a consuming host's stylesheet check applies; the CSS comment quotes it.
MAX_SELECTOR_CHARS = 400


def _css() -> str:
    return read_package_text("katex/katex-text-face.css")


def _sans_faces() -> list[FontFace]:
    return _parse_faces(_css(), FAMILY)


def _screen_and_print() -> tuple[list[FontFace], list[FontFace]]:
    """The composite's faces, split at the `@media print` block that layers over them."""
    css = _COMMENT_RE.sub("", _css())
    start = _PRINT_BLOCK.search(css)
    assert start, "the composite declares no print instances"
    return _parse_faces(css[: start.start()], FAMILY), _parse_faces(css[start.start() :], FAMILY)


def _rules(css: str) -> dict[str, list[tuple[str, str]]]:
    """Every rule whose declarations name the sans composite, as (selector, body)."""
    found: dict[str, list[tuple[str, str]]] = {}
    for match in re.finditer(r"(?P<sel>[^{}]+)\{(?P<body>[^}]*)\}", css):
        body = match.group("body")
        # `@` skips the face declarations and the print block they sit in.
        if FAMILY not in body or "@" in match.group("sel") or "@" in body:
            continue
        selector = " ".join(match.group("sel").split())
        # Two scopes end in `)`; the overlay's is a plain compound, so strip it by name.
        tail = selector.split(")")[-1].strip().removeprefix(OVERLAY_SCOPE).strip()
        found.setdefault(tail, []).append((selector, body))
    return found


def test_declares_four_slots_each_with_a_reading_face_and_scaled_greek() -> None:
    screen, _print_faces = _screen_and_print()

    assert len(screen) == 8, "four slots x (Source Sans, scaled Greek)"
    assert sorted({face.slot for face in screen}) == sorted(SLOTS)
    for slot in SLOTS:
        assert len([face for face in screen if face.slot == slot]) == 2
    for face in screen:
        assert face.declarations["font-display"] == "swap"


def test_each_slot_pins_one_weight_and_the_generator_builds_its_table_there() -> None:
    """A metric table describes one weight, so the descriptor may not be a range.

    CSS Fonts 4 clamps a variable face to the range its `@font-face` declares, so a
    single value draws the weight the table was built at whatever the context asks for.
    """
    weights = {weight for _style, weight in SLOTS}

    assert weights == {str(SANS_REGULAR_WEIGHT), str(SANS_BOLD_WEIGHT)}
    for face in _sans_faces():
        assert face.declarations["font-weight"].isdigit(), (
            f"{face.slot} declares a weight range; the table describes one weight"
        )
    built_at = {plan.reading_font for plan in SANS_FACE_PLANS}
    assert built_at == {
        sans_font(weight, style)
        for weight in (SANS_REGULAR_WEIGHT, SANS_BOLD_WEIGHT)
        for style in ("normal", "italic")
    }


def test_the_screen_draws_the_latin_ranges_from_the_variable_faces() -> None:
    screen, _print_faces = _screen_and_print()

    for (style, _weight), (_katex, latin, _greek) in SLOTS.items():
        matches = [
            face
            for face in screen
            if face.slot[0] == style and VARIABLE_FACE.format(style=style) in face.source
        ]
        assert len(matches) == 2, f"one variable face per weight in the {style} slots"
        for face in matches:
            assert face.ranges == latin
            assert "../fonts/" in face.source
            assert "size-adjust" not in face.declarations


def test_print_layers_the_static_instances_over_the_same_ranges() -> None:
    """Chromium cannot embed a variable face away from its default, so print needs a
    static instance; declared last, so the last-defined-face rule hands it to print."""
    _screen, printed = _screen_and_print()

    assert len(printed) == 4, "one static instance per slot, upright and italic"
    for face in printed:
        style, weight = face.slot
        assert sans_font(int(weight), style) in face.source, face.source
        assert "size-adjust" not in face.declarations
        latin = SLOTS[face.slot][1]
        assert face.ranges == latin
    assert sorted({face.slot for face in printed}) == sorted(SLOTS)


def test_greek_is_scaled_by_the_generator_factor_for_the_sans() -> None:
    screen, _print_faces = _screen_and_print()
    expected = {plan.scaled_against: round(plan.scale * 100, 1) for plan in SANS_FACE_PLANS}

    for slot, (katex, _latin, greek) in SLOTS.items():
        matches = [
            face
            for face in screen
            if face.slot == slot and katex in face.source and "size-adjust" in face.declarations
        ]
        assert len(matches) == 1, f"one scaled Greek face per slot: {slot}"
        assert matches[0].ranges == greek
        assert "../katex/fonts/" in matches[0].source
        declared = float(matches[0].declarations["size-adjust"].removesuffix("%"))
        assert declared == expected[katex], (slot, declared, expected[katex])
    # Below 100% for the upright slots: Computer Modern's Greek capitals are taller than
    # Source Sans's, where they were shorter than PT Serif's.
    assert expected["KaTeX_Main-Regular.woff2"] < 100
    assert expected["KaTeX_Math-Italic.woff2"] > 100


def test_every_class_is_repointed_in_all_three_scopes() -> None:
    """One rule per class per scope: the document's sans roles, the sans reading face,
    and the footnote preview overlay. Separate rules rather than one selector list, so
    each selector stays short."""
    rules = _rules(_COMMENT_RE.sub("", _css()))

    assert sorted(rules) == sorted(SANS_RULES)
    for tail, katex_family in SANS_RULES.items():
        assert len(rules[tail]) == 3, f"{tail} needs the roles, the reading face, the overlay"
        selectors = [selector for selector, _body in rules[tail]]
        assert any(
            ":is(" in selector and ".kpress-figcaption" in selector for selector in selectors
        ), tail
        assert any(PROSE_FONT_SANS in selector for selector in selectors), tail
        assert sum(selector.startswith(OVERLAY_SCOPE) for selector in selectors) == 1, tail
        for selector, body in rules[tail]:
            assert f"font-family: {FAMILY}, {katex_family}" in body, (tail, body)
            assert len(selector) <= MAX_SELECTOR_CHARS, (tail, len(selector))


def test_the_two_document_scopes_list_every_opt_out_twice() -> None:
    """The same guard the serif rules carry, and for the same reason: `closest()` reads
    each attribute on the wrapper itself as well as on an ancestor, so a scope that only
    excluded the descendant form would let the sans composite draw Source Sans over the
    Computer Modern numbers `katex-init.js` had declined to replace. Compared as a set,
    because `[data-kpress-font-set="system"]` is a substring of its own descendant form
    and a containment check passes whether or not the bare one is there.

    The overlay scope is exempt and carries no `:not()`: it is stamped by tooltips.js,
    which resolves the same three opt-outs before it writes the attribute.
    """
    rules = _rules(_COMMENT_RE.sub("", _css()))

    checked = 0
    for tail in SANS_RULES:
        for selector, _body in rules[tail]:
            if selector.startswith(OVERLAY_SCOPE):
                assert ":not(" not in selector, tail
                continue
            found = _NOT_LIST.search(selector)
            assert found, (tail, selector)
            listed = {part.strip() for part in found.group("exclusions").split(",")}
            assert listed == SCOPE_EXCLUSIONS, (tail, listed)
            checked += 1
    assert checked == len(SANS_RULES) * 2, "two document scopes for each class"


def test_bold_asks_for_the_sans_bold_token_not_upstreams_700() -> None:
    """`\\mathbf` in a caption reaches the same bold as a bold word in the caption."""
    rules = _rules(_COMMENT_RE.sub("", _css()))

    for tail in (".katex .mathbf", ".katex .boldsymbol"):
        for _selector, body in rules[tail]:
            assert "font-weight: var(--kpress-font-weight-sans-bold, 650)" in body, (tail, body)
    assert SANS_BOLD_WEIGHT == 650, "the fallback above and the tables' build weight"


def test_textrm_takes_the_family_only_here_too() -> None:
    """`\\textrm{\\textit{x}}` is one `.mord.textrm.textit` leaf. These rules land at
    (0,5,0), so a `font-style: normal` would outrank upstream's `.textit` at (0,2,0) and
    draw the upright slot over a run KaTeX laid out from the italic table -- the reason
    the serif rule drops the pin, and truer here, one class further up. `.mainrm` keeps
    it, because upstream pins it too."""
    rules = _rules(_COMMENT_RE.sub("", _css()))

    for _selector, body in rules[".katex .textrm"]:
        assert "font-style" not in body, body
    for _selector, body in rules[".katex .mainrm"]:
        assert "font-style: normal" in body, body


def test_the_role_list_matches_the_one_katex_init_selects_tables_with() -> None:
    """The stylesheet decides which face draws; the script decides which table lays out.
    They are two languages and one list, so a divergence would draw Source Sans and lay
    out PT Serif inside every role that had drifted."""
    css_roles = _ROLE_LIST.search(_COMMENT_RE.sub("", _css()))
    assert css_roles, "the sans rules declare no role list"
    from_css = {role.strip() for role in css_roles.group("roles").split(",")}

    script = read_package_text("katex/katex-init.js")
    js = _JS_SANS_CONTEXT.search(script)
    assert js, "katex-init.js declares no SANS_CONTEXT"
    from_js = {role.strip() for role in js.group("value")[1:-1].split(",")}

    assert from_js == from_css | {PROSE_FONT_SANS}


def test_headings_and_the_toc_are_left_to_the_serif_composite() -> None:
    """Both are sans roles set at the sans bold weight, where the pinned 400 would draw
    the mathematics a step lighter than the words; recorded in the research brief."""
    css_roles = _ROLE_LIST.search(_COMMENT_RE.sub("", _css()))
    assert css_roles
    roles = css_roles.group("roles")

    for excluded in (".kpress-toc", ".kpress-toc-title", "h1", "h2", "h3"):
        assert excluded not in roles, excluded
