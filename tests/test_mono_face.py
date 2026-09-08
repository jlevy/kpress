"""What the shipped mono face is, and what the two mono settings select from it.

Three questions, none of which needs a browser:

- the vendored files are the ones ``devtools/subset_mono.py`` would write, and each
  stylesheet declares exactly the face its name says;
- ``mono_font`` and ``mono_weights`` decide which of those files a render declares,
  and nothing that was not declared reaches the manifest;
- the 0.87 size token is the ratio the two faces' ink asks for, re-derived here from
  the shipped bytes rather than restated.

The browser half -- which face Chromium actually resolved -- is in
``test_playwright_mono_face.py``, and the PDF half in
``test_playwright_print_pdf_fonts.py``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

from fontTools.ttLib import TTFont

from devtools.subset_mono import CSS, FAMILY, FONTS, SOURCES, check
from kpress.format import DocumentInput, RenderOptions, render_page
from kpress.format.assets import (
    MONO_FONT_ASSETS,
    package_asset_manifest,
    package_asset_refs,
)
from kpress.format.model import DEFAULT_MONO_WEIGHTS, MONO_WEIGHT_ORDER, MonoWeight

_STATIC = Path(__file__).resolve().parents[1] / "src" / "kpress" / "format" / "static"
_STYLE_TOKENS = _STATIC / "css" / "style-tokens.css"

#: The prose face the mono is sized against, and the reading column it has to fit.
_PROSE_FACE = _STATIC / "fonts" / "pt-serif-latin-400-normal.woff2"
#: ``--kpress-measure: calc(var(--kpress-font-size-base) * 45)`` in style-tokens.css.
_MEASURE_EM = 45


def _document(body: str, options: RenderOptions) -> str:
    return render_page(
        DocumentInput(title="Doc", source_text=body, body_markdown=body, source_path="doc.md"),
        options,
    ).html


def _ink(path: Path, character: str) -> tuple[float, float]:
    """A face's x-height and one column's advance, in em, from its outlines."""
    from fontTools.pens.boundsPen import BoundsPen

    font = cast(Any, TTFont(str(path), lazy=True))
    upm = float(font["head"].unitsPerEm)
    cmap = cast(dict[int, str], font.getBestCmap())
    glyphs = font.getGlyphSet()
    pen: Any = BoundsPen(glyphs)
    glyphs[cmap[ord("x")]].draw(pen)
    advance = float(font["hmtx"][cmap[ord(character)]][0])
    # (xMin, yMin, xMax, yMax): the top of a lowercase x is the face's ink x-height,
    # which is the number the size ratio is derived from.
    return float(pen.bounds[3]) / upm, advance / upm


def test_the_generator_agrees_with_the_shipped_files() -> None:
    """The same gate ``make lint-check`` runs, so a stale asset fails the suite too."""
    assert check() == 0


def test_every_offered_style_ships_a_subset_and_a_stylesheet() -> None:
    for style in SOURCES:
        assert (FONTS / style.font_name).is_file(), style.font_name
        assert (CSS / style.css_name).is_file(), style.css_name
    # The generator's styles and the manifest's are one list written twice; a style
    # added to one and not the other is the failure this catches.
    assert {style.name for style in SOURCES} == set(MONO_FONT_ASSETS)
    assert tuple(style.name for style in SOURCES) == MONO_WEIGHT_ORDER
    for style in SOURCES:
        assert MONO_FONT_ASSETS[cast(MonoWeight, style.name)] == (
            f"css/{style.css_name}",
            f"fonts/{style.font_name}",
        )


def test_each_stylesheet_declares_exactly_its_own_face() -> None:
    for style in SOURCES:
        css = (CSS / style.css_name).read_text(encoding="utf-8")
        assert css.count("@font-face") == 1, style.css_name
        assert f'font-family: "{FAMILY}";' in css, style.css_name
        assert f"font-weight: {style.weight};" in css, style.css_name
        assert f"font-style: {style.style};" in css, style.css_name
        assert f'url("../fonts/{style.font_name}")' in css, style.css_name
        # The same range the other vendored faces answer, so no two families in one
        # document disagree about which code points they cover.
        assert "U+0000-00FF" in css and "U+FFFD" in css, style.css_name


def test_the_subsets_keep_the_upstream_identity() -> None:
    """No rename: Planetaire reserves no font name, unlike Source Sans and Source Serif.

    The upstream copyright and the OFL notice have to survive the subsetting too --
    they are the attribution the license asks for, and they travel in the file rather
    than beside it.
    """
    for style in SOURCES:
        font = cast(Any, TTFont(str(FONTS / style.font_name), lazy=True))
        names = font["name"]
        assert names.getDebugName(1) == FAMILY, style.font_name
        assert names.getDebugName(6) == f"PlanetaireMonoText-{style.upstream}", style.font_name
        assert "Open Font License" in (names.getDebugName(13) or ""), style.font_name
        assert "Joshua Levy" in (names.getDebugName(0) or ""), style.font_name
        assert font["OS/2"].usWeightClass == style.weight, style.font_name


def test_the_default_declares_the_upright_and_bold_faces_and_nothing_else() -> None:
    manifest = package_asset_manifest(mode="hashed")
    ids = {asset.id for asset in manifest.assets}
    declared = {path for weight in DEFAULT_MONO_WEIGHTS for path in MONO_FONT_ASSETS[weight]}
    assert declared <= ids
    withheld = {
        path
        for weight, paths in MONO_FONT_ASSETS.items()
        if weight not in DEFAULT_MONO_WEIGHTS
        for path in paths
    }
    assert not withheld & ids, sorted(withheld & ids)
    # The stylesheets are entry points, so they are linked rather than merely copied.
    assert declared <= set(package_asset_refs()["css"]) | {
        asset.id for asset in manifest.assets if asset.loading == "resource"
    }


def test_mono_weights_selects_exactly_the_declared_faces() -> None:
    cases: tuple[tuple[MonoWeight, ...], ...] = (
        ("regular",),
        ("regular", "italic"),
        ("bold", "regular"),
        MONO_WEIGHT_ORDER,
        (),
    )
    for weights in cases:
        manifest = package_asset_manifest(mode="hashed", mono_weights=weights)
        ids = {asset.id for asset in manifest.assets}
        expected = {path for weight in weights for path in MONO_FONT_ASSETS[weight]}
        unexpected = {path for paths in MONO_FONT_ASSETS.values() for path in paths} - expected
        assert expected <= ids, weights
        assert not unexpected & ids, (weights, sorted(unexpected & ids))


def test_the_default_pair_leaves_the_syntax_italics_to_the_browser() -> None:
    """The default is short, not complete, and the docs say which.

    `syntax.css` sets comments and docstrings italic, and the default `mono_weights`
    declares no italic face, so a browser slants the upright one. That is a deliberate
    trade -- 15 KB for an italic a prose page uses in one comment -- and it stops being
    a trade the moment either half changes: an italic added to the default pair, or the
    italic rules removed from the highlighter. Either way this fails and the paragraphs
    in `kpress-design.md` and the fonts README get revisited.
    """
    syntax = (_STATIC / "css" / "syntax.css").read_text(encoding="utf-8")
    assert "font-style: italic;" in syntax
    assert "italic" not in DEFAULT_MONO_WEIGHTS
    assert "bold-italic" not in DEFAULT_MONO_WEIGHTS
    # But the drawn faces are vendored, so naming them is all a host has to do.
    assert {"italic", "bold-italic"} <= set(MONO_FONT_ASSETS)


def test_declaration_order_is_the_generator_s_order_not_the_host_s() -> None:
    """Two hosts that enable the same styles get byte-identical pages."""
    forwards = package_asset_refs(mono_weights=("regular", "italic", "bold"))["css"]
    backwards = package_asset_refs(mono_weights=("bold", "italic", "regular"))["css"]
    assert forwards == backwards


def test_system_mono_declares_no_face_at_all() -> None:
    manifest = package_asset_manifest(mode="hashed", mono_font="system")
    ids = {asset.id for asset in manifest.assets}
    every_mono = {path for paths in MONO_FONT_ASSETS.values() for path in paths}
    assert not every_mono & ids, sorted(every_mono & ids)
    # And the reader faces that are not mono are untouched: this setting is about code.
    assert "fonts/pt-serif-latin-400-normal.woff2" in ids


def test_the_page_stamps_and_links_what_each_setting_selected() -> None:
    body = "# Doc\n\nProse with `inline code` in it.\n"
    default = _document(body, RenderOptions(asset_mode="linked"))
    assert 'data-kpress-mono-font="planetaire"' in default
    assert "mono-planetaire-400-normal.css" in default
    assert "mono-planetaire-400-italic.css" not in default

    system = _document(body, RenderOptions(asset_mode="linked", mono_font="system"))
    assert 'data-kpress-mono-font="system"' in system
    assert "mono-planetaire" not in system
    assert "planetaire-mono-text" not in system


def test_the_style_tokens_switch_on_the_stamped_attribute() -> None:
    css = _STYLE_TOKENS.read_text(encoding="utf-8")
    assert '.kpress[data-kpress-mono-font="system"]' in css
    assert '[data-kpress-mono-font="system"] .kpress-page-main' in css
    # The default stack leads with the shipped face; the switch hands code back.
    default_stack = css.split("--kpress-font-mono:", 1)[1].split(";", 1)[0]
    assert f'"{FAMILY}"' in default_stack
    override = css.split('.kpress[data-kpress-mono-font="system"]', 1)[1].split("}", 1)[0]
    assert FAMILY not in override
    assert "ui-monospace" in override
    # font_mode="system" is the other way to ask for the platform mono, and it has to
    # cover code now that code is a shipped face rather than the platform's own.
    font_mode = css.split('.kpress[data-kpress-fonts="system"]', 1)[1].split("}", 1)[0]
    assert "--kpress-font-mono:" in font_mode
    assert FAMILY not in font_mode


def test_the_mono_size_token_is_the_ratio_the_two_faces_ask_for() -> None:
    """0.87 is derived, so this re-derives it instead of restating the number.

    The mono rung is chosen so code's x-height lands a hair under the prose x-height
    beside it -- close enough that a code span does not bulge out of its line, under
    it so it still reads as an inset. The width consequence is the second half: a
    mono column is an advance wide whatever the letter, so the ratio also fixes how
    much code fits the reading measure.
    """
    css = _STYLE_TOKENS.read_text(encoding="utf-8")
    token = re.search(
        r"--kpress-font-size-mono:\s*var\(\s*--kpress-host-font-size-mono,\s*"
        r"calc\(var\(--kpress-font-size-base\) \* ([\d.]+)\)",
        re.sub(r"\s+", " ", css),
    )
    assert token is not None, "the mono rung is no longer a base-derived ratio"
    ratio = float(token.group(1))

    mono_x, mono_advance = _ink(FONTS / MONO_FONT_ASSETS["regular"][1].removeprefix("fonts/"), "m")
    prose_x, _ = _ink(_PROSE_FACE, "m")
    assert mono_x == 0.560, mono_x
    assert prose_x == 0.500, prose_x

    # Code's x-height against the prose x-height beside it: 97%, just under parity.
    relative_x_height = (ratio * mono_x) / prose_x
    assert 0.95 <= relative_x_height <= 1.0, relative_x_height
    assert round(relative_x_height, 2) == 0.97, relative_x_height

    # And the reading measure holds 85 columns of it.
    columns = int(_MEASURE_EM / (ratio * mono_advance))
    assert columns == 85, columns

    # The small and tiny rungs derive from the mono rung, so a host that retunes it
    # through --kpress-host-font-size-mono keeps the proportions between the three.
    for rung in ("small", "tiny"):
        assert f"--kpress-font-size-mono-{rung}: calc(var(--kpress-font-size-mono)" in css, rung
