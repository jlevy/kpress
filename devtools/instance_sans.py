"""Generate the static Source Sans 3 instances the print stylesheet embeds.

Chromium's PDF writer cannot embed a variable font at any position but its default, so
every glyph of Source Sans 3 Variable in a printed page is drawn as a Type3 outline
path rather than set in a font. The outlines carry the right weight, but a viewer that
smooths text drawn through the font machinery -- Preview does -- leaves those paths
alone, and the sans reads a step lighter than the serif and the mathematics beside it.
A static instance embeds like any other font and is smoothed like one.

This tool instances the vendored variable faces at the weights kpress's own sans
contexts request and writes them to ``static/fonts/``, together with the stylesheet
``static/css/print-fonts.css`` that declares them as the ``Source Sans 3`` family under
print media. Both are generated files: hand edits are overwritten.

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

#: The family the static faces declare. It is the upstream name of the static Source
#: Sans 3 release, distinct from ``Source Sans 3 Variable`` so the two never share a
#: weight range and font matching never has to break a tie between them.
FAMILY: Final = "Source Sans 3"

#: The weights kpress's own sans contexts request: the three weight tokens, the two
#: literal weights of the footnote controls and of bold, and 400 for the resets. The
#: sans-mode headings at 380 and 440 land on 370 and 400, ten and forty units away,
#: and ``tests/test_print_sans_faces.py`` pins every request's landing place.
WEIGHTS: Final[tuple[int, ...]] = (370, 400, 550, 600, 650, 700)
STYLES: Final[tuple[str, ...]] = ("normal", "italic")

#: The subset the variable faces cover, repeated verbatim so a static face is never
#: asked for a glyph the variable one would have passed down the stack.
UNICODE_RANGE: Final = (
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304,\n"
    "    U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF,\n"
    "    U+FFFD"
)


def variable_face(style: str, fonts: Path = FONTS) -> Path:
    """The vendored variable face for a style."""
    return fonts / f"source-sans-3-latin-wght-{style}.woff2"


def instance_name(weight: int, style: str) -> str:
    """The file name of a static instance, beside the variable faces it comes from."""
    return f"source-sans-3-latin-{weight}-{style}.woff2"


def instance_face(variable: Path, weight: int, family: str = FAMILY) -> bytes:
    """A static woff2 instance of a variable face at one weight.

    The instance is named by its family and weight -- ``SourceSans3-370Italic`` in a
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
    """Name a pinned instance by family and weight, in every name record it carries."""
    os2 = font["OS/2"]
    italic = bool(int(os2.fsSelection) & 1)
    os2.usWeightClass = weight
    subfamily = f"{weight}{' Italic' if italic else ''}"
    postscript = f"{family.replace(' ', '')}-{weight}{'Italic' if italic else ''}"
    strings = {
        1: family,
        2: "Italic" if italic else "Regular",
        3: f"{postscript};kpress",
        4: f"{family} {subfamily}",
        6: postscript,
        16: family,
        17: subfamily,
    }
    for record in font["name"].names:
        if record.nameID in strings:
            record.string = strings[record.nameID]


def face_rule(weight: int, style: str, url: str, family: str = FAMILY) -> str:
    """One ``@font-face`` rule for a static instance, indented for a media block."""
    return (
        "  @font-face {\n"
        f'    font-family: "{family}";\n'
        f"    font-style: {style};\n"
        "    font-display: block;\n"
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
        "   Static instances of Source Sans 3 for print. Chromium's PDF writer draws a\n"
        "   variable font at a non-default weight as Type3 outline paths, which viewers\n"
        "   that smooth embedded text leave thin; a static instance embeds as a font.\n"
        "   `print.css` puts this family ahead of the variable one under print media. */\n"
        "\n"
        "@media print {\n" + "\n".join(rules) + "}\n"
    )


def expected_files(fonts: Path = FONTS) -> dict[Path, bytes]:
    """Every generated file with the bytes it should hold."""
    files: dict[Path, bytes] = {}
    for style in STYLES:
        source = variable_face(style, fonts)
        for weight in WEIGHTS:
            files[fonts / instance_name(weight, style)] = instance_face(source, weight)
    files[CSS_PATH] = stylesheet().encode()
    return files


def write() -> int:
    for path, data in expected_files().items():
        path.write_bytes(data)
        print(f"wrote {path.relative_to(ROOT)} ({len(data):,} bytes)")
    return 0


def check() -> int:
    stale = [
        path.relative_to(ROOT)
        for path, data in expected_files().items()
        if not path.exists() or path.read_bytes() != data
    ]
    if stale:
        for path in stale:
            print(f"stale: {path}", file=sys.stderr)
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
