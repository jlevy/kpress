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


def test_greek_face_is_the_katex_face_scaled() -> None:
    faces = _parse_faces(_css())
    for slot, (_reading, katex, _latin, greek) in SLOTS.items():
        matches = [
            face
            for face in faces
            if face.slot == slot and katex in face.source and "size-adjust" in face.declarations
        ]
        assert len(matches) == 1, f"one scaled Greek face per slot: {slot}"
        assert matches[0].ranges == greek
        # Provisional until `katex_text_metrics --print-scale` lands; that tool's
        # --check pins the exact value, so only the shape is asserted here.
        scale = matches[0].declarations["size-adjust"]
        assert scale.endswith("%")
        assert 100.0 <= float(scale.removesuffix("%")) <= 130.0


def test_every_feature_rule_names_the_katex_face_after_the_composite() -> None:
    """What the composite does not claim is drawn by the next family in the stack."""
    css = _COMMENT_RE.sub("", _css())
    expected = {
        ".kpress .katex {": "KaTeX_Main",
        ".kpress .katex .mathit {": "KaTeX_Math",
        ".kpress .katex .mathbf {": "KaTeX_Main",
        ".kpress .katex .boldsymbol {": "KaTeX_Math",
        ".kpress .katex .mainrm {": "KaTeX_Main",
    }
    for selector, family in expected.items():
        assert selector in css, selector
        block = css.split(selector, 1)[1].split("}", 1)[0]
        assert f"font-family: {FAMILY}, {family}" in block, (selector, block)


def test_feature_rules_point_the_katex_classes_at_the_composite() -> None:
    css = _css()
    assert '.kpress .katex {\n  font-family: "KPress Math Text", KaTeX_Main' in css
    for selector in (
        ".kpress .katex .mathnormal",
        ".kpress .katex .mathit",
        ".kpress .katex .mathbf",
        ".kpress .katex .boldsymbol",
        ".kpress .katex .textrm",
        ".kpress .katex .mainrm",
    ):
        assert f"{selector},\n" in css or f"{selector} {{" in css
    # Left to KaTeX: these inherit the root or keep their own families.
    for untouched in (".mathrm", ".delimsizing", ".op-symbol", ".mathbb", ".mathcal", ".mathtt"):
        assert f".kpress .katex {untouched}" not in css


def test_opt_out_and_system_reverts_exist() -> None:
    css = _css()
    assert '[data-kpress-math-text="katex"] .kpress .katex' in css
    assert '.kpress[data-kpress-fonts="system"] .katex' in css
    for selector in (
        '[data-kpress-math-text="katex"] .kpress .katex .mathnormal',
        '[data-kpress-math-text="katex"] .kpress .katex .mathbf',
        '[data-kpress-math-text="katex"] .kpress .katex .boldsymbol',
        '.kpress[data-kpress-fonts="system"] .katex .mathnormal',
    ):
        assert selector in css
    # The reverts name the KaTeX families again, never the composite.
    for block in css.split('[data-kpress-math-text="katex"]')[1:]:
        assert FAMILY not in block.split("}", 1)[0]


def test_inline_math_takes_the_prose_size_and_reverts() -> None:
    css = _css()
    assert ".kpress {\n  --kpress-katex-size-prose: 1em;\n}" in css
    assert "--kpress-katex-size-prose: 1.05em;" in css
    # The sans and display tokens are style-tokens.css's business, not this file's.
    assert "--kpress-katex-size-sans" not in css
    assert "--kpress-katex-size-display" not in css
