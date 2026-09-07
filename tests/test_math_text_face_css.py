"""Contract tests for the `KPress Math Text` composite family.

`katex/katex-text-face.css` is KPress-authored (unlike the byte-identical
vendored `katex.min.css` beside it) and defines four style/weight slots, each
built from two `@font-face` rules with disjoint `unicode-range`s: the reading
face for Latin letters (and digits, upright), and the KaTeX face scaled by
`size-adjust` for Greek. Everything else is claimed by no face, so CSS Fonts 4
moves it to the next family in the stack, which every feature rule sets to the
KaTeX face the slot replaces. An overlap would make which face draws a glyph
depend on declaration order, which is exactly what the disjoint-range design
avoids; a claimed code point outside those ranges would shadow the stack.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from devtools.katex_text_metrics import FACE_PLANS
from kpress.format.assets import read_package_text

FAMILY = '"KPress Math Text"'
MAX_CODE_POINT = 0x10FFFF

LATIN_LETTERS: tuple[tuple[int, int], ...] = ((0x41, 0x5A), (0x61, 0x7A))
LATIN_UPRIGHT: tuple[tuple[int, int], ...] = ((0x30, 0x39), *LATIN_LETTERS)
GREEK_UPRIGHT: tuple[tuple[int, int], ...] = ((0x391, 0x3A9),)
GREEK_ITALIC: tuple[tuple[int, int], ...] = ((0x370, 0x3FF),)

# slot -> (reading-face woff2, KaTeX woff2, reading ranges, scaled Greek ranges)
SLOTS: dict[
    tuple[str, str],
    tuple[str, str, tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]],
] = {
    ("normal", "400"): (
        "pt-serif-latin-400-normal.woff2",
        "KaTeX_Main-Regular.woff2",
        LATIN_UPRIGHT,
        GREEK_UPRIGHT,
    ),
    ("italic", "400"): (
        "pt-serif-latin-400-italic.woff2",
        "KaTeX_Math-Italic.woff2",
        LATIN_LETTERS,
        GREEK_ITALIC,
    ),
    ("normal", "700"): (
        "pt-serif-latin-700-normal.woff2",
        "KaTeX_Main-Bold.woff2",
        LATIN_UPRIGHT,
        GREEK_UPRIGHT,
    ),
    ("italic", "700"): (
        "pt-serif-latin-700-italic.woff2",
        "KaTeX_Math-BoldItalic.woff2",
        LATIN_LETTERS,
        GREEK_ITALIC,
    ),
}

_FONT_FACE_RE = re.compile(r"@font-face\s*\{(?P<body>[^}]*)\}")
_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_RANGE_RE = re.compile(r"U\+([0-9A-Fa-f]+)(?:-([0-9A-Fa-f]+))?")


@dataclass(frozen=True)
class FontFace:
    """One parsed `@font-face` rule: its declarations and its code-point ranges."""

    declarations: dict[str, str]
    ranges: tuple[tuple[int, int], ...]

    @property
    def slot(self) -> tuple[str, str]:
        return (self.declarations["font-style"], self.declarations["font-weight"])

    @property
    def source(self) -> str:
        return self.declarations["src"]


def _css() -> str:
    return read_package_text("katex/katex-text-face.css")


def _parse_faces(css: str) -> list[FontFace]:
    faces: list[FontFace] = []
    for match in _FONT_FACE_RE.finditer(_COMMENT_RE.sub("", css)):
        declarations: dict[str, str] = {}
        for chunk in match.group("body").split(";"):
            if ":" not in chunk:
                continue
            name, _, value = chunk.partition(":")
            declarations[name.strip()] = value.strip()
        ranges = tuple(
            (int(start, 16), int(end or start, 16))
            for start, end in _RANGE_RE.findall(declarations.get("unicode-range", ""))
        )
        faces.append(FontFace(declarations=declarations, ranges=ranges))
    return faces


def _points(ranges: tuple[tuple[int, int], ...]) -> set[int]:
    """Expand ranges to a set of code points, capped so the check stays cheap.

    Only the disputed neighbourhood matters: ASCII, Greek and Coptic, and the
    first code point past them. A face that claims everything above stays
    represented by that sentinel.
    """

    sentinel = 0x400
    points: set[int] = set()
    for start, end in ranges:
        points.update(range(start, min(end, sentinel) + 1))
    return points


def test_declares_eight_composite_faces() -> None:
    faces = _parse_faces(_css())
    assert len(faces) == 8, "four slots x (reading face, scaled Greek)"
    for face in faces:
        assert face.declarations["font-family"] == FAMILY
        # KaTeX lays out from metrics, so a late face is a clean repaint.
        assert face.declarations["font-display"] == "swap"
        assert face.ranges, "every composite face must declare a unicode-range"
    assert sorted({face.slot for face in faces}) == sorted(SLOTS)
    for slot in SLOTS:
        assert len([face for face in faces if face.slot == slot]) == 2


def test_each_slot_claims_only_latin_and_greek() -> None:
    """The composite claims letters, digits and Greek, and nothing else.

    Disjoint, so no glyph's face depends on declaration order; and bounded, so
    every other code point falls through to the KaTeX family named after the
    composite in each rule rather than being shadowed by a face here.
    """
    faces = _parse_faces(_css())
    for slot, (_reading, _katex, latin, greek) in SLOTS.items():
        seen: set[int] = set()
        for face in (face for face in faces if face.slot == slot):
            points = _points(face.ranges)
            assert not (points & seen), f"overlapping unicode-range in slot {slot}"
            seen |= points
            assert max(end for _start, end in face.ranges) < MAX_CODE_POINT, (
                f"slot {slot} claims the whole code space; the stack must supply the rest"
            )
        assert seen == _points(latin) | _points(greek), f"slot {slot} claims more than its share"


def test_reading_face_takes_the_latin_ranges() -> None:
    faces = _parse_faces(_css())
    for slot, (reading, _katex, latin, _greek) in SLOTS.items():
        matches = [face for face in faces if face.slot == slot and reading in face.source]
        assert len(matches) == 1, f"one reading face per slot: {slot}"
        assert matches[0].ranges == latin
        assert "../fonts/" in matches[0].source
        assert "size-adjust" not in matches[0].declarations


def test_greek_face_is_the_katex_face_scaled_by_the_generator_factor() -> None:
    """One source for the percentages: the generator's plans, keyed by the drawn font."""
    faces = _parse_faces(_css())
    expected = {plan.scaled_against: round(plan.scale * 100, 1) for plan in FACE_PLANS}
    for slot, (_reading, katex, _latin, greek) in SLOTS.items():
        matches = [
            face
            for face in faces
            if face.slot == slot and katex in face.source and "size-adjust" in face.declarations
        ]
        assert len(matches) == 1, f"one scaled Greek face per slot: {slot}"
        assert matches[0].ranges == greek
        assert "../katex/fonts/" in matches[0].source
        declared = float(matches[0].declarations["size-adjust"].removesuffix("%"))
        assert declared == expected[katex], (slot, declared, expected[katex])


SCOPE_EXCLUSIONS = (
    '[data-kpress-fonts="system"]',
    '[data-kpress-math-text="katex"]',
    '[data-kpress-fonts="system"] *',
    '[data-kpress-font-set="system"] *',
    '[data-kpress-math-text="katex"] *',
)


def _rule_block(css: str, tail: str) -> str:
    """The declarations of the feature rule whose selector ends with `tail`."""
    # Biome breaks a long selector across lines, so any whitespace joins the parts.
    parts = r"\s+".join(re.escape(part) for part in tail.split())
    pattern = re.compile(r"\.kpress:not\([^)]*\)\s*" + parts + r"\s*\{(?P<body>[^}]*)\}")
    match = pattern.search(css)
    assert match, tail
    return match.group("body")


def test_every_feature_rule_names_the_katex_face_after_the_composite() -> None:
    """What the composite does not claim is drawn by the next family in the stack."""
    css = _COMMENT_RE.sub("", _css())
    expected = {
        ".katex": "KaTeX_Main",
        ".katex .mathnormal": "KaTeX_Math",
        # `\mathit` is laid out from the Main-Italic table, so KaTeX_Main follows.
        ".katex .mathit": "KaTeX_Main",
        ".katex .mathbf": "KaTeX_Main",
        ".katex .boldsymbol": "KaTeX_Math",
        ".katex .mainrm": "KaTeX_Main",
    }
    for tail, family in expected.items():
        body = _rule_block(css, tail)
        assert f"font-family: {FAMILY}, {family}" in body, (tail, body)
    # Left to KaTeX: these inherit the root or keep their own families.
    for untouched in (".mathrm", ".delimsizing", ".op-symbol", ".mathbb", ".mathcal", ".mathtt"):
        assert f".katex {untouched}" not in css


def test_feature_rules_are_scoped_to_wrappers_that_have_not_opted_out() -> None:
    """Positive scoping: nothing to revert, and link order decides nothing.

    Every feature rule hangs off one `:not()` that excludes the three ways out,
    each on the wrapper or any ancestor; an opted-out wrapper keeps upstream's
    rules and style-tokens.css's size untouched.
    """
    css = _COMMENT_RE.sub("", _css())
    scopes = re.findall(r"\.kpress:not\(([^)]*)\)", css)
    assert len(scopes) >= 7, "the size token, the root and five class rules"
    for scope in scopes:
        for exclusion in SCOPE_EXCLUSIONS:
            assert exclusion in scope, (exclusion, scope)
    # No revert restates upstream's families or the 1.05em token.
    assert "1.05em" not in css
    assert re.search(r"font-family:\s*KaTeX_Main,", css) is None


def test_inline_math_takes_the_prose_size_inside_the_scope() -> None:
    css = _COMMENT_RE.sub("", _css())
    body = _rule_block(css, "")
    assert "--kpress-katex-size-prose: 1em" in body
    # The sans and display tokens are style-tokens.css's business, not this file's.
    assert "--kpress-katex-size-sans" not in css
    assert "--kpress-katex-size-display" not in css
