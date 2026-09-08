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

import pytest
from fontTools.ttLib import TTFont

from devtools.subset_mono import CSS, DEFAULT_SOURCE, FAMILY, FONTS, SOURCES, check
from kpress.errors import KPressInvalidRequestError, KPressPublishError
from kpress.format import DocumentInput, RenderOptions, render_page
from kpress.format.assets import (
    MONO_FONT_ASSETS,
    MONO_REQUIRED_STYLES,
    mono_synthesis_gaps,
    mono_weight_order,
    package_asset_manifest,
    package_asset_refs,
)
from kpress.format.model import DEFAULT_MONO_WEIGHTS, MONO_WEIGHT_ORDER, MonoWeight
from kpress.publish.config import FormatConfig, KPressConfig, validate_config

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


def test_the_generator_agrees_with_the_shipped_files(capsys: pytest.CaptureFixture[str]) -> None:
    """The same gate ``make lint-check`` runs, so a stale asset fails the suite too.

    Which of the two checks this is depends on the machine: with the upstream faces
    fetched it rebuilds every subset and compares byte for byte, and without them it
    only hashes the shipped files against their recorded digests. Both are worth
    running, but they are not the same assertion, so the mode is read back out of the
    tool's own output rather than left ambiguous -- a green line here meant one thing
    on a developer's machine and a weaker thing in CI, and nothing said which.
    """
    assert check() == 0
    # The first line carries the verdict and names its mode. Later lines may mention the
    # other mode -- the pinned-hash path ends by saying how to reach the fresh-subset
    # one -- so the verdict line is the one to read.
    verdict = capsys.readouterr().out.splitlines()[0]
    fetched = DEFAULT_SOURCE.is_dir() and any(DEFAULT_SOURCE.glob("PlanetaireMonoText-*.woff2"))
    expected = "[fresh-subset]" if fetched else "[pinned-hash]"
    assert verdict.startswith(expected), verdict


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


def test_the_default_declares_its_four_faces_and_nothing_else() -> None:
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


def _config(weights: tuple[MonoWeight, ...], mono_font: str) -> KPressConfig:
    """A programmatic config carrying one mono setting, as a host would build it."""
    return KPressConfig(format=FormatConfig(mono_font=cast("Any", mono_font), mono_weights=weights))


def test_the_default_declares_every_style_the_stylesheets_ask_for() -> None:
    """Nothing KPress's own CSS asks for is left for the browser to invent.

    `syntax.css` sets comment tokens italic and preprocessor and docstring tokens
    italic AND 700, so all four styles are reachable from default markup. A style a
    rule asks for and the document does not declare is not absent from the page: the
    browser synthesizes it, which on the weight axis puts `/Type3` outlines in an
    exported PDF and on the slant axis leans about 3 degrees steeper than the drawn
    italic. Declaring a face is not loading it -- a prose page with no code fetches
    none of the four -- so the default covers the demand instead of trading against it.

    This fails if the highlighter grows a demand the default does not answer.
    """
    syntax = (_STATIC / "css" / "syntax.css").read_text(encoding="utf-8")
    assert "font-style: italic;" in syntax
    assert set(MONO_REQUIRED_STYLES) <= set(DEFAULT_MONO_WEIGHTS)
    assert not mono_synthesis_gaps(DEFAULT_MONO_WEIGHTS)
    # The three additive weights stay opt-in: nothing packaged asks for them.
    assert set(DEFAULT_MONO_WEIGHTS) < set(MONO_FONT_ASSETS)


#: Sets measured to leave a demand the packaged stylesheets make unanswered. The
#: weight-axis ones put `/Type3` in the PDF. Shared by the two surfaces that take the
#: setting, because the point of the gate is that they agree.
_SYNTHESIZING_SETS: tuple[tuple[MonoWeight, ...], ...] = (
    ("regular",),
    ("regular", "bold"),
    ("regular", "italic"),
    ("regular", "bold", "italic"),
    ("medium", "bold"),
    (),
)

#: Sets a host may legally declare: the four the stylesheets ask for, plus any of the
#: three additive weights nothing packaged reaches for.
_ADMISSIBLE_SETS: tuple[tuple[MonoWeight, ...], ...] = (
    DEFAULT_MONO_WEIGHTS,
    (*DEFAULT_MONO_WEIGHTS, "medium"),
    MONO_WEIGHT_ORDER,
)


def test_a_set_that_would_synthesize_a_style_is_refused() -> None:
    """The trap this closes: a legal-looking set that silently prints outlines.

    Each of these was measured to leave a demand unanswered, and the weight-axis ones
    put `/Type3` in the PDF. `mono_font: system` declares no face at all, so it is the
    supported way to ship none rather than a set that ships some.
    """
    for weights in _SYNTHESIZING_SETS:
        assert mono_synthesis_gaps(weights), weights
        with pytest.raises(KPressPublishError, match="mono_weights"):
            _ = validate_config(_config(weights, "planetaire"))
        # Ignored under `system`, which is what "ship no face" actually looks like.
        # The value still normalizes to declaration order, as it does everywhere.
        assert validate_config(_config(weights, "system")).format.mono_weights == tuple(
            name for name in MONO_WEIGHT_ORDER if name in set(weights)
        )


def test_render_options_refuses_the_same_sets_the_config_refuses() -> None:
    """The Python API is the other surface that takes the setting, and it gates too.

    The check lived only in `publish/config.py`, so the documented guarantee held for
    `kpress build --config` and not for `RenderOptions`, which every other entry point
    -- `export_document`, a render request, an embedding host's own call -- builds. A
    set that reached a render unchecked shipped the outlines the gate exists to
    prevent, which is how the verification that found this produced its `/Type3`
    measurements.
    """
    for weights in _SYNTHESIZING_SETS:
        with pytest.raises(KPressInvalidRequestError, match="mono_weights"):
            _ = RenderOptions(mono_weights=weights)
        # `system` declares no Planetaire face, so nothing can be synthesized from one.
        assert RenderOptions(mono_font="system", mono_weights=weights).mono_weights == weights
    for weights in _ADMISSIBLE_SETS:
        assert RenderOptions(mono_weights=weights).mono_weights == weights


def test_both_surfaces_refuse_in_the_same_words() -> None:
    """One message, so a host that meets the refusal once recognizes it anywhere.

    Only the two setting names differ -- `format.mono_weights` in YAML against
    `mono_weights` on the dataclass -- because a message that named the YAML key at the
    Python API would send a host looking for a config file it does not have.
    """
    for weights in _SYNTHESIZING_SETS:
        with pytest.raises(KPressPublishError) as from_config:
            _ = validate_config(_config(weights, "planetaire"))
        with pytest.raises(KPressInvalidRequestError) as from_options:
            _ = RenderOptions(mono_weights=weights)
        yaml_worded = str(from_config.value)
        assert str(from_options.value) == yaml_worded.replace("format.mono", "mono")
        # The part that tells a host what to fix is present verbatim in both.
        assert "no declared face answers" in yaml_worded, yaml_worded


def test_an_unknown_style_name_says_which_names_are_valid() -> None:
    """A typo should not send a host to the source to find the vocabulary."""
    with pytest.raises(ValueError, match="expected one of"):
        _ = mono_weight_order(cast("list[MonoWeight]", ["semi-bold"]))
    with pytest.raises(KPressPublishError, match="expected one of"):
        _ = validate_config(_config(cast("tuple[MonoWeight, ...]", ("semi-bold",)), "planetaire"))
    # And the Python API says the same thing rather than accepting the typo.
    with pytest.raises(ValueError, match="expected one of"):
        _ = RenderOptions(mono_weights=cast("tuple[MonoWeight, ...]", ("semi-bold",)))


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
    for weight in DEFAULT_MONO_WEIGHTS:
        assert MONO_FONT_ASSETS[weight][0].removeprefix("css/") in default, weight
    # And the three additive weights, which nothing packaged asks for, stay out.
    assert "mono-planetaire-500-normal.css" not in default
    assert "mono-planetaire-600-normal.css" not in default
    assert "mono-planetaire-800-normal.css" not in default

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
    assert "--kpress-mono-stack-platform" in override
    # font_mode="system" is the other way to ask for the platform mono, and it has to
    # cover code now that code is a shipped face rather than the platform's own.
    font_mode = css.split('.kpress[data-kpress-fonts="system"]', 1)[1].split("}", 1)[0]
    assert "--kpress-font-mono:" in font_mode

    # The platform stack is written once and read three times. Three hand-copied
    # stacks drift, and this is the token that stops them.
    assert css.count("ui-monospace") == 1, "the platform mono stack is duplicated again"
    stack = css.split("--kpress-mono-stack-platform:", 1)[1].split(";", 1)[0]
    assert "ui-monospace" in stack and "monospace" in stack

    # Every rule that sets --kpress-font-mono reads the host hook first, the reader's
    # system-font toggle included: a documented public seam must not stop working on a
    # control the reader owns. Before this, that block set a bare stack and the host's
    # chosen face was discarded the moment a reader flipped system fonts on.
    for declaration in re.findall(r"--kpress-font-mono:([^;]+);", css):
        assert "var(--kpress-host-font-mono," in re.sub(r"\s+", "", declaration), declaration
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

    # And the reading measure holds 85 columns of it: 45 / (0.87 x 0.602) = 85.9, and
    # a column is not divisible, so the floor is the number that fits.
    exact_columns = _MEASURE_EM / (ratio * mono_advance)
    assert round(exact_columns, 2) == 85.92, exact_columns
    assert int(exact_columns) == 85, exact_columns

    # The small and tiny rungs derive from the mono rung, so a host that retunes it
    # through --kpress-host-font-size-mono keeps the proportions between the three.
    for rung in ("small", "tiny"):
        assert f"--kpress-font-size-mono-{rung}: calc(var(--kpress-font-size-mono)" in css, rung

    # And they hold the same ratio the mono rung does, which is the whole claim the
    # three-rung ramp makes. The two ramps pair by index, so each mono multiplier is
    # its prose partner's own step and the ratio collapses to 0.87 in every rung. Left
    # unchecked, these were 0.915 and 0.855 -- the pre-Planetaire absolutes rescaled --
    # which put small and tiny at 99% and 98% of the prose x-height beside them while
    # the rung above sat at 97%. Nothing failed, because nothing measured them.
    for rung, prose_step in (("small", 0.9), ("tiny", 0.85)):
        found = re.search(
            rf"--kpress-font-size-mono-{rung}:\s*calc\(var\(--kpress-font-size-mono\) \* ([\d.]+)\)",
            re.sub(r"\s+", " ", css),
        )
        assert found is not None, rung
        rung_parity = (ratio * float(found.group(1)) * mono_x) / (prose_step * prose_x)
        assert round(rung_parity, 4) == round(relative_x_height, 4), (rung, rung_parity)
