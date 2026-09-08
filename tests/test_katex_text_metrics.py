from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from devtools.katex_text_metrics import (
    ASSET_HEADER,
    ASSET_PATH,
    GLOBAL_NAME,
    KATEX_BUNDLE,
    KATEX_FONTS,
    LETTERS_AND_DIGITS,
    MATH_ITALIC_SCALE,
    OS2_INK_TOLERANCE,
    PRECISION,
    READING_FONTS,
    SANS_KEY,
    SANS_MATH_ITALIC_SCALE,
    SANS_SCALE_FACTORS,
    SCALE_FACTORS,
    SCALE_KEY,
    SOURCE_SANS_BOLD,
    SOURCE_SANS_REGULAR,
    MetricsError,
    check,
    parse_asset,
    parse_katex_table,
    read_face,
)

# Ground truth from the reading faces, independent of the generator: PT Serif sets its
# digits on a 0.533em advance with a 0.712em cap, and PT Serif Italic's `n` is 0.512em
# tall on a 0.552em advance with a 6/1000 overshoot below the baseline.
PT_SERIF_DIGIT_ONE = [0, 0.712, 0, 0, 0.533]
PT_SERIF_ITALIC_N = [0.006, 0.512, 0, 0, 0.552]

# The same, from Source Sans 3 at the two weights the sans slots pin. The pair is the
# point: a KaTeX table describes one weight, and `1` is 4.6% wider at 650 than at 400,
# so a single table built at one of them would misdescribe the other.
SOURCE_SANS_DIGIT_ONE = [0, 0.638, 0, 0, 0.497]
SOURCE_SANS_BOLD_DIGIT_ONE = [0, 0.636, 0, 0, 0.52]
SOURCE_SANS_ITALIC_N = [0, 0.498, 0, 0, 0.525]


@pytest.fixture(scope="module")
def asset() -> dict[str, Any]:
    return parse_asset(ASSET_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def bundle() -> str:
    return KATEX_BUNDLE.read_text(encoding="utf-8")


def _table(asset: dict[str, Any], face: str) -> dict[str, list[float]]:
    return cast("dict[str, list[float]]", asset[face])


def test_shipped_asset_is_current() -> None:
    """The asset, the scale factors and the stylesheet all agree with their inputs."""
    assert check() == []


def test_asset_declares_the_public_global(asset: dict[str, Any]) -> None:
    text = ASSET_PATH.read_text(encoding="utf-8")

    assert text.startswith(ASSET_HEADER)
    assert f"globalThis.{GLOBAL_NAME} = {{" in text
    assert set(asset) == {*SCALE_FACTORS, SANS_KEY, SCALE_KEY, "katex"}


def test_original_tables_can_restore_an_opted_out_formula(
    asset: dict[str, Any], bundle: str
) -> None:
    original = asset["katex"]
    for face in SCALE_FACTORS:
        expected = {str(code): list(row) for code, row in parse_katex_table(bundle, face).items()}
        assert original[face] == expected


def test_swapped_digit_carries_pt_serif_metrics(asset: dict[str, Any]) -> None:
    assert _table(asset, "Main-Regular")["49"] == PT_SERIF_DIGIT_ONE


def test_swapped_letter_carries_pt_serif_italic_metrics(asset: dict[str, Any]) -> None:
    assert _table(asset, "Math-Italic")["110"] == PT_SERIF_ITALIC_N


def test_unswapped_operator_is_untouched(asset: dict[str, Any], bundle: str) -> None:
    """`+` is not a letter, so KaTeX keeps drawing it and its entry must not move."""
    original = parse_katex_table(bundle, "Main-Regular")[0x2B]

    assert _table(asset, "Main-Regular")["43"] == list(original)


def test_greek_is_scaled_by_the_face_factor(asset: dict[str, Any], bundle: str) -> None:
    """Theta is drawn from KaTeX at `size-adjust`, so every value scales with it."""
    original = parse_katex_table(bundle, "Math-Italic")[0x3B8]
    expected = [round(value * MATH_ITALIC_SCALE, PRECISION) + 0.0 for value in original]

    assert _table(asset, "Math-Italic")["952"] == expected


def test_mathit_greek_is_copied_from_the_face_that_draws_it(
    asset: dict[str, Any], bundle: str
) -> None:
    """`\\mathit` is laid out from Main-Italic but drawn from KaTeX_Math-Italic.

    The composite's italic slot claims U+0370-03FF for KaTeX_Math-Italic, so the
    Greek rows in the Main-Italic table have to be that face's rows scaled, not
    Main-Italic's own. The two faces disagree: Main-Italic sets Upsilon on a
    0.76666em advance, Math-Italic on 0.58333em. Scaling the wrong one leaves
    `\\mathit{\\Upsilon}` measured a third of an em wider than it is drawn.
    """
    for table, drawn in (("Main-Italic", "Math-Italic"), ("Main-BoldItalic", "Math-BoldItalic")):
        own = parse_katex_table(bundle, table)
        scale = SCALE_FACTORS[table]
        for code_point in (0x393, 0x3A5, 0x3B8):  # Gamma, Upsilon, theta
            drawn_row = parse_katex_table(bundle, drawn)[code_point]
            expected = [round(value * scale, PRECISION) + 0.0 for value in drawn_row]

            assert _table(asset, table)[str(code_point)] == expected, (table, hex(code_point))
        # Not merely equal by coincidence: the source rows genuinely differ.
        assert own[0x3A5] != parse_katex_table(bundle, drawn)[0x3A5]


def test_mathit_greek_keeps_the_drawn_faces_accent_skew(asset: dict[str, Any]) -> None:
    """Skew is where an accent sits, so it has to come from the drawn face too.

    KaTeX centres `\\hat{}` over a glyph using the table's skew. Main-Italic
    reports 0 for its Greek capitals and Math-Italic reports a real overhang, so
    a table scaled from Main-Italic would put the accent over `\\hat{\\mathit
    {\\Gamma}}` about a tenth of an em to the left of the glyph it is drawn on.
    """
    skew_index = 3
    for table, drawn in (("Main-Italic", "Math-Italic"), ("Main-BoldItalic", "Math-BoldItalic")):
        assert _table(asset, table)["915"][skew_index] == _table(asset, drawn)["915"][skew_index]
    assert _table(asset, "Main-Italic")["915"][skew_index] > 0.09


def test_mathit_keeps_its_own_digits_and_punctuation(asset: dict[str, Any], bundle: str) -> None:
    """Only the Greek is re-sourced: the italic slot draws no digits of its own."""
    original = parse_katex_table(bundle, "Main-Italic")
    for code_point in (0x31, 0x2B, 0x2C):  # `1`, `+`, `,`
        assert _table(asset, "Main-Italic")[str(code_point)] == list(original[code_point])


def test_scale_key_matches_the_module_constants(asset: dict[str, Any]) -> None:
    assert asset[SCALE_KEY] == SCALE_FACTORS


def test_tables_are_complete(asset: dict[str, Any], bundle: str) -> None:
    """`__setFontMetrics` replaces a whole table, so no code point may be dropped."""
    for face in SCALE_FACTORS:
        original = parse_katex_table(bundle, face)

        assert {int(code) for code in _table(asset, face)} >= set(original)


def test_every_swapped_code_point_is_rewritten(asset: dict[str, Any], bundle: str) -> None:
    original = parse_katex_table(bundle, "Main-Regular")
    table = _table(asset, "Main-Regular")

    assert all(table[str(code)] != list(original[code]) for code in LETTERS_AND_DIGITS)


def test_parse_katex_table_rejects_a_missing_face() -> None:
    with pytest.raises(MetricsError, match="no metric table"):
        parse_katex_table('{"Main-Regular":{32:[0,0,0,0,.25]}}', "Math-Italic")


def test_parse_katex_table_rejects_an_unexpected_shape() -> None:
    """A KaTeX bump that reshapes the tables must fail loudly, not parse halfway."""
    with pytest.raises(MetricsError, match="shape has changed"):
        parse_katex_table('{"Main-Regular":{32:[0,0,0,0,.25],width:2}}', "Main-Regular")


def test_parse_katex_table_rejects_a_short_row() -> None:
    with pytest.raises(MetricsError, match="expected 5"):
        parse_katex_table('{"Main-Regular":{32:[0,0,0,.25]}}', "Main-Regular")


# ---- The sans set ----
#
# `KPress Math Text Sans` draws the same ranges from Source Sans 3 for the sans roles of
# a document and for the reader's sans reading face, so it needs its own tables under the
# asset's `sans` key. `katex-init.js` installs one set or the other per rendered node.


@pytest.fixture(scope="module")
def sans(asset: dict[str, Any]) -> dict[str, Any]:
    return cast("dict[str, Any]", asset[SANS_KEY])


def test_sans_set_carries_the_same_faces_and_its_own_factors(sans: dict[str, Any]) -> None:
    assert set(sans) == {*SANS_SCALE_FACTORS, SCALE_KEY}
    assert sans[SCALE_KEY] == SANS_SCALE_FACTORS
    # Below 1 for the upright slots, which the serif factors never are, because the factor
    # equalizes LATIN cap heights: KaTeX's `H` is 683 against the 656 Source Sans draws at
    # 400 and the 700 PT Serif draws. What it leaves the Greek at is not one number, since
    # Computer Modern's Greek capitals are not one height; the generator records the
    # measured spread beside the factors.
    assert SANS_SCALE_FACTORS["Main-Regular"] < 1 < SCALE_FACTORS["Main-Regular"]


def test_sans_digits_come_from_the_weight_its_slot_pins(sans: dict[str, Any]) -> None:
    """The regular table is built at 400 and the bold one at 650, which is what lets the
    composite pin each slot's `font-weight` and still describe what it draws."""
    assert _table(sans, "Main-Regular")["49"] == SOURCE_SANS_DIGIT_ONE
    assert _table(sans, "Main-Bold")["49"] == SOURCE_SANS_BOLD_DIGIT_ONE
    assert _table(sans, "Math-Italic")["110"] == SOURCE_SANS_ITALIC_N


def test_sans_and_serif_sets_disagree_where_the_faces_do(
    sans: dict[str, Any], asset: dict[str, Any]
) -> None:
    """One asset, two sets, and installing the wrong one is the failure this guards."""
    assert _table(sans, "Main-Regular")["49"] != _table(asset, "Main-Regular")["49"]


def test_sans_operators_are_untouched(sans: dict[str, Any], bundle: str) -> None:
    """Source Sans centres its operators 0.080em above KaTeX's axis and has no `<=`, so
    the composite leaves them to KaTeX and the table must say so."""
    original = parse_katex_table(bundle, "Main-Regular")[0x2B]

    assert _table(sans, "Main-Regular")["43"] == list(original)


def test_sans_greek_is_scaled_by_the_sans_factor(sans: dict[str, Any], bundle: str) -> None:
    original = parse_katex_table(bundle, "Math-Italic")[0x3B8]
    expected = [round(value * SANS_MATH_ITALIC_SCALE, PRECISION) + 0.0 for value in original]

    assert _table(sans, "Math-Italic")["952"] == expected


def test_sans_tables_are_complete(sans: dict[str, Any], bundle: str) -> None:
    """`__setFontMetrics` replaces a whole table, and the sans set replaces the serif one
    in place, so a dropped code point would survive from whichever ran last."""
    for face in SANS_SCALE_FACTORS:
        original = parse_katex_table(bundle, face)

        assert {int(code) for code in _table(sans, face)} >= set(original)


# ---- OS/2 against ink ----
#
# Every Greek factor is a ratio of two vertical measures, and `_vertical_measure` decides
# for each one whether to believe the font's OS/2 declaration or the outline it describes.
# OS2_INK_TOLERANCE is that decision, and it is the whole of it, so these read the fonts
# themselves rather than the generator's frozen literals.


def _os2_field(path: Path, field: str) -> float:
    """One OS/2 vertical field in em, read straight, with no ink cross-check."""
    font = cast(Any, TTFont(path))
    try:
        return float(cast(int, getattr(font["OS/2"], field))) / float(
            cast(int, font["head"].unitsPerEm)
        )
    finally:
        font.close()


def _ink_height(path: Path, character: str) -> float:
    """How tall one glyph is actually drawn, in em: the top of its outline bounds."""
    font = cast(Any, TTFont(path))
    try:
        glyph_set = font.getGlyphSet()
        pen = BoundsPen(glyph_set)
        glyph_set[cast("dict[int, str]", font.getBestCmap())[ord(character)]].draw(pen)
        bounds = cast("tuple[float, float, float, float]", pen.bounds)
        return bounds[3] / float(cast(int, font["head"].unitsPerEm))
    finally:
        font.close()


def _os2_ink_gap(path: Path, field: str, character: str) -> float:
    """How far one OS/2 field is from the glyph it claims to describe, in em."""
    return abs(_os2_field(path, field) - _ink_height(path, character))


@pytest.mark.parametrize(
    ("reading_font", "katex_font", "face", "drawn_cap"),
    [
        (SOURCE_SANS_REGULAR, "KaTeX_Main-Regular.woff2", "Main-Regular", 0.656),
        (SOURCE_SANS_BOLD, "KaTeX_Main-Bold.woff2", "Main-Bold", 0.653),
    ],
)
def test_the_upright_sans_factor_is_the_drawn_cap_not_the_declared_one(
    reading_font: str, katex_font: str, face: str, drawn_cap: float
) -> None:
    """Source Sans declares one cap height for its whole weight axis and draws another.

    It varies sxHeight along the axis and the drawn x-height tracks it to the unit, but
    sCapHeight stays 0.660 at every instance while the `H` shortens: 0.656 at the 400 slot
    and 0.653 at the 650 one. Scaling KaTeX's Greek to the declaration puts the bold slot
    further out than the regular one, which is the opposite of what deriving a factor per
    weight is for, so the numerator has to be the ink.

    This pins the outcome and not the constant: loosen OS2_INK_TOLERANCE past the gap and
    `read_face` hands back the declaration, and both of the last two assertions fail.
    """
    declared = _os2_field(READING_FONTS / reading_font, "sCapHeight")
    measured = read_face(READING_FONTS / reading_font).cap_height
    katex = read_face(KATEX_FONTS / katex_font).cap_height

    assert declared == pytest.approx(0.660), "the axis-invariant declaration is still there"
    assert measured == pytest.approx(drawn_cap)
    assert measured != declared, "OS2_INK_TOLERANCE is too loose to see the declared cap"
    assert SANS_SCALE_FACTORS[face] == round(measured / katex, 3)
    assert SANS_SCALE_FACTORS[face] != round(declared / katex, 3)


def test_the_scaled_upright_greek_is_laid_out_at_the_cap_source_sans_draws(
    sans: dict[str, Any], bundle: str
) -> None:
    """The end of the same chain: what the shipped table says a Greek capital's height is.

    KaTeX declares a single height for every Greek capital in an upright face, so after
    scaling there is one number per face to check, and it should be the cap height the
    reading face draws beside it rather than the one its OS/2 table claims. Compared at
    three decimals because KaTeX's own declaration is not exactly its ink `H` either:
    Main-Bold's table says 0.68611 where the outline tops out at 0.686.
    """
    height_index = 1
    for face, drawn_cap in (("Main-Regular", 0.656), ("Main-Bold", 0.653)):
        table = _table(sans, face)
        greek = [code for code in parse_katex_table(bundle, face) if 0x391 <= code <= 0x3A9]
        heights = {round(table[str(code)][height_index], 3) for code in greek}

        assert len(greek) == 11, face
        assert heights == {drawn_cap}, face


def test_the_ink_tolerance_sits_between_rounding_and_a_real_disagreement() -> None:
    """The tolerance is a band and both of its edges carry weight.

    Under it sits KaTeX_Math-Italic, whose sxHeight is 441 against a 442 ink `x`. One unit
    at 1000 upem is the font build's own rounding, and preferring the ink there would move
    the serif composite's Math-Italic slot from 115.0% to 114.7% and rewrite four shipped
    tables for no change in what any glyph is drawn at.

    Over it sit the two Source Sans cap heights, wrong by 4 units at 400 and 7 at 650, and
    KaTeX_Math-BoldItalic's sxHeight, wrong by 80 -- the case this fallback was written
    for. A tolerance outside the band is either the defect the caps are or a needless
    churn of the serif set, so pin both edges against the fonts rather than the number.
    """
    rounding = _os2_ink_gap(KATEX_FONTS / "KaTeX_Math-Italic.woff2", "sxHeight", "x")
    cap_400 = _os2_ink_gap(READING_FONTS / SOURCE_SANS_REGULAR, "sCapHeight", "H")
    cap_650 = _os2_ink_gap(READING_FONTS / SOURCE_SANS_BOLD, "sCapHeight", "H")
    declared_lie = _os2_ink_gap(KATEX_FONTS / "KaTeX_Math-BoldItalic.woff2", "sxHeight", "x")

    assert (rounding, cap_400, cap_650, declared_lie) == pytest.approx((0.001, 0.004, 0.007, 0.080))
    assert rounding < OS2_INK_TOLERANCE < cap_400 < cap_650 < declared_lie
