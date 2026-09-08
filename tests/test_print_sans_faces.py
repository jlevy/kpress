"""Where every sans weight kpress asks for lands on the static print instances.

Under print the sans stack leads with the static ``KPress Print Sans`` family (see
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

import pytest
from fontTools.ttLib import TTFont

from devtools.instance_sans import (
    FAMILY,
    FONTS,
    STYLES,
    WEIGHTS,
    MissingSourceFaceError,
    check,
    expected_files,
    instance_name,
    variable_face,
)

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
#: Every ``font-weight`` declaration, however it is spelled and wherever it sits in its
#: block. A declaration may end at the block's closing brace rather than a semicolon,
#: the property is case-insensitive, and CSS allows space before the colon; each of
#: those spellings would have slipped past a narrower pattern, and a request this scan
#: misses is a weight that ships with no instance behind it.
_FONT_WEIGHT = re.compile(r"\bfont-weight\s*:\s*([^;}]+?)\s*[;}]", re.IGNORECASE)
#: The same property, matched on its own, to count what the scan above must find. The
#: token custom properties (``--kpress-font-weight-sans-light``) do not match: their
#: colon comes after the rest of the name.
_FONT_WEIGHT_PROPERTY = re.compile(r"\bfont-weight\s*:", re.IGNORECASE)
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

    The walk is recursive so a stylesheet added in a subdirectory of ``static/css`` is
    scanned too. KaTeX's own stylesheet is outside that tree and stays outside this
    scan: the weights it asks for are for the math faces, which are not this family.
    """
    tokens = (_CSS / "style-tokens.css").read_text(encoding="utf-8")
    declared = {
        name: int(value)
        for name, value in re.findall(r"--kpress-font-weight-sans-(\w+):\s*(\d+);", tokens)
    }
    assert declared == WEIGHT_TOKENS

    weights: set[int] = set()
    for path in sorted(_CSS.rglob("*.css")):
        css = _FONT_FACE_BLOCK.sub("", path.read_text(encoding="utf-8"))
        found = _FONT_WEIGHT.findall(css)
        # The scan must fail loudly on a spelling it cannot read, not quietly skip it.
        assert len(found) == len(_FONT_WEIGHT_PROPERTY.findall(css)), path.name
        for raw in found:
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


def test_a_missing_source_face_is_reported_as_one(tmp_path: Path) -> None:
    """``--check`` runs in CI, so a checkout without the inputs must say so.

    Without this the first thing to notice is fontTools, several frames inside the
    instancer, with a traceback that names neither the file nor what to do about it.
    """
    with pytest.raises(MissingSourceFaceError) as caught:
        _ = expected_files(tmp_path)
    assert "missing source face" in str(caught.value)
    assert variable_face("normal", tmp_path).name in str(caught.value)


def test_each_instance_is_a_static_face_named_by_its_weight() -> None:
    """A pinned instance carries no variation axes and states its weight in its names.

    The missing ``fvar`` is the point of the exercise: it is what lets Chromium's PDF
    writer embed the face instead of drawing its glyphs as outline paths. The name is
    how the face is identified in a PDF's font list, so it names the weight.

    Twelve faces need twelve identities. Name IDs 1 and 2 hold at most four styles per
    family, so the weight goes in ID 1 and the family the twelve share goes in the
    typographic pair, 16 and 17 -- records the variable inputs do not all carry, so the
    generator has to create them rather than overwrite what is there.
    """
    identities: set[tuple[str, str]] = set()
    for style in STYLES:
        for weight in WEIGHTS:
            path = FONTS / instance_name(weight, style)
            font = cast(Any, TTFont(str(path)))
            names = font["name"]
            italic = style == "italic"
            suffix = " Italic" if italic else ""
            assert "fvar" not in font, path.name
            assert font["OS/2"].usWeightClass == weight, path.name
            assert names.getDebugName(1) == f"{FAMILY} {weight}", path.name
            assert names.getDebugName(2) == ("Italic" if italic else "Regular"), path.name
            assert names.getDebugName(4) == f"{FAMILY} {weight}{suffix}", path.name
            assert names.getDebugName(6) == f"{FAMILY.replace(' ', '')}-{weight}{suffix.strip()}", (
                path.name
            )
            assert names.getDebugName(16) == FAMILY, path.name
            assert names.getDebugName(17) == f"{weight}{suffix}", path.name
            # Adobe's copyright and the OFL notice travel with the derived face; the
            # family it presents is kpress's own, since the OFL reserves "Source".
            assert "Adobe" in (names.getDebugName(0) or ""), path.name
            assert "OFL" in (names.getDebugName(14) or ""), path.name
            assert "Source" not in (names.getDebugName(1) or ""), path.name
            assert "Source" not in (names.getDebugName(16) or ""), path.name
            identities.add((names.getDebugName(1), names.getDebugName(2)))

    assert len(identities) == len(WEIGHTS) * len(STYLES)
