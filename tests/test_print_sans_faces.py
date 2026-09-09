"""Where every sans weight kpress asks for lands on the static print instances.

Under print the sans stack leads with the static ``KPress Print Sans`` family (see
print.css and devtools/instance_sans.py), which covers discrete weights rather than the
variable face's whole 200-900 axis. A request that has no instance is not an error: CSS
font matching picks the nearest available weight by a rule with a documented asymmetry
around 400-500, so the sans-mode headings at 380 and 440 land a step apart in direction.
This module implements that rule and pins where each request lands, so a new weight in
the stylesheets either gets an instance or is a deliberate, visible choice.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import pytest
from fontTools.ttLib import TTFont

from devtools.instance_sans import (
    FAMILY,
    FONTS,
    REGULAR_WEIGHT,
    STYLES,
    WEIGHTS,
    MissingSourceFaceError,
    check,
    expected_files,
    instance_name,
    regular_weight,
    variable_face,
)

_CSS = Path(__file__).resolve().parents[1] / "src" / "kpress" / "format" / "static" / "css"

#: Every numeric sans weight kpress's own stylesheets request, and the instance CSS
#: Fonts 4 matching draws it from. The regular, medium and bold tokens and the footnote controls' 600 are exact; the sans-mode headings are not, and the pair 380/440
#: is where the rule's asymmetry shows: 380 falls to 370 while 440 falls to 410 rather
#: than rising to 550, because a request inside 400-500 looks up only as far as 500
#: before looking down. 540, just outside, rises to 550.
#:
#: 700 is here because the scan below still finds it in the stylesheets, but it
#: deliberately has no instance: every rule that asks for it is prose (``.kpress-prose
#: h5``, which sets the prose family) or mono (the syntax rules), and neither family can
#: resolve to the print sans. Sans bold is the 650 token, so 650 is the heaviest weight
#: a sans element reaches, and a stray 700 request lands there.
EXPECTED_LANDING = {
    380: 370,
    400: 400,
    410: 410,
    440: 410,
    540: 550,
    550: 550,
    600: 600,
    650: 650,
    700: 650,
}

#: The weight tokens, with the values style-tokens.css must give them.
WEIGHT_TOKENS = {"regular": 410, "medium": 550, "bold": 650}

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
    assert "--kpress-font-weight-sans-light: var(--kpress-font-weight-sans-regular);" in tokens
    declared["light"] = declared["regular"]

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
            if value == "var(--_kpress-font-weight-prose)":
                # The reading choice switches the prose family and its regular weight
                # together; the serif path stays 400.
                weights.update((400, REGULAR_WEIGHT))
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


def test_regular_weight_reader_rejects_ambiguous_or_invalid_settings(tmp_path: Path) -> None:
    tokens = tmp_path / "tokens.css"
    for text in (
        ":root {}",
        ":root {--kpress-font-weight-sans-regular: var(--another);}",
        ":root {--kpress-font-weight-sans-regular: 901;}",
        ":root {--kpress-font-weight-sans-regular: 600;}",
        ":root {--kpress-font-weight-sans-regular: 650;}",
        ":root {--kpress-font-weight-sans-regular: 410; --kpress-font-weight-sans-regular: 420;}",
    ):
        tokens.write_text(text)
        with pytest.raises(ValueError, match="expected one numeric regular sans weight"):
            regular_weight(tokens)


def test_one_token_regenerates_print_faces_composite_metrics_and_warmup(tmp_path: Path) -> None:
    """A different source weight must not require editing any generated weight literal."""
    from devtools.katex_text_metrics import ASSET_PATH, parse_asset

    project = Path(__file__).resolve().parents[1]
    copied_static = tmp_path / "src" / "kpress" / "format" / "static"
    shutil.copytree(_CSS.parent, copied_static)
    shutil.copy(project / "src/kpress/format/assets.py", copied_static.parent / "assets.py")
    (tmp_path / "devtools").mkdir()
    for name in ("__init__.py", "instance_sans.py", "katex_text_metrics.py"):
        shutil.copy(project / "devtools" / name, tmp_path / "devtools" / name)
    tokens = copied_static / "css/style-tokens.css"
    tokens.write_text(
        tokens.read_text().replace(
            f"--kpress-font-weight-sans-regular: {REGULAR_WEIGHT};",
            "--kpress-font-weight-sans-regular: 500;",
        )
    )
    for module in ("devtools.instance_sans", "devtools.katex_text_metrics"):
        subprocess.run(
            [sys.executable, "-m", module], cwd=tmp_path, check=True, capture_output=True, text=True
        )

    baseline = parse_asset(ASSET_PATH.read_text())["sans"]
    changed = parse_asset((copied_static / "katex/katex-text-metrics.js").read_text())["sans"]
    assert changed["Main-Regular"] != baseline["Main-Regular"]
    assert changed["Math-Italic"] != baseline["Math-Italic"]
    assert changed["Main-Bold"] == baseline["Main-Bold"]
    assert changed["Math-BoldItalic"] == baseline["Math-BoldItalic"]
    assert changed["fonts"][:2] == [
        "500 1em 'KPress Math Text Sans'",
        "italic 500 1em 'KPress Math Text Sans'",
    ]
    composite = (copied_static / "katex/katex-text-face.css").read_text()
    assert "--_kpress-math-sans-regular-weight: 500;" in composite
    for style in STYLES:
        filename = instance_name(500, style)
        font = cast(Any, TTFont(copied_static / "fonts" / filename))
        assert font["OS/2"].usWeightClass == 500
        assert filename in composite
        assert filename in (copied_static / "css/print-fonts.css").read_text()
        assert filename in (copied_static.parent / "assets.py").read_text()


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

    Ten faces need ten identities. Name IDs 1 and 2 hold at most four styles per family,
    so the weight goes in ID 1 and the family the ten share goes in the typographic
    pair, 16 and 17 -- records the variable inputs do not all carry, so the generator
    has to create them rather than overwrite what is there.
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
