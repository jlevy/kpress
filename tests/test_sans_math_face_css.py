"""Contract tests for the `KPress Math Text Sans` composite family.

The sans composite is the second half of the math text face: the same four style and
weight slots, drawing the Latin ranges from Source Sans 3 instead of PT Serif, applied
inside a document's sans roles and under the reader's sans reading face.

Five things here cannot be checked anywhere else and all five are load-bearing:

- each slot pins ONE weight, because a KaTeX metric table describes one weight and
  Source Sans's advances travel along the axis (see the research brief); the tables are
  built at those same two weights, so a slot that widened its range would hand KaTeX
  numbers for glyphs it is not drawing;
- the static instances are layered over the same ranges inside `@media print` and AFTER
  the variable faces, which is what CSS Fonts 4's last-defined-face rule turns into "the
  screen keeps the variable face and the PDF embeds a font";
- the stylesheet reaches the document by the mark `katex-init.js` stamps and by nothing
  else, so which face draws and which table lays out come from ONE decision. An earlier
  shape spelled the twelve sans roles in both languages, fourteen copies in the CSS
  alone, and a role dropped from one of them drew Source Sans over PT Serif's numbers in
  that role with the whole suite green;
- every selector in the file fits the 400-character budget a consuming host's stylesheet
  check applies, measured the way that host measures it: on the prelude as it sits on
  disk, newlines and indentation intact;
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
from .test_math_text_face_css import (
    FAMILY as SERIF_FAMILY,
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

#: The reader's sans reading face: the one entry of the JS selector that is not a role.
#: It used to be a CSS scope of its own, seven more rules; the mark subsumes it, because
#: a document that is sans throughout is a document whose every math node is marked.
PROSE_FONT_SANS = '[data-kpress-prose-font="sans"]'

#: The mark `katex-init.js` stamps on a math node when the sans metric tables are what it
#: installs for that node, and the only thing the document rules select on.
MARK = '[data-kpress-math-face="sans"]'

#: Roles the review found missing, kept here so a regression names itself: `details`
#: because document.css sets the whole disclosure subtree in sans while `summary` reaches
#: the disclosure line alone, and the hydrated spelling of the tab button, which is what
#: tabs.js actually writes.
REQUIRED_ROLES = (".kpress-figcaption", ".kpress-footnotes", ".kpress-table", ".sans-text")
ADDED_ROLES = ("details", ".kpress-tab-button")

#: The third scope: a footnote preview, which tooltips.js mounts outside every `.kpress`
#: and stamps with the originating wrapper's math mode. It is the only preview kind that
#: carries rendered math, and a footnote is a sans role in every mode, so the clone it
#: carries was laid out from the sans tables and has to be drawn from the sans composite.
#: There is no `:not()` here: the overlay opts in by the stamp, which tooltips.js has
#: already resolved against the same three opt-outs.
OVERLAY_SCOPE = '.kpress-tooltip[data-kpress-math-text="prose"].kpress-tooltip-footnote'

_PRINT_BLOCK = re.compile(r"@media print\s*\{")
_JS_SANS_CONTEXT = re.compile(r"const SANS_CONTEXT =\s*(?P<value>'[^']*'|\"[^\"]*\");", re.DOTALL)
_JS_MARK_ATTR = re.compile(r'const SANS_FACE_ATTR = "(?P<key>\w+)";')
_NOT_LIST = re.compile(r":not\((?P<exclusions>[^)]*)\)")
#: Selector budget a consuming host's stylesheet check applies, and the comparison it
#: uses: `len(prelude.strip()) < 400`. Strictly less than, and measured on the prelude as
#: it sits on disk, because the host inlines the stylesheet with its newlines and
#: indentation intact. Normalizing the whitespace first, as an earlier version of this
#: test did, understates a selector by around eighty characters and reported five
#: characters of headroom where the host had seventy-eight characters of overrun.
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
    """Every rule whose declarations name the sans composite, as (selector, body).

    Keyed by the tail from `.katex` on, which is the part that says WHICH class the rule
    repoints; everything before it is the scope. Both scopes end in the same tail, so a
    class that lost one of them shows up as a short list rather than as a missing key.
    """
    found: dict[str, list[tuple[str, str]]] = {}
    for match in re.finditer(r"(?P<sel>[^{}]+)\{(?P<body>[^}]*)\}", css):
        body = match.group("body")
        # `@` skips the face declarations and the print block they sit in.
        if FAMILY not in body or "@" in match.group("sel") or "@" in body:
            continue
        selector = " ".join(match.group("sel").split())
        tail = selector[selector.index(".katex") :]
        found.setdefault(tail, []).append((selector, body))
    return found


def _preludes(css: str) -> list[str]:
    """Every top-level rule prelude, whitespace intact, the way the host reads them.

    Comments are removed first (they are not part of a prelude), and nesting is tracked
    so the four `@font-face` blocks inside `@media print` are not mistaken for rules of
    their own.
    """
    stripped = _COMMENT_RE.sub("", css)
    preludes: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(stripped):
        if char == "{":
            if depth == 0:
                preludes.append(stripped[start:index])
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                start = index + 1
    return preludes


def _js_sans_context() -> list[str]:
    """The one list of sans roles, read out of `katex-init.js`."""
    script = read_package_text("katex/katex-init.js")
    found = _JS_SANS_CONTEXT.search(script)
    assert found, "katex-init.js declares no SANS_CONTEXT"
    return [role.strip() for role in found.group("value")[1:-1].split(",")]


def test_declares_four_slots_each_with_a_reading_face_and_scaled_greek() -> None:
    screen, _print_faces = _screen_and_print()

    assert len(screen) == 8, "four slots x (Source Sans, scaled Greek)"
    assert sorted({face.slot for face in screen}) == sorted(SLOTS)
    for slot in SLOTS:
        assert len([face for face in screen if face.slot == slot]) == 2


def test_both_composites_block_on_screen_and_the_print_instances_do_not() -> None:
    """One assertion over both families, because the reason is one reason.

    `katex-init.js` waits for the faces of whichever composites the page draws from
    before it renders, so `block` decides only the case where a slot is somehow still
    not ready: hide those glyphs briefly rather than paint them in KaTeX_Main and
    repaint them in the reading face. A sans face left on `swap` while the serif ones
    blocked would flash in exactly the roles -- captions, footnotes, table cells --
    that the sans composite exists to set, and only there, which is the hardest kind
    of inconsistency to notice.

    The static instances under `@media print` keep `swap`: there is no first paint to
    protect in a printed page, and `block` blanks a whole run rather than the code
    points the face claims.
    """
    screen, printed = _screen_and_print()
    serif = _parse_faces(_COMMENT_RE.sub("", _css()), SERIF_FAMILY)

    assert len(serif) == 8, "the serif composite's four slots x two faces"
    for face in (*serif, *screen):
        assert face.declarations["font-display"] == "block", face.slot
    for face in printed:
        assert face.declarations["font-display"] == "swap", face.slot


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


def test_every_class_is_repointed_in_both_scopes() -> None:
    """One rule per class per scope: the document, by the mark, and the footnote overlay.

    Two scopes rather than the three an earlier shape had. The reader's sans reading face
    was the third, and it is gone because the mark already covers it: `SANS_CONTEXT` ends
    in the reading-face attribute, so a document that is sans throughout has every one of
    its math nodes marked and needs no scope of its own.
    """
    rules = _rules(_COMMENT_RE.sub("", _css()))

    assert sorted(rules) == sorted(SANS_RULES)
    for tail, katex_family in SANS_RULES.items():
        assert len(rules[tail]) == 2, f"{tail} needs the document scope and the overlay"
        selectors = [selector for selector, _body in rules[tail]]
        assert sum(MARK in selector for selector in selectors) == 1, tail
        assert sum(selector.startswith(OVERLAY_SCOPE) for selector in selectors) == 1, tail
        for _selector, body in rules[tail]:
            assert f"font-family: {FAMILY}, {katex_family}" in body, (tail, body)


def test_the_document_scope_lists_every_opt_out_twice() -> None:
    """The same guard the serif rules carry, and for the same reason: `closest()` reads
    each attribute on the wrapper itself as well as on an ancestor, so a scope that only
    excluded the descendant form would let the sans composite draw Source Sans over the
    Computer Modern numbers `katex-init.js` had declined to replace. Compared as a set,
    because `[data-kpress-font-set="system"]` is a substring of its own descendant form
    and a containment check passes whether or not the bare one is there.

    The mark does not make this redundant. `katex-init.js` marks a node wherever the sans
    set is what it installs, which includes a wrapper that opted out inside a page that
    did not, so the guard is what keeps the composite out of that wrapper.

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
    assert checked == len(SANS_RULES), "one document scope for each class"


def test_bold_pins_650_literally_rather_than_reading_the_public_token() -> None:
    """650 is where the `\\mathbf` table was built, so 650 is what the rule must ask for.

    `--kpress-font-weight-sans-bold` is a pinned public variable and a host may set it.
    The composite declares 400 and 650 only, and CSS Fonts 4 searches DOWNWARD for a
    desired weight in [400, 500], so a host that set the token to 500 or less got the 400
    face drawn under the 650 table: measured at 0.6153 em drawn against 0.6300 em laid
    out on `\\mathbf{D}` in a table cell, 2.3% wrong and silent. The token still decides
    what bold means for the caption's words; it may not decide which face a metric table
    describes.
    """
    rules = _rules(_COMMENT_RE.sub("", _css()))

    for tail in (".katex .mathbf", ".katex .boldsymbol"):
        for _selector, body in rules[tail]:
            assert "font-weight: 650;" in body, (tail, body)
            assert "--kpress-font-weight-sans-bold" not in body, (tail, body)
    assert SANS_BOLD_WEIGHT == 650, "the literal above and the tables' build weight"


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


def test_the_stylesheet_names_no_role_and_reaches_the_document_only_by_the_mark() -> None:
    """One list, in one language, because two copies could disagree and did.

    The stylesheet decides which face draws and the script decides which table lays out.
    While the roles were spelled in both, a divergence drew Source Sans and laid out PT
    Serif inside whichever role had drifted -- and the earlier test caught it in one of
    the seven duplicated CSS rules only, so dropping `.kpress-table` from the `.mathnormal
    ` rule left the whole suite green. There is nothing to keep in step now: the script
    stamps the mark on the nodes it installs the sans tables for, and the document rules
    select on the mark and on nothing else.

    Checked in both directions: no role name reaches the stylesheet, and both files agree
    on what the mark is called.
    """
    css = _COMMENT_RE.sub("", _css())
    script = read_package_text("katex/katex-init.js")

    for role in (*REQUIRED_ROLES, *ADDED_ROLES, PROSE_FONT_SANS):
        assert role not in css, f"{role} is spelled in the stylesheet; the script owns the list"
    assert css.count(MARK) == len(SANS_RULES), "one document rule per repointed class"

    key = _JS_MARK_ATTR.search(script)
    assert key, "katex-init.js declares no SANS_FACE_ATTR"
    # `kpressMathFace` is how a `dataset` write spells `data-kpress-math-face`.
    dashed = re.sub(r"([A-Z])", lambda m: f"-{m.group(1).lower()}", key.group("key"))
    assert f'[data-{dashed}="sans"]' == MARK, (key.group("key"), MARK)


def test_the_script_carries_every_sans_role_including_the_two_the_review_found() -> None:
    """`SANS_CONTEXT` is the list now, so this is where a missing role has to be caught.

    `details` rather than `summary`: document.css puts the whole disclosure subtree in
    sans, while a `summary` scope reaches the disclosure line alone and left math in the
    body of a `<details>` drawn from the serif composite under sans words. `<summary>` is
    a child of `<details>`, so the wider selector subsumes the narrower one and the bare
    element name is gone.

    `.kpress-tab-button` because that is what tabs.js writes on the buttons it hydrates;
    the bare `.tab-button` the list already had is the author-markup spelling, which
    components.css also treats as a sans role, so both stay.
    """
    roles = _js_sans_context()

    assert roles[-1] == PROSE_FONT_SANS, "the reading face is the last entry, and not a role"
    for role in (*REQUIRED_ROLES, *ADDED_ROLES, ".tab-button"):
        assert role in roles, role
    assert "summary" not in roles, "`details` subsumes it; two selectors would be one too many"
    assert len(roles) == len(set(roles)), roles


def test_every_selector_fits_the_consuming_hosts_budget() -> None:
    """Measured the way the host measures it, over the whole stylesheet.

    A consuming host inlines this file and asserts `len(prelude.strip()) < 400` on every
    rule, with the newlines and indentation intact. An earlier version of this test
    normalized the whitespace first and compared with `<=`, which understated the longest
    selector by 82 characters: it reported 395 against a limit of 400 where the host saw
    477 and refused to build. Measure it the host's way or the number means nothing.
    """
    over = [
        (len(prelude.strip()), " ".join(prelude.split())[:60])
        for prelude in _preludes(_css())
        if len(prelude.strip()) >= MAX_SELECTOR_CHARS
    ]

    assert not over, over


def test_headings_and_the_toc_are_left_to_the_serif_composite() -> None:
    """Both are sans roles and both are left out, for two different reasons.

    Not, as this docstring and the stylesheet used to say, because both are set at the
    sans bold weight. They are not: `h3` is 550 and `h4` is 540 in document.css, `h2` is
    the serif italic at 400, and `.kpress-toc` declares no `font-weight` at all. The
    exclusion holds anyway, because a heading sits a weight STEP away from the words
    around it whichever way the step goes, and a table built at 400 describes 540 and 550
    no better than it describes 650.

    The TOC is safe for a reason of its own that has nothing to do with weight: kpress
    escapes entry titles when it builds the TOC, so no `.katex` ever reaches it.
    """
    roles = _js_sans_context()

    for excluded in (".kpress-toc", ".kpress-toc-title", "h1", "h2", "h3", "h4"):
        assert excluded not in roles, excluded
