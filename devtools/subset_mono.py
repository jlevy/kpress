"""Generate the Planetaire Mono Text subsets KPress sets code in.

Code was the last role in a KPress document still drawn from whatever mono the
reader's machine happened to have. Planetaire Mono Text is the face chosen to end
that: B612 Mono's letterforms with Hack's punctuation and symbols, under the SIL
Open Font License, from https://github.com/jlevy/planetaire.

This tool subsets the upstream web faces down to the same latin ``unicode-range``
every other vendored face here covers, writes them to ``static/fonts/``, and writes
one stylesheet per style beside them in ``static/css/``. One stylesheet per style is
the point rather than an accident: ``RenderOptions.mono_weights`` decides which
styles a document declares, and a single-file page inlines every face it declares,
so a style that was not asked for must not reach the page at all. The renderer
selects among these files; nothing at render time rewrites CSS.

The upstream faces are **not** vendored: they are between 50 and 66 KB each and the
subsets are a third of that. Fetch them once into :data:`DEFAULT_SOURCE` (or pass
``--source``)::

    mkdir -p ~/.cache/kpress/fonts && cd ~/.cache/kpress/fonts
    for f in Regular Bold Italic BoldItalic Medium SemiBold ExtraBold; do
      curl -fLO "https://cdn.jsdelivr.net/gh/jlevy/planetaire@v0.2.0/fonts/web/PlanetaireMonoText-$f.woff2"
    done

Run ``python -m devtools.subset_mono`` to regenerate and ``--check`` to verify. As in
``devtools/subset_quotes.py``, which check runs depends on whether the sources are at
hand:

* **Sources present** (each sha256 must match :data:`SOURCES`): every subset is rebuilt
  and compared byte for byte against the shipped file. This is the real check.
* **Sources absent** -- CI, and any checkout that has not fetched them: each shipped
  file is hashed against :data:`SUBSET_SHA256`, which catches a corrupted or
  hand-edited asset but cannot catch a stale one.

The stylesheets are checked either way: they are generated from this file alone.

The subsets keep the upstream family name. Planetaire reserves no font name of its own
(its LICENSE reserves only "Bitstream" and "Vera", inherited from Hack's symbols, which
this subset does not rename), so unlike ``instance_sans.py`` and ``subset_quotes.py``
there is no reserved name to step around. ``static/fonts/README.md`` records the
provenance and ``src/kpress/licenses/planetaire-mono.txt`` carries the license text.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT: Final = Path(__file__).resolve().parents[1]
STATIC: Final = ROOT / "src" / "kpress" / "format" / "static"
FONTS: Final = STATIC / "fonts"
CSS: Final = STATIC / "css"

#: The family the subsets declare, unchanged from upstream.
FAMILY: Final = "Planetaire Mono Text"

#: The pinned upstream release. A GitHub repository we publish ourselves, so the
#: 14-day cool-off in SUPPLY-CHAIN-SECURITY.md does not apply; the tag and the
#: per-file sha256 below are the pin.
PACKAGE: Final = "jlevy/planetaire"
TAG: Final = "v0.2.0"

#: Where the tool looks for the upstream faces when ``--source`` is not given. Outside
#: the repository on purpose: the whole faces are build inputs, not something KPress
#: ships.
DEFAULT_SOURCE: Final = Path.home() / ".cache" / "kpress" / "fonts"


@dataclass(frozen=True)
class MonoStyle:
    """One style KPress offers, from its upstream file to its two generated files."""

    #: The name a host writes in ``format.mono_weights`` / ``RenderOptions``.
    name: str
    weight: int
    style: str
    #: The upstream file's style suffix, e.g. ``BoldItalic``.
    upstream: str
    #: sha256 of ``fonts/web/PlanetaireMonoText-<upstream>.woff2`` at :data:`TAG`.
    source_sha256: str

    @property
    def source_name(self) -> str:
        return f"PlanetaireMonoText-{self.upstream}.woff2"

    @property
    def font_name(self) -> str:
        return f"planetaire-mono-text-latin-{self.weight}-{self.style}.woff2"

    @property
    def css_name(self) -> str:
        return f"mono-planetaire-{self.weight}-{self.style}.css"


#: The seven styles KPress offers, in declaration order. Regular and bold are the
#: default pair; the rest opt in by name through ``mono_weights``, which is where a site
#: whose code carries italic comments buys the drawn italic instead of the browser's
#: synthesized one. The three remaining upstream italics (Medium, SemiBold and ExtraBold
#: Italic) are deliberately not vendored: no KPress rule asks for an italic above 700,
#: and every vendored file is bytes in the wheel whether or not a document declares it.
SOURCES: Final[tuple[MonoStyle, ...]] = (
    MonoStyle(
        name="regular",
        weight=400,
        style="normal",
        upstream="Regular",
        source_sha256="f412b36c96e0b92dcb0d9d476e572375706d449616d341c7429af02eac7b408f",
    ),
    MonoStyle(
        name="bold",
        weight=700,
        style="normal",
        upstream="Bold",
        source_sha256="3c56f2c14f843426a868cbd0730cdeff061eddb2614a7d9481ab885a4cf84820",
    ),
    MonoStyle(
        name="italic",
        weight=400,
        style="italic",
        upstream="Italic",
        source_sha256="348c6582e8ec6822a3d5d3fda89196f04320b5ed0b873ab1fb7404ede0ac7d7b",
    ),
    MonoStyle(
        name="bold-italic",
        weight=700,
        style="italic",
        upstream="BoldItalic",
        source_sha256="a477f92124203bb20fc02c31ff6817584d879caa568ae3d88cc89e432fbba133",
    ),
    MonoStyle(
        name="medium",
        weight=500,
        style="normal",
        upstream="Medium",
        source_sha256="fcfc30f97d941c24058aab40f9f1d3744dde4c19194df85327f2837227eaaf7f",
    ),
    MonoStyle(
        name="semibold",
        weight=600,
        style="normal",
        upstream="SemiBold",
        source_sha256="16d6807dc7157e4a2e9d86a7087ea2ebddf58d95b5909aca1305131d12b17bdc",
    ),
    MonoStyle(
        name="extrabold",
        weight=800,
        style="normal",
        upstream="ExtraBold",
        source_sha256="51da9327a03ca057ccf156636086929d784ebd7037ce02f9d3763841802b7bdc",
    ),
)

#: The generated subsets, for the check that runs when the sources are not at hand.
SUBSET_SHA256: Final[dict[str, str]] = {
    "planetaire-mono-text-latin-400-normal.woff2": (
        "0ecd530d8bdc55cc58ace248b570949c17043a16638b93c19a8c1a16591a23ed"
    ),
    "planetaire-mono-text-latin-700-normal.woff2": (
        "5b01f48d9a28b2657a74cc1f36043544eb19800726a08775088d1478be2edb7b"
    ),
    "planetaire-mono-text-latin-400-italic.woff2": (
        "079d54b75f6d5822224ccb27d9d62e9fac0f12b6f6ee467b215ed8022ad87954"
    ),
    "planetaire-mono-text-latin-700-italic.woff2": (
        "4665ca22f8e645185e6137e53a535a021f1d0e1a8b68f7a20c1c7f31f948b71b"
    ),
    "planetaire-mono-text-latin-500-normal.woff2": (
        "ad5b7520c3a8c54c1752a14800cc1791590c17e8321637b2c74b7f963dae53ff"
    ),
    "planetaire-mono-text-latin-600-normal.woff2": (
        "d480c09ee43ab1f749ce1637555acd09e6f3674faae365ed2604e7314b6cc804"
    ),
    "planetaire-mono-text-latin-800-normal.woff2": (
        "18e5a3f5eb67ade69a4ae21a64ab94a46e7064190f0f4468fceaec2fce622f9f"
    ),
}

#: The subset every vendored face here covers, spelled as ``instance_sans.py`` spells
#: it so no two families in one document disagree about which code points they answer.
#: The continuation lines carry the four-space indent Biome gives a wrapped value in a
#: top-level rule; the repository's formatter checks the generated stylesheets like any
#: other file.
UNICODE_RANGE: Final = (
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304,\n"
    "    U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF,\n"
    "    U+FFFD"
)

#: The code points :data:`UNICODE_RANGE` names, for the subsetter.
CODE_POINTS: Final[tuple[int, ...]] = (
    *range(0x0000, 0x0100),
    0x0131,
    0x0152,
    0x0153,
    0x02BB,
    0x02BC,
    0x02C6,
    0x02DA,
    0x02DC,
    0x0304,
    0x0308,
    0x0329,
    *range(0x2000, 0x2070),
    0x20AC,
    0x2122,
    0x2191,
    0x2193,
    0x2212,
    0x2215,
    0xFEFF,
    0xFFFD,
)

#: Tables the subsets have no use for. ``DSIG`` describes bytes that no longer exist
#: after subsetting, and the Nerd Font icon machinery upstream carries is out of range
#: by construction. Everything a mono face needs to lay out code -- ``cmap``, ``hmtx``,
#: the layout tables -- stays.
DROP_TABLES: Final[tuple[str, ...]] = ("DSIG",)


def subset_face(source: Path) -> bytes:
    """One upstream face reduced to :data:`CODE_POINTS`, as woff2 bytes.

    Byte-stable for one fontTools release, which is what ``--check`` relies on.
    ``recalcTimestamp=False`` keeps the upstream ``head.modified`` rather than
    stamping the run's clock into the output. Nothing is renamed: the subset keeps
    upstream's family, style and PostScript names, so a PDF's font list and a
    browser's font panel both say ``Planetaire Mono Text``.
    """
    font = cast(Any, TTFont(str(source), recalcTimestamp=False))
    options = cast(Any, subset.Options())
    options.notdef_outline = True
    options.glyph_names = False
    options.recommended_glyphs = False
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.name_languages = ["*"]
    options.drop_tables += list(DROP_TABLES)
    subsetter = cast(Any, subset.Subsetter(options=options))
    subsetter.populate(unicodes=list(CODE_POINTS))
    subsetter.subset(font)
    font.flavor = "woff2"
    buffer = io.BytesIO()
    font.save(buffer)
    return buffer.getvalue()


def face_rule(style: MonoStyle, url_prefix: str = "../fonts/") -> str:
    """The ``@font-face`` rule for one style, as its own stylesheet.

    ``font-display: block`` matches the other reader faces: code is text a reader
    reads, and a swap from the platform mono to this one at a different size would
    reflow the line it sits in.
    """
    return (
        f"/* Generated by `python -m devtools.subset_mono`; do not edit.\n"
        f"\n"
        f"   Planetaire Mono Text {style.name}, the face KPress sets code in. One\n"
        f"   stylesheet per style because `RenderOptions.mono_weights` decides which\n"
        f"   styles a document declares, and an inlined page carries every face it\n"
        f"   declares. Provenance: static/fonts/README.md. */\n"
        f"\n"
        f"@font-face {{\n"
        f'  font-family: "{FAMILY}";\n'
        f"  font-style: {style.style};\n"
        f"  font-display: block;\n"
        f"  font-weight: {style.weight};\n"
        f'  src: url("{url_prefix}{style.font_name}") format("woff2");\n'
        f"  unicode-range:\n    {UNICODE_RANGE};\n"
        f"}}\n"
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _shown(path: Path) -> str:
    """A path as the repository names it, or absolute if it lies outside."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _resolve_sources(source: Path | None) -> dict[str, Path] | None:
    """The upstream faces if they are all present and are the versions we pinned."""
    directory = source if source is not None else DEFAULT_SOURCE
    found: dict[str, Path] = {}
    for style in SOURCES:
        path = directory / style.source_name
        if not path.exists():
            if source is not None:
                print(f"no such file: {path}", file=sys.stderr)
                raise SystemExit(2)
            return None
        digest = _sha256(path.read_bytes())
        if digest != style.source_sha256:
            print(f"{path} is not the pinned source", file=sys.stderr)
            print(f"  expected sha256 {style.source_sha256}", file=sys.stderr)
            print(f"  found    sha256 {digest}", file=sys.stderr)
            raise SystemExit(2)
        found[style.name] = path
    return found


def stylesheets() -> dict[Path, bytes]:
    """Every generated stylesheet with the bytes it should hold."""
    return {CSS / style.css_name: face_rule(style).encode() for style in SOURCES}


def subsets(sources: dict[str, Path]) -> dict[Path, bytes]:
    """Every generated font file with the bytes it should hold."""
    return {FONTS / style.font_name: subset_face(sources[style.name]) for style in SOURCES}


def write(source: Path | None = None) -> int:
    sources = _resolve_sources(source)
    if sources is None:
        print(f"no source faces in {DEFAULT_SOURCE}", file=sys.stderr)
        print("fetch them as the module docstring shows, or pass --source", file=sys.stderr)
        return 2
    for path, data in {**subsets(sources), **stylesheets()}.items():
        path.write_bytes(data)
        print(f"wrote {_shown(path)} ({len(data):,} bytes)")
    print()
    print("SUBSET_SHA256 for this run:")
    for style in SOURCES:
        digest = _sha256((FONTS / style.font_name).read_bytes())
        print(f'    "{style.font_name}": (\n        "{digest}"\n    ),')
    return 0


def check(source: Path | None = None) -> int:
    failed = False
    for path, data in stylesheets().items():
        if not path.exists():
            print(f"missing: {_shown(path)}", file=sys.stderr)
            failed = True
        elif path.read_bytes() != data:
            print(f"stale: {_shown(path)}", file=sys.stderr)
            failed = True
    sources = _resolve_sources(source)
    if sources is None:
        for style in SOURCES:
            path = FONTS / style.font_name
            expected = SUBSET_SHA256[style.font_name]
            if not path.exists():
                print(f"missing: {_shown(path)}", file=sys.stderr)
                failed = True
                continue
            digest = _sha256(path.read_bytes())
            if digest != expected:
                print(f"corrupt: {_shown(path)}", file=sys.stderr)
                print(f"  expected sha256 {expected}", file=sys.stderr)
                print(f"  found    sha256 {digest}", file=sys.stderr)
                failed = True
        if failed:
            print("regenerate with `python -m devtools.subset_mono`", file=sys.stderr)
            return 1
        print(f"mono faces match their recorded sha256 ({len(SOURCES)} subsets)")
        print(f"fetch the upstream faces into {DEFAULT_SOURCE} for the fresh-subset check")
        return 0
    for path, data in subsets(sources).items():
        if not path.exists():
            print(f"missing: {_shown(path)}", file=sys.stderr)
            failed = True
        elif path.read_bytes() != data:
            print(f"stale: {_shown(path)}", file=sys.stderr)
            failed = True
    if failed:
        print("regenerate with `python -m devtools.subset_mono`", file=sys.stderr)
        return 1
    print(f"mono faces current: {len(SOURCES)} subsets and their stylesheets")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument(
        "--check", action="store_true", help="verify the shipped files instead of writing them"
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help=f"directory holding the upstream faces (default: {DEFAULT_SOURCE})",
    )
    args = parser.parse_args(argv)
    return check(args.source) if args.check else write(args.source)


if __name__ == "__main__":
    sys.exit(main())
