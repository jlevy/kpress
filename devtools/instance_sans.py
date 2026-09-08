"""Generate the static Source Sans 3 instances the print stylesheet embeds.

Chromium's PDF writer cannot embed a variable font at any position but its default, so
every glyph of Source Sans 3 Variable in a printed page is drawn as a Type3 outline
path rather than set in a font. The outlines carry the right weight, but a viewer that
smooths text drawn through the font machinery -- Preview does -- leaves those paths
alone, and the sans reads a step lighter than the serif and the mathematics beside it.
A static instance embeds like any other font and is smoothed like one.

This tool instances the vendored variable faces at the weights kpress's own sans
contexts request and writes them to ``static/fonts/``, together with the stylesheet
``static/css/print-fonts.css`` that declares them as the ``KPress Print Sans`` family
under print media. Both are generated files: hand edits are overwritten.

The output is a modified version of an OFL font whose copyright holder reserves the
name "Source", so the generated family carries a name of its own (:data:`FAMILY`) and
the derived faces keep Adobe's copyright and the OFL notice in their name tables. A
host that instances its own set is in the same position and passes its own ``family``.

Run ``python -m devtools.instance_sans`` to regenerate, ``--check`` to verify the shipped
files still match their inputs. Hosts that override the weight tokens instance their own
set with :func:`instance_face` and :func:`face_rule`; the file stays importable on its
own for that, with fontTools as its only dependency.
"""

from __future__ import annotations

import argparse
import io
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, Final, cast

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT: Final = Path(__file__).resolve().parents[1]
STATIC: Final = ROOT / "src" / "kpress" / "format" / "static"
FONTS: Final = STATIC / "fonts"
CSS_PATH: Final = STATIC / "css" / "print-fonts.css"

#: The family the static faces declare. The faces are modified versions of Source Sans
#: 3, whose OFL reserves the name "Source" for the original: condition 3 of that license
#: keeps a reserved name out of the primary name a derived font presents, so the derived
#: family gets one of its own. It also keeps this set clear of ``Source Sans 3
#: Variable`` and of any Source Sans the reader has installed, so font matching never
#: has to break a tie between two families over one weight.
FAMILY: Final = "KPress Print Sans"

#: The weights kpress's own sans contexts request: the three weight tokens (370, 550
#: and 650), the footnote controls' literal 600, and 400 for the resets. The two
#: sans-mode headings ask for 380 and 440, which get no instance of their own and land
#: on 370 and 400, ten and forty units away; ``tests/test_print_sans_faces.py`` pins
#: every request's landing place.
#:
#: A 700 pair shipped here until 2026-09-07 and was dropped because no sans context asks
#: for it. ``.kpress b, .kpress strong`` sets the bold token, so 650 is the heaviest
#: weight any sans element resolves to, and the only 700s left in the stylesheets are
#: the prose ``h5`` and the mono syntax rules -- neither family can resolve to this one.
#: A host that raises a weight token above 650 lands on 650, which is the fallback
#: ``docs/kpress-operations-and-host-integration.md`` documents.
WEIGHTS: Final[tuple[int, ...]] = (370, 400, 550, 600, 650)
STYLES: Final[tuple[str, ...]] = ("normal", "italic")

#: The subset the variable faces cover, repeated verbatim so a static face is never
#: asked for a glyph the variable one would have passed down the stack. The
#: continuation lines carry the six-space indent Biome gives a wrapped value inside a
#: rule nested in ``@media``, which is the only place :func:`face_rule` puts them; the
#: repository's formatter checks the generated stylesheet like any other.
UNICODE_RANGE: Final = (
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304,\n"
    "      U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF,\n"
    "      U+FFFD"
)


def variable_face(style: str, fonts: Path = FONTS) -> Path:
    """The vendored variable face for a style."""
    return fonts / f"source-sans-3-latin-wght-{style}.woff2"


def instance_name(weight: int, style: str) -> str:
    """The file name of a static instance, beside the variable faces it comes from.

    Named for the family the file declares rather than for the face it is derived from,
    so nothing in the asset tree presents a modified font under the reserved name.
    """
    return f"kpress-print-sans-latin-{weight}-{style}.woff2"


def instance_face(variable: Path, weight: int, family: str = FAMILY) -> bytes:
    """A static woff2 instance of a variable face at one weight.

    The instance is named by its family and weight -- ``KPressPrintSans-370Italic`` in a
    PDF's font list -- rather than from the font's named instances, since the weights
    kpress asks for are not among them. The output is byte-stable for one fontTools
    release, which is what ``--check`` relies on.
    """
    font = cast(Any, TTFont(str(variable), recalcTimestamp=False))
    static = cast(Any, instancer).instantiateVariableFont(font, {"wght": weight})
    _rename(static, weight, family)
    static.flavor = "woff2"
    buffer = io.BytesIO()
    static.save(buffer)
    return buffer.getvalue()


def _rename(font: Any, weight: int, family: str) -> None:
    """Give a pinned instance a name-table identity of its own, by family and weight.

    Ten faces need ten identities, so the pair legacy consumers read -- name IDs 1 and
    2, which hold at most four styles per family -- names the weight, and the
    typographic pair (16 and 17) carries the family the ten share. The records are set
    rather than rewritten in place: an instance of the italic face has no ID 17 to
    overwrite, and none of the ten has an ID 16.

    Everything above ID 255 named the axes and named instances of the variable face,
    and ``STAT`` is what referred to them. The instance has neither an axis nor a named
    instance left, and those style names -- ``Semibold`` on the face this calls ``600``
    -- would contradict the ones written here, so both go.
    """
    os2 = font["OS/2"]
    italic = bool(int(os2.fsSelection) & 1)
    os2.usWeightClass = weight
    subfamily = f"{weight}{' Italic' if italic else ''}"
    postscript = f"{family.replace(' ', '')}-{weight}{'Italic' if italic else ''}"
    strings = {
        1: f"{family} {weight}",
        2: "Italic" if italic else "Regular",
        3: f"{postscript};kpress",
        4: f"{family} {subfamily}",
        6: postscript,
        16: family,
        17: subfamily,
    }
    names = font["name"]
    names.names = [record for record in names.names if record.nameID < 256]
    for name_id, value in strings.items():
        names.setName(value, name_id, 3, 1, 0x409)
    if "STAT" in font:
        del font["STAT"]


def face_rule(weight: int, style: str, url: str, family: str = FAMILY) -> str:
    """One ``@font-face`` rule for a static instance, indented for a media block.

    ``font-display: swap`` because these faces are asked for only once print layout
    runs, and a print layout has one chance to draw. ``block`` would hold the text
    invisible until the face arrived, and a print path that cannot wait -- a browser's
    own Print dialog, or any caller that goes straight to ``page.pdf()`` -- draws the
    page inside that window and prints the sans as nothing at all. Under ``swap`` the
    worst case is the fallback the stack already names. There is no flash to trade
    against: nothing on screen ever uses these rules.
    """
    return (
        "  @font-face {\n"
        f'    font-family: "{family}";\n'
        f"    font-style: {style};\n"
        "    font-display: swap;\n"
        f"    font-weight: {weight};\n"
        f'    src: url("{url}") format("woff2");\n'
        f"    unicode-range:\n      {UNICODE_RANGE};\n"
        "  }\n"
    )


def stylesheet(
    weights: Iterable[int] = WEIGHTS,
    styles: Iterable[str] = STYLES,
    url_prefix: str = "../fonts/",
    family: str = FAMILY,
) -> str:
    """The print-media stylesheet declaring every instance."""
    rules = [
        face_rule(weight, style, f"{url_prefix}{instance_name(weight, style)}", family)
        for style in styles
        for weight in weights
    ]
    return (
        "/* Generated by `python -m devtools.instance_sans`; do not edit.\n"
        "\n"
        "   Static instances of Source Sans 3 for print, under a family name of their\n"
        "   own because the OFL reserves the original's. Chromium's PDF writer draws a\n"
        "   variable font at a non-default weight as Type3 outline paths, which viewers\n"
        "   that smooth embedded text leave thin; a static instance embeds as a font.\n"
        "   `print.css` puts this family ahead of the variable one under print media. */\n"
        "\n"
        "@media print {\n" + "\n".join(rules) + "}\n"
    )


class MissingSourceFaceError(FileNotFoundError):
    """A vendored variable face the instances come from is not in the tree."""


def expected_files(fonts: Path = FONTS) -> dict[Path, bytes]:
    """Every generated file with the bytes it should hold.

    Raises :class:`MissingSourceFaceError` if an input face is absent, so a checkout
    that never fetched the vendored fonts is reported as that rather than as a
    ``fontTools`` traceback from somewhere inside the instancer.
    """
    files: dict[Path, bytes] = {}
    for style in STYLES:
        source = variable_face(style, fonts)
        if not source.is_file():
            raise MissingSourceFaceError(f"missing source face: {_shown(source)}")
        for weight in WEIGHTS:
            files[fonts / instance_name(weight, style)] = instance_face(source, weight)
    files[CSS_PATH] = stylesheet().encode()
    return files


def _shown(path: Path) -> str:
    """A path as the repository names it, or absolute if it lies outside."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write() -> int:
    try:
        expected = expected_files()
    except MissingSourceFaceError as exc:
        print(exc, file=sys.stderr)
        return 1
    for path, data in expected.items():
        path.write_bytes(data)
        print(f"wrote {_shown(path)} ({len(data):,} bytes)")
    return 0


def check() -> int:
    try:
        expected = expected_files()
    except MissingSourceFaceError as exc:
        print(exc, file=sys.stderr)
        return 1
    # A file that is absent and one whose bytes have moved on call for different
    # answers: the first is usually a checkout that lost it, the second a generator
    # or an input that changed under the shipped output.
    missing = [path for path in expected if not path.exists()]
    stale = [path for path, data in expected.items() if path.exists() and path.read_bytes() != data]
    for path in missing:
        print(f"missing: {_shown(path)}", file=sys.stderr)
    for path in stale:
        print(f"stale: {_shown(path)}", file=sys.stderr)
    if missing or stale:
        print("regenerate with `python -m devtools.instance_sans`", file=sys.stderr)
        return 1
    print(f"print sans faces current: {len(WEIGHTS) * len(STYLES)} instances and the stylesheet")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument(
        "--check", action="store_true", help="verify the shipped files instead of writing them"
    )
    args = parser.parse_args(argv)
    return check() if args.check else write()


if __name__ == "__main__":
    sys.exit(main())
