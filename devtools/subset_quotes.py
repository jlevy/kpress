"""Generate the six-glyph quote face KPress ships beside PT Serif.

PT Serif draws its own quotation marks badly: at an 18px reading size its opening pair
hangs about 2px above its closing pair, and its curly doubles are 16% wider than the
Georgia marks KPress used to borrow through a ``local()`` face. Borrowing solved the
look and broke the rule that every glyph in a document comes from a face KPress ships,
so the marks are shipped instead -- six glyphs of Source Serif 4, the companion of the
Source Sans 3 and Source Code Pro faces already vendored here.

This tool subsets the upstream ``source-serif-4-latin-400-normal.woff2`` down to the
straight and curly quotes and the apostrophe, renames the result to the family
``KPress Quotes``, and writes ``static/fonts/kpress-quotes.woff2``. The 20 KB source is
deliberately **not** vendored: only the subset is, at well under a kilobyte. Fetch the
source once into :data:`DEFAULT_SOURCE` (or pass ``--source``)::

    mkdir -p ~/.cache/kpress/fonts && cd ~/.cache/kpress/fonts
    npm pack @fontsource/source-serif-4@5.3.0 --ignore-scripts
    tar xzOf fontsource-source-serif-4-5.3.0.tgz \\
        package/files/source-serif-4-latin-400-normal.woff2 \\
        > source-serif-4-latin-400-normal.woff2

Run ``python -m devtools.subset_quotes`` to regenerate and ``--check`` to verify. The two
checks are not the same, and which one runs depends on whether the source is at hand:

* **Source present** (its sha256 must match :data:`SOURCE_SHA256`): the subset is rebuilt
  and compared byte for byte against the shipped file. This is the real check.
* **Source absent** -- CI, and any checkout that has not fetched it: the shipped file is
  hashed and compared against :data:`SUBSET_SHA256`, which catches a corrupted or
  hand-edited asset but cannot catch a stale one. Fetch the source to get the real check.

Output is byte-stable for one fontTools release, which is what ``--check`` relies on;
``static/fonts/README.md`` records the provenance, and the OFL text ships in
``src/kpress/licenses/source-serif-4.txt``.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final, cast

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT: Final = Path(__file__).resolve().parents[1]
STATIC: Final = ROOT / "src" / "kpress" / "format" / "static"
FONTS: Final = STATIC / "fonts"
OUTPUT: Final = FONTS / "kpress-quotes.woff2"

#: Where the tool looks for the upstream face when ``--source`` is not given. Outside the
#: repository on purpose: the whole face is a build input, not something KPress ships.
DEFAULT_SOURCE: Final = (
    Path.home() / ".cache" / "kpress" / "fonts" / "source-serif-4-latin-400-normal.woff2"
)

#: ``package/files/source-serif-4-latin-400-normal.woff2`` inside
#: ``@fontsource/source-serif-4`` 5.3.0, published 2026-07-19 under OFL-1.1.
SOURCE_SHA256: Final = "02194deb92d3975dd30e11a3824a1f1db32b48c93654e60560cb81ce8e7b5f95"

#: The generated subset, for the check that runs when the source is not at hand.
SUBSET_SHA256: Final = "c1b4e25238045596fcee7c888f5cc589d5294f59ab8feb2745c57824682df570"

#: The family the subset declares, and its PostScript name. Not ``Source Serif 4``: this
#: is a modified version of an OFL face whose license reserves the upstream name for the
#: original, the same reason ``devtools/instance_sans.py`` writes ``KPress Print Sans``.
#: It also settles font matching, since a page that asked for Source Serif 4 by name
#: would otherwise get quotation marks and nothing else. Adobe's copyright and the OFL
#: notice stay in the name table. The PostScript name is what a PDF's ``/BaseFont``
#: carries, after the subset tag.
FAMILY: Final = "KPress Quotes"
POSTSCRIPT_NAME: Final = "KPressQuotes-Regular"

#: The straight quote and apostrophe, the curly singles, and the curly doubles. The same
#: six code points the retired ``LocalPunct`` face covered, and the same six the
#: ``@font-face`` in ``style-tokens.css`` declares as its ``unicode-range``.
CODE_POINTS: Final[tuple[int, ...]] = (0x0022, 0x0027, 0x2018, 0x2019, 0x201C, 0x201D)

#: Tables a six-glyph face has no use for. The layout tables go because the subset keeps
#: no features (kerning six marks against nothing), ``BASE`` and ``STAT`` describe a
#: family this file is no longer part of, and ``gasp`` is hinting advice for outlines
#: whose hints are dropped below.
DROP_TABLES: Final[tuple[str, ...]] = ("BASE", "STAT", "GDEF", "GSUB", "GPOS", "gasp", "DSIG")

#: Name records the subset keeps. The upstream copyright (0), version (5) and license
#: URL (14) stay exactly as Adobe wrote them, which is the OFL attribution; the family
#: and PostScript names are rewritten below.
KEEP_NAME_IDS: Final[tuple[int, ...]] = (0, 1, 2, 3, 4, 5, 6, 14)


def subset_quotes(source: Path, family: str = FAMILY, postscript: str = POSTSCRIPT_NAME) -> bytes:
    """The quote face as woff2 bytes: six glyphs of *source*, renamed to *family*.

    Byte-stable for one fontTools release. ``recalcTimestamp=False`` keeps the upstream
    ``head.modified`` rather than stamping the run's clock into the output.
    """
    font = cast(Any, TTFont(str(source), recalcTimestamp=False))
    options = cast(Any, subset.Options())
    options.layout_features = []
    options.hinting = False
    options.notdef_outline = False
    options.glyph_names = False
    options.recommended_glyphs = False
    options.name_IDs = list(KEEP_NAME_IDS)
    options.name_legacy = False
    options.name_languages = ["*"]
    options.drop_tables += list(DROP_TABLES)
    subsetter = cast(Any, subset.Subsetter(options=options))
    subsetter.populate(unicodes=list(CODE_POINTS))
    subsetter.subset(font)
    _rename(font, family, postscript)
    font.flavor = "woff2"
    buffer = io.BytesIO()
    font.save(buffer)
    return buffer.getvalue()


def _rename(font: Any, family: str, postscript: str) -> None:
    """Give the subset its own identity, leaving the upstream credits alone."""
    strings = {
        1: family,
        2: "Regular",
        3: f"{postscript};kpress",
        4: family,
        6: postscript,
    }
    for record in font["name"].names:
        if record.nameID in strings:
            record.string = strings[record.nameID]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _resolve_source(source: Path | None) -> Path | None:
    """The source file if it is where we expect it and is the version we pinned."""
    path = source if source is not None else DEFAULT_SOURCE
    if not path.exists():
        if source is not None:
            print(f"no such file: {path}", file=sys.stderr)
            raise SystemExit(2)
        return None
    digest = _sha256(path.read_bytes())
    if digest != SOURCE_SHA256:
        print(f"{path} is not the pinned source", file=sys.stderr)
        print(f"  expected sha256 {SOURCE_SHA256}", file=sys.stderr)
        print(f"  found    sha256 {digest}", file=sys.stderr)
        raise SystemExit(2)
    return path


def write(source: Path | None = None) -> int:
    path = _resolve_source(source)
    if path is None:
        print(f"no source font at {DEFAULT_SOURCE}", file=sys.stderr)
        print("fetch it as the module docstring shows, or pass --source", file=sys.stderr)
        return 2
    data = subset_quotes(path)
    OUTPUT.write_bytes(data)
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({len(data):,} bytes)")
    print(f"sha256 {_sha256(data)}")
    return 0


def check(source: Path | None = None) -> int:
    if not OUTPUT.exists():
        print(f"missing: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    shipped = OUTPUT.read_bytes()
    path = _resolve_source(source)
    if path is None:
        if _sha256(shipped) != SUBSET_SHA256:
            print(f"corrupt: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
            print(f"  expected sha256 {SUBSET_SHA256}", file=sys.stderr)
            print(f"  found    sha256 {_sha256(shipped)}", file=sys.stderr)
            return 1
        print(f"quote face matches its recorded sha256 ({len(shipped):,} bytes)")
        print(f"fetch {DEFAULT_SOURCE.name} to check it against a fresh subset instead")
        return 0
    if shipped != subset_quotes(path):
        print(f"stale: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        print("regenerate with `python -m devtools.subset_quotes`", file=sys.stderr)
        return 1
    print(f"quote face current: {len(CODE_POINTS)} glyphs, {len(shipped):,} bytes")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument(
        "--check", action="store_true", help="verify the shipped file instead of writing it"
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help=f"the upstream woff2 (default: {DEFAULT_SOURCE})",
    )
    args = parser.parse_args(argv)
    return check(args.source) if args.check else write(args.source)


if __name__ == "__main__":
    sys.exit(main())
