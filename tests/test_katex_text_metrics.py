from __future__ import annotations

from typing import Any, cast

import pytest

from devtools.katex_text_metrics import (
    ASSET_HEADER,
    ASSET_PATH,
    GLOBAL_NAME,
    KATEX_BUNDLE,
    LETTERS_AND_DIGITS,
    MATH_ITALIC_SCALE,
    PRECISION,
    SANS_KEY,
    SANS_MATH_ITALIC_SCALE,
    SANS_SCALE_FACTORS,
    SCALE_FACTORS,
    SCALE_KEY,
    MetricsError,
    check,
    parse_asset,
    parse_katex_table,
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
    assert set(asset) == {*SCALE_FACTORS, SANS_KEY, SCALE_KEY}


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
    # Below 1 for the upright slots, which the serif factors never are: Computer Modern's
    # Greek capitals are taller than Source Sans's and shorter than PT Serif's.
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
