"""Where every sans weight kpress asks for lands on the static print instances.

Under print the sans stack leads with the static ``Source Sans 3`` family (see
print.css and devtools/instance_sans.py), which covers six weights rather than the
variable face's whole 200-900 axis. A request that has no instance is not an error: CSS
font matching picks the nearest available weight by a rule with a documented asymmetry
around 400-500, so the sans-mode headings at 380 and 440 land a step apart in direction.
This module implements that rule and pins where each request lands, so a new weight in
the stylesheets either gets an instance or is a deliberate, visible choice.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from fontTools.ttLib import TTFont

from devtools.instance_sans import FAMILY, FONTS, STYLES, WEIGHTS, check, instance_name

_CSS = Path(__file__).resolve().parents[1] / "src" / "kpress" / "format" / "static" / "css"

#: Every numeric sans weight kpress's own stylesheets request, and the instance CSS
#: Fonts 4 matching draws it from. The three weight tokens, the footnote controls' 600,
#: bold's 700 and the resets' 400 are exact; the sans-mode headings are not, and the
#: pair 380/440 is where the rule's asymmetry shows: 380 falls to 370 while 440 falls to
#: 400 rather than rising to 550, because a request inside 400-500 looks up only as far
#: as 500 before looking down. 540, just outside, rises to 550.
EXPECTED_LANDING = {
    370: 370,
    380: 370,
    400: 400,
    440: 400,
    540: 550,
    550: 550,
    600: 600,
    650: 650,
    700: 700,
}

#: The weight tokens, with the values style-tokens.css must give them.
WEIGHT_TOKENS = {"light": 370, "medium": 550, "bold": 650}

_FONT_FACE_BLOCK = re.compile(r"@font-face\s*\{[^}]*\}")
_FONT_WEIGHT = re.compile(r"font-weight:\s*([^;]+);")
_WEIGHT_TOKEN = re.compile(r"var\(\s*--kpress-font-weight-sans-(\w+)(?:,\s*(\d+))?\s*\)")


def match_weight(desired: int, available: Sequence[int]) -> int:
    """The weight CSS Fonts 4 font matching picks from ``available`` for ``desired``.

    The rule (CSS Fonts 4, "Matching font styles"): an exact match wins; below 400 the
    search goes down first and then up; above 500 it goes up first and then down; inside
    400-500 it goes up as far as 500, then down, then up again past 500.
    """
    if desired in available:
        return desired
    below = sorted((weight for weight in available if weight < desired), reverse=True)
    above = sorted(weight for weight in available if weight > desired)
    if desired < 400:
        order = [*below, *above]
    elif desired > 500:
        order = [*above, *below]
    else:
        order = [
            *(weight for weight in above if weight <= 500),
            *below,
            *(weight for weight in above if weight > 500),
        ]
    assert order, f"no face at all for {desired}"
    return order[0]


def _requested_weights() -> set[int]:
    """Every numeric font-weight kpress's own stylesheets request.

    ``@font-face`` blocks are dropped first: their ``font-weight`` declares what a face
    covers rather than what a rule asks for, and the variable face's ``200 900`` is a
    range, not a request.
    """
    tokens = (_CSS / "style-tokens.css").read_text(encoding="utf-8")
    declared = {
        name: int(value)
        for name, value in re.findall(r"--kpress-font-weight-sans-(\w+):\s*(\d+);", tokens)
    }
    assert declared == WEIGHT_TOKENS

    weights: set[int] = set()
    for path in sorted(_CSS.glob("*.css")):
        css = _FONT_FACE_BLOCK.sub("", path.read_text(encoding="utf-8"))
        for raw in _FONT_WEIGHT.findall(css):
            value = str(raw).strip()
            if value.isdigit():
                weights.add(int(value))
                continue
            token = _WEIGHT_TOKEN.fullmatch(value)
            assert token is not None, f"{path.name}: unrecognized font-weight {value!r}"
            resolved = declared[token.group(1)]
            fallback = token.group(2)
            # An inline fallback that disagreed with the token would be a second,
            # invisible weight in whatever context dropped the token.
            assert fallback is None or int(fallback) == resolved, value
            weights.add(resolved)
    return weights


def test_every_sans_weight_the_stylesheets_request_is_accounted_for() -> None:
    assert _requested_weights() == set(EXPECTED_LANDING)


def test_each_request_lands_on_its_instance() -> None:
    assert {desired: match_weight(desired, WEIGHTS) for desired in EXPECTED_LANDING} == (
        EXPECTED_LANDING
    )


def test_shipped_instances_and_stylesheet_are_current() -> None:
    """The generator agrees with what the repository ships, byte for byte."""
    assert check() == 0


def test_each_instance_is_a_static_face_named_by_its_weight() -> None:
    """A pinned instance carries no variation axes and states its weight in its names.

    The missing ``fvar`` is the point of the exercise: it is what lets Chromium's PDF
    writer embed the face instead of drawing its glyphs as outline paths. The name is
    how the face is identified in a PDF's font list, so it names the weight.
    """
    for style in STYLES:
        for weight in WEIGHTS:
            path = FONTS / instance_name(weight, style)
            font = cast(Any, TTFont(str(path)))
            names = font["name"]
            suffix = "Italic" if style == "italic" else ""
            assert "fvar" not in font, path.name
            assert font["OS/2"].usWeightClass == weight, path.name
            assert names.getDebugName(1) == FAMILY, path.name
            assert names.getDebugName(6) == f"SourceSans3-{weight}{suffix}", path.name
