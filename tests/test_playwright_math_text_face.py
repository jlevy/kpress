"""Real-browser regression for the math text face.

The feature routes the Latin letters and digits inside KaTeX mathematics to the
reading face through the ``KPress Math Text`` composite (see kpress-design.md
"Math Text Face"), and hands KaTeX the reading face's metrics before it renders.
Neither can be checked without a real cascade and real glyphs: which face drew a
glyph shows only in its advance, and whether KaTeX's boxes fit the glyphs shows
only in a layout.

The invariants, each measured on a rendered page:

- a digit inside math advances by PT Serif's 0.533em rather than KaTeX_Main's
  0.500em, and reverts when the document opts out (``format.math_text_font:
  katex``) and when the reader's persisted font set is ``system``, which the
  pre-paint bootstrap stamps on ``<html>`` and which loads no reading face;
- a display fraction is laid out for the taller PT Serif digits: KaTeX sizes the
  fraction's vertical list from its metric table, so the list is taller with the
  reading face's table installed than with KaTeX's own, which is what the metrics
  asset buys and what a CSS-only swap would leave undone;
- ``\\mathit`` Greek is drawn and laid out by the same face: its slot draws with
  KaTeX_Math-Italic, so its table's Greek advances and accent skews have to be
  that face's rows, not the Main-Italic rows KaTeX would otherwise supply;
- ``\\textrm{\\textit{...}}`` stays italic, in both nesting orders and with bold:
  KaTeX emits one leaf for the pair and lays it out from the italic table;
- the reader's font-set chooser carries typeset mathematics with it, in both
  directions, and a footnote preview -- a clone mounted outside ``.kpress`` --
  keeps the mode and the size of the document it was opened from;
- an opt-out stamped directly on the wrapper reaches the stylesheet as well as
  the script, so the composite family and the metrics can never disagree;
- the mathematics paints once: every face the mode draws from has finished
  loading before the first typeset expression reaches the DOM, so no formula is
  painted in a fallback and repainted in the reading face.
"""

from __future__ import annotations

import threading
from collections.abc import Generator
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, TypedDict, cast

import pytest

from devtools.katex_text_metrics import ASSET_PATH, parse_asset
from kpress.publish import build_site

#: Advance width of the digit glyphs, per em, in the two faces a digit can come
#: from. PT Serif's tabular figures are 533 units; KaTeX_Main's are 500.
PT_SERIF_DIGIT_ADVANCE = 0.533
KATEX_DIGIT_ADVANCE = 0.500


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


DEFAULT_MARKDOWN = (
    "# Math text face smoke\n\n"
    "Stromquist settled $s(10) = 3 + 1/\\sqrt{2}$ in 2003, and the mass is\n\n"
    "$$\\mu(Q) = \\frac{4001}{4000} = 1.00025.$$\n"
)


def _build_fixture_site(
    tmp_path: Path,
    *,
    math_text_font: str | None,
    markdown: str = DEFAULT_MARKDOWN,
    choosers: str | None = None,
) -> Path:
    (tmp_path / "content").mkdir(parents=True)
    (tmp_path / "content" / "index.md").write_text(markdown, encoding="utf-8")
    fmt = "" if math_text_font is None else f"  math_text_font: {math_text_font}\n"
    if choosers is not None:
        fmt += f"  widgets:\n    settings:\n      choosers: [{choosers}]\n"
    (tmp_path / "kpress.yml").write_text(
        "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n"
        + (f"format:\n{fmt}" if fmt else ""),
        encoding="utf-8",
    )
    build_site(tmp_path / "kpress.yml")
    return tmp_path / "public"


class Probe(TypedDict):
    """What the page reports once KaTeX has typeset it."""

    advance: float
    family: str
    fractionHeightEm: float
    rendered: int


#: Measured once KaTeX has typeset: the advance of the first digit glyph inside
#: inline math as a fraction of the math font size, and the height KaTeX gave the
#: display fraction's vertical list, in em, which it computes from its metric
#: table for the numerator and denominator glyphs.
_PROBE = """(() => {
  const inline = document.querySelector('.kpress-math-inline .katex');
  const digit = [...inline.querySelectorAll('.mord')].find(
    (el) => /^[0-9]$/.test(el.textContent) && el.children.length === 0
  );
  const size = parseFloat(getComputedStyle(digit).fontSize);
  const fraction = document.querySelector('.katex-display .mfrac .vlist');
  return {
    advance: digit.getBoundingClientRect().width / size,
    family: getComputedStyle(digit).fontFamily,
    fractionHeightEm: parseFloat(fraction.style.height),
    rendered: document.querySelectorAll('[data-kpress-math-rendered="true"]').length,
  };
})()"""

#: How much taller KaTeX's vertical list for `4001/4000` comes out with PT Serif's
#: metrics installed than with Computer Modern's: the digits are 0.046em taller
#: (0.712 against 0.664), and the fraction's shift rules add a little on top.
#: Bounded on both sides, so a metrics asset that never applied (zero) and one
#: that applied something wild both fail.
FRACTION_GROWTH_EM = (0.03, 0.15)


def _probe(tmp_path: Path, math_text_font: str | None, *, font_set: str | None = None) -> Probe:
    sync_api = pytest.importorskip("playwright.sync_api")
    public = _build_fixture_site(tmp_path, math_text_font=math_text_font)
    handler = partial(_QuietHandler, directory=str(public))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_api.sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
            except sync_api.Error:
                try:
                    browser = playwright.chromium.launch(headless=True, channel="chrome")
                except sync_api.Error as exc:
                    pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")
            try:
                context = browser.new_context(viewport={"width": 900, "height": 900})
                if font_set is not None:
                    # What theme-bootstrap.js reads before first paint.
                    context.add_init_script(f"localStorage.setItem('kpress.fontSet', '{font_set}')")
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                page.wait_for_selector('[data-kpress-math-rendered="true"]', timeout=30_000)
                page.evaluate("document.fonts.ready")
                return cast(Probe, page.evaluate(_PROBE))
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_reading_face_draws_and_lays_out_the_digits(tmp_path: Path) -> None:
    default = _probe(tmp_path / "prose", None)
    katex = _probe(tmp_path / "katex", "katex")
    for probe in (default, katex):
        assert probe["rendered"] == 2

    # Drawn: the digit advances by PT Serif's width by default and by
    # KaTeX_Main's when the document opts out.
    assert "KPress Math Text" in default["family"]
    assert default["advance"] == pytest.approx(PT_SERIF_DIGIT_ADVANCE, abs=0.01)
    assert katex["advance"] == pytest.approx(KATEX_DIGIT_ADVANCE, abs=0.01)

    # The reader's persisted system font set opts out too, faces and metrics alike.
    system = _probe(tmp_path / "system", None, font_set="system")
    assert system["rendered"] == 2
    assert system["advance"] == pytest.approx(KATEX_DIGIT_ADVANCE, abs=0.01)
    assert system["fractionHeightEm"] == pytest.approx(katex["fractionHeightEm"], abs=0.001)

    # Laid out: the metrics asset makes KaTeX size the fraction for the glyphs
    # it now draws, so the vertical list is taller than the opt-out's.
    growth = default["fractionHeightEm"] - katex["fractionHeightEm"]
    low, high = FRACTION_GROWTH_EM
    assert low <= growth <= high, (default["fractionHeightEm"], katex["fractionHeightEm"])


# ---- The `\mathit` slot, the `\textrm` slot, the chooser and the preview overlay ----


def _serve(public: Path) -> tuple[ThreadingHTTPServer, threading.Thread]:
    handler = partial(_QuietHandler, directory=str(public))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _launch(playwright: Any, sync_api: Any) -> Any:
    try:
        return playwright.chromium.launch(headless=True)
    except sync_api.Error:
        try:
            return playwright.chromium.launch(headless=True, channel="chrome")
        except sync_api.Error as exc:
            pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")


@contextmanager
def _served_page(public: Path) -> Generator[Any]:
    """One built site, one browser, one loaded page: the probes are cheap, the setup is not."""
    sync_api = pytest.importorskip("playwright.sync_api")
    server, thread = _serve(public)
    try:
        with sync_api.sync_playwright() as playwright:
            browser = _launch(playwright, sync_api)
            try:
                context = browser.new_context(viewport={"width": 1100, "height": 900})
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                page.wait_for_selector('[data-kpress-math-rendered="true"]', timeout=30_000)
                page.evaluate("document.fonts.ready")
                yield page
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _asset_row(face: str, code_point: int) -> list[float]:
    """One row of the shipped metric table: what KaTeX is told the glyph measures."""
    table = cast("dict[str, dict[str, list[float]]]", parse_asset(ASSET_PATH.read_text("utf-8")))
    return table[face][str(code_point)]


#: `\mathit` Greek, as the shipped Main-Italic table now describes it. The rows come
#: from KaTeX_Math-Italic, the face the composite's italic slot actually draws them
#: with; Main-Italic's own rows, which this table used to be scaled from, put Upsilon
#: on a 0.88166em advance and give Gamma no skew at all.
UPSILON_WIDTH_EM = _asset_row("Main-Italic", 0x3A5)[4]
GAMMA_SKEW_EM = _asset_row("Main-Italic", 0x393)[3]
#: Half the `^` advance: KaTeX centres an accent by `skew - width/2` (an inline
#: `left` on `.accent-body`), so the skew row is directly readable off the page.
HAT_HALF_WIDTH_EM = _asset_row("Main-Regular", 0x5E)[4] / 2
#: What a Main-Italic-sourced table would have produced instead.
UNSCALED_MAIN_ITALIC_UPSILON_EM = 0.88166

_GREEK_MARKDOWN = (
    "# Greek and nested text styles\n\n"
    "Capital $\\mathit{\\Upsilon}$, accented $\\hat{\\mathit{\\Gamma}}$.\n\n"
    "Nested $\\textrm{\\textit{n123}}$, $\\textit{\\textrm{n123}}$ and "
    "$\\textrm{\\textbf{\\textit{n123}}}$.\n"
)

#: Advance of the `\mathit` Upsilon and the inline `left` KaTeX gives the accent
#: over `\hat{\mathit{\Gamma}}`, plus every `\text...` leaf's resolved style.
_GREEK_PROBE = """(() => {
  const em = (el, px) => px / parseFloat(getComputedStyle(el).fontSize);
  const upsilon = [...document.querySelectorAll('.katex .mathit')].find(
    (el) => el.textContent === '\\u03a5'
  );
  const accent = document.querySelector('.katex .accent-body');
  return {
    upsilonAdvance: em(upsilon, upsilon.getBoundingClientRect().width),
    accentLeftEm: parseFloat(accent.style.left),
    textLeaves: [...document.querySelectorAll('.katex .textrm, .katex .textbf')]
      .filter((el) => el.textContent === 'n123')
      .map((el) => ({
        cls: el.className,
        style: getComputedStyle(el).fontStyle,
        advance: em(el, el.getBoundingClientRect().width),
      })),
  };
})()"""


def test_mathit_greek_is_drawn_and_laid_out_by_the_same_face(tmp_path: Path) -> None:
    """The `\\mathit` slot draws its Greek with KaTeX_Math-Italic, so its table must too.

    `\\mathit` is laid out from KaTeX's Main-Italic table but the composite's italic
    slot claims U+0370-03FF for KaTeX_Math-Italic, and the two faces disagree about
    both advance and skew. A table scaled from Main-Italic measures Upsilon a fifth
    of an em wider than the browser draws it and centres the accent over
    `\\hat{\\mathit{\\Gamma}}` about a tenth of an em off the glyph.
    """
    public = _build_fixture_site(tmp_path, math_text_font=None, markdown=_GREEK_MARKDOWN)
    with _served_page(public) as page:
        probe = cast("dict[str, Any]", page.evaluate(_GREEK_PROBE))

    # Drawn advance and shipped table row agree, and neither is Main-Italic's own.
    assert probe["upsilonAdvance"] == pytest.approx(UPSILON_WIDTH_EM, abs=0.005)
    assert probe["upsilonAdvance"] < UNSCALED_MAIN_ITALIC_UPSILON_EM - 0.1

    # The accent sits at the drawn face's skew, not at the zero Main-Italic reports.
    assert probe["accentLeftEm"] == pytest.approx(GAMMA_SKEW_EM - HAT_HALF_WIDTH_EM, abs=0.001)
    assert probe["accentLeftEm"] > -HAT_HALF_WIDTH_EM + 0.05


def test_textrm_does_not_suppress_an_explicit_nested_italic(tmp_path: Path) -> None:
    """`\\textrm{\\textit{n}}` is one `.mord.textrm.textit` leaf and stays italic.

    KaTeX lays the run out from the italic table either way, so pinning the upright
    slot on `.textrm` would draw one face over another's metrics. Both nesting
    orders and the bold combination collapse onto the same leaf, so one fixture
    covers all three.
    """
    public = _build_fixture_site(tmp_path, math_text_font=None, markdown=_GREEK_MARKDOWN)
    with _served_page(public) as page:
        probe = cast("dict[str, Any]", page.evaluate(_GREEK_PROBE))

    leaves = probe["textLeaves"]
    assert [leaf["cls"] for leaf in leaves] == [
        "mord textrm textit",
        "mord textrm textit",
        "mord textrm textbf textit",
    ]
    for leaf in leaves:
        assert leaf["style"] == "italic", leaf
    # The italic advance, not the upright 2.193em the pinned rule produced.
    assert leaves[0]["advance"] == pytest.approx(2.085, abs=0.01)
    assert leaves[2]["advance"] > leaves[0]["advance"], (
        "the bold combination is bolder, not upright"
    )


_FOOTNOTE_MARKDOWN = (
    "# Previews and the reader's font set\n\n"
    "Stromquist settled $s(10) = 3 + 1/\\sqrt{2}$ in 2003, and the mass is "
    "$\\frac{4001}{4000}$, repeated in a footnote[^mass].\n\n"
    "[^mass]: The mass is $\\frac{4001}{4000}$ exactly.\n"
)

#: The same expression twice, because the two are set in different composites: prose
#: takes the reading face, and a footnote is a sans role, so it takes `KPress Math Text
#: Sans` (see katex-text-face.css). The reading face is therefore read where the reading
#: face is, and the overlay -- a clone of the FOOTNOTE -- is compared against the
#: footnote it was cloned from rather than against prose.
PROSE_SCOPE = ".kpress-prose > p"
FOOTNOTE_SCOPE = ".kpress-footnotes"

#: Source Sans 3 sets its digits on 0.497em, which is 0.003 from KaTeX_Main's 0.500 and
#: so cannot tell a mode change apart on its own; that is the whole reason the document
#: reading below is taken in prose.
SOURCE_SANS_DIGIT_ADVANCE = 0.497

#: One reading of a math host: the advance of its `4001` digit run per em, whether the
#: composite family drew it, and the ratio the KaTeX root was sized at against the prose
#: around it. `scope` is either the document or the preview overlay, which must report
#: the same three; the ratio rather than the size, because a preview sets its own prose
#: a little smaller and it is the lift over that prose which has to match.
_MODE_PROBE = """((selector) => {
  const scope = document.querySelector(selector);
  const digits = [...scope.querySelectorAll('.katex .mord')].find(
    (el) => el.textContent === '4001' && el.children.length === 0
  );
  const style = getComputedStyle(digits);
  const katex = scope.querySelector('.katex');
  return {
    advancePerDigit: digits.getBoundingClientRect().width / parseFloat(style.fontSize) / 4,
    composite: style.fontFamily.includes('KPress Math Text'),
    katexSizeRatio:
      parseFloat(getComputedStyle(katex).fontSize) /
      parseFloat(getComputedStyle(katex.parentElement).fontSize),
    mathText: scope.getAttribute('data-kpress-math-text'),
  };
})"""


def _open_preview(page: Any) -> dict[str, Any]:
    page.locator("a[data-kpress-footnote-ref]").first.hover()
    page.wait_for_selector(".kpress-tooltip", state="visible", timeout=5_000)
    page.evaluate("document.fonts.ready")
    probe = cast("dict[str, Any]", page.evaluate(_MODE_PROBE, ".kpress-tooltip"))
    page.keyboard.press("Escape")
    return probe


def _choose_font_set(page: Any, value: str) -> None:
    page.locator(".kpress-settings-btn").first.click()
    page.select_option("select.kpress-menu-select", value)
    page.wait_for_selector('[data-kpress-math-rendered="true"]', timeout=30_000)
    page.evaluate("document.fonts.ready")


def test_the_font_set_chooser_carries_math_and_previews_with_it(tmp_path: Path) -> None:
    """Both directions through the real chooser, and the preview overlay with them.

    The chooser flips CSS instantly, but KaTeX was handed its metric tables once,
    at load, so the switch is completed by a reload into the persisted choice (see
    `fontSetSwitchNeedsReload` in settings-widget.js). Whatever mode the page ends
    up in, the footnote preview -- a clone mounted outside `.kpress` -- has to be
    drawn and sized in it too, or its glyphs sit in boxes measured for the others.

    The clone comes from a footnote, which is a sans role, so the overlay is measured
    against the footnote rather than against prose: matching prose would be the wrong
    invariant and would put PT Serif glyphs on boxes measured for Source Sans.
    """
    public = _build_fixture_site(
        tmp_path,
        math_text_font=None,
        markdown=_FOOTNOTE_MARKDOWN,
        choosers="theme, font-set",
    )
    with _served_page(public) as page:
        custom = cast("dict[str, Any]", page.evaluate(_MODE_PROBE, PROSE_SCOPE))
        custom_note = cast("dict[str, Any]", page.evaluate(_MODE_PROBE, FOOTNOTE_SCOPE))
        custom_preview = _open_preview(page)

        _choose_font_set(page, "system")
        system = cast("dict[str, Any]", page.evaluate(_MODE_PROBE, PROSE_SCOPE))
        system_note = cast("dict[str, Any]", page.evaluate(_MODE_PROBE, FOOTNOTE_SCOPE))
        system_preview = _open_preview(page)
        persisted = page.evaluate("localStorage.getItem('kpress.fontSet')")

        _choose_font_set(page, "custom")
        back = cast("dict[str, Any]", page.evaluate(_MODE_PROBE, PROSE_SCOPE))

    # The document: the reader's choice reaches the glyphs, not only the stylesheet.
    assert custom["advancePerDigit"] == pytest.approx(PT_SERIF_DIGIT_ADVANCE, abs=0.01)
    assert custom["composite"]
    assert system["advancePerDigit"] == pytest.approx(KATEX_DIGIT_ADVANCE, abs=0.01)
    assert not system["composite"]
    assert persisted == "system"
    assert back["advancePerDigit"] == pytest.approx(PT_SERIF_DIGIT_ADVANCE, abs=0.01)
    assert back["composite"]

    # The footnote follows the same switch, in the sans composite rather than the serif.
    assert custom_note["advancePerDigit"] == pytest.approx(SOURCE_SANS_DIGIT_ADVANCE, abs=0.01)
    assert custom_note["composite"]
    assert not system_note["composite"]

    # The size follows too: the reading face needs no lift, KaTeX's own does.
    assert custom["katexSizeRatio"] == pytest.approx(1.0, abs=0.01)
    assert system["katexSizeRatio"] == pytest.approx(1.05, abs=0.01)

    # The overlay carries the mode of the document it was opened from and the metrics of
    # the footnote it was cloned from, in both modes.
    for document_probe, note, preview in (
        (custom, custom_note, custom_preview),
        (system, system_note, system_preview),
    ):
        assert preview["mathText"] == ("prose" if document_probe["composite"] else "katex")
        assert preview["composite"] is document_probe["composite"]
        assert preview["advancePerDigit"] == pytest.approx(note["advancePerDigit"], abs=0.005)
        assert preview["katexSizeRatio"] == pytest.approx(note["katexSizeRatio"], abs=0.01)


def test_a_font_set_stamped_on_the_wrapper_opts_out_of_both_guards(tmp_path: Path) -> None:
    """The CSS scope and the JS guard have to agree wherever the attribute is stamped.

    The built-in producers stamp `data-kpress-font-set` on `<html>`, and katex-init.js
    reads it with `closest()`, which matches the element it starts from. So the
    stylesheet excludes each opt-out bare as well as as an ancestor; otherwise a host
    that stamped the wrapper directly would get the composite family with KaTeX's own
    metrics, which is the one state the design forbids.
    """
    public = _build_fixture_site(tmp_path, math_text_font=None)
    index = public / "index.html"
    stamped = index.read_text(encoding="utf-8").replace(
        'data-kpress-fonts="custom"',
        'data-kpress-fonts="custom" data-kpress-font-set="system"',
        1,
    )
    assert 'data-kpress-font-set="system"' in stamped, "the wrapper markup has moved"
    index.write_text(stamped, encoding="utf-8")

    with _served_page(public) as page:
        probe = cast(Probe, page.evaluate(_PROBE))

    assert probe["rendered"] == 2
    assert "KPress Math Text" not in probe["family"]
    assert probe["advance"] == pytest.approx(KATEX_DIGIT_ADVANCE, abs=0.01)


# ---- The mathematics paints once ----


#: Recorded from the moment the page starts, before any of its own scripts run:
#: when the first `.katex` node was inserted, and when each `@font-face` in
#: `document.fonts` finished loading. Every face is watched as soon as it enters
#: the set, while its `loaded` promise is still pending, so the time recorded is
#: when the load settled and not when the probe happened to look -- an
#: `requestAnimationFrame` poll would be a whole blocked frame late, and KaTeX
#: blocks the frame it renders in.
#:
#: A face is recorded under its IDENTITY -- family, style, weight, unicode-range --
#: and not per `FontFace` object, because a browser may hand out more than one
#: object for the same `@font-face` rule. Chrome on Linux rebuilds the
#: CSS-connected faces when the active stylesheet set changes, so a poll that lands
#: between `katex.min.css` and `katex-text-face.css` catches a whole generation of
#: objects that is then replaced and never loads: on that run `document.fonts`
#: reported the KaTeX faces twice, the first copy pending forever. `objects` counts
#: how many were seen for one identity, and `loaded` is the first of them to load,
#: which is when the face's bytes were in fact ready.
_PAINT_PROBE_INIT = """(() => {
  const probe = { firstKatex: null, faces: [] };
  globalThis.__kpressPaintProbe = probe;

  const mark = (node) => {
    if (probe.firstKatex !== null || node.nodeType !== 1) return;
    if (node.classList.contains("katex") || node.querySelector(".katex")) {
      probe.firstKatex = performance.now();
    }
  };
  new MutationObserver((records) => {
    for (const record of records) for (const node of record.addedNodes) mark(node);
  }).observe(document, { childList: true, subtree: true });

  const watched = new WeakSet();
  const byKey = new Map();
  const watch = () => {
    document.fonts.forEach((face) => {
      if (watched.has(face)) return;
      watched.add(face);
      const key = [face.family, face.style, face.weight, face.unicodeRange].join("|");
      let record = byKey.get(key);
      if (record === undefined) {
        record = {
          family: face.family,
          style: face.style,
          weight: face.weight,
          unicodeRange: face.unicodeRange,
          loaded: null,
          objects: 0,
        };
        byKey.set(key, record);
        probe.faces.push(record);
      }
      record.objects += 1;
      face.loaded.then(
        () => {
          if (record.loaded === null) record.loaded = performance.now();
        },
        () => {},
      );
    });
    setTimeout(watch, 1);
  };
  watch();
})()"""


class FaceTiming(TypedDict):
    """One `@font-face` of the page, and when it finished loading."""

    family: str
    style: str
    weight: str
    unicodeRange: str
    loaded: float | None
    objects: int


class WaitEntry(TypedDict):
    """One request `katex-init.js` made of the font loading API, and its outcome.

    ``request`` is a face key when the init asked for a face it can see in
    ``document.fonts`` and a CSS ``font`` shorthand when it asked the matching
    algorithm for one; ``outcome`` is ``loaded``, ``empty``, ``error`` or (only if
    the three-second deadline beat the loads) ``pending``.
    """

    request: str
    outcome: str
    faces: list[str]


class PaintProbe(TypedDict):
    """When the first typeset expression reached the DOM, against the faces."""

    firstKatex: float | None
    faces: list[FaceTiming]
    wait: list[WaitEntry]


#: The composite family the mathematics is drawn from where the face is on.
TEXT_FACE_FAMILY = "KPress Math Text"

#: The two KaTeX families every rule in katex-text-face.css names after the composite
#: (and that draw the letters and digits themselves when the face is off), against how
#: many `@font-face` rules the pinned bundle declares for each. The init asks for every
#: one of them by name, so a bump that adds or drops a face has to be seen here.
KATEX_FACE_COUNTS = {"KaTeX_Main": 4, "KaTeX_Math": 2}

#: The KaTeX faces every expression on the fixture page is drawn from, whatever it
#: contains: upright `KaTeX_Main` for operators, relations, punctuation and (in the
#: opt-out mode) the letters and digits, and italic `KaTeX_Math` for the variables.
#: The bold and bold-italic faces of either family are only reached by `\mathbf`,
#: `\boldsymbol` and `\textbf`, which this fixture has none of.
REQUIRED_KATEX_FACES = (("KaTeX_Main", "normal", "400"), ("KaTeX_Math", "italic", "400"))

#: The init's own ceiling on the wait (`FACE_WAIT_MS` in katex-init.js), and the bound
#: this test holds the first render to. Every ordering assertion below is relative to
#: `firstKatex`, so a page whose faces never settle satisfies all of them by rendering
#: three seconds late; the bound is what tells that apart from the wait working. Two
#: thirds of the ceiling: far above any real load on any runner, and far enough below
#: 3000 that a render the deadline released cannot land under it. It is the init's
#: constant and not this machine's speed, so it is as platform-independent as the
#: orderings are.
FACE_WAIT_MS = 3000
FACE_WAIT_BOUND_MS = 2000


def _face_key(face: FaceTiming) -> str:
    """The identity `katex-init.js` records a face under (its `faceKey`)."""
    return "|".join((face["family"], face["style"], face["weight"], face["unicodeRange"]))


def _paint_probe(tmp_path: Path, math_text_font: str | None) -> PaintProbe:
    sync_api = pytest.importorskip("playwright.sync_api")
    public = _build_fixture_site(tmp_path, math_text_font=math_text_font)
    server, thread = _serve(public)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    try:
        with sync_api.sync_playwright() as playwright:
            browser = _launch(playwright, sync_api)
            try:
                context = browser.new_context(viewport={"width": 900, "height": 900})
                context.add_init_script(_PAINT_PROBE_INIT)
                page = context.new_page()
                page.goto(url)
                page.wait_for_selector('[data-kpress-math-rendered="true"]', timeout=30_000)
                page.evaluate("document.fonts.ready")
                probe = cast(PaintProbe, page.evaluate("globalThis.__kpressPaintProbe"))
                # The init's own account of the wait, which says which faces it in
                # fact covered; see "PAINTING ONCE" in katex-init.js.
                probe["wait"] = cast(
                    "list[WaitEntry]", page.evaluate("globalThis.kpressMathFaceWait ?? []")
                )
                return probe
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _faces(probe: PaintProbe, family: str) -> list[FaceTiming]:
    return [face for face in probe["faces"] if face["family"] == family]


def _report(probe: PaintProbe) -> str:
    """Everything the page recorded, so a failure here explains itself.

    A browser that loads a different set of faces than the one this machine loads
    is the whole difficulty of this test, and the assertions below cannot say which
    face it was. This can.
    """
    lines = [f"first .katex inserted at {probe['firstKatex']}ms", "the init's font wait:"]
    lines += [
        f"  {entry['outcome']:<7} {entry['request']} -> {entry['faces'] or '(none)'}"
        for entry in probe["wait"]
    ] or ["  (nothing recorded)"]
    lines.append("every @font-face of the page, and when it loaded:")
    lines += [
        f"  {face['loaded']} {_face_key(face)} ({face['objects']} object(s))"
        for face in probe["faces"]
    ]
    return "\n".join(lines)


def _loaded_first(probe: PaintProbe, faces: list[FaceTiming], why: str) -> None:
    """Every one of `faces` finished loading before the first `.katex` node existed."""
    first = probe["firstKatex"]
    assert first is not None
    for face in faces:
        loaded = face["loaded"]
        assert loaded is not None, f"{why}: {_face_key(face)} never loaded\n{_report(probe)}"
        assert loaded <= first, (
            f"{why}: {_face_key(face)} loaded {loaded - first:.1f}ms after the first .katex"
            f"\n{_report(probe)}"
        )


def _settled_before_the_deadline(probe: PaintProbe) -> None:
    """The wait ran to its end rather than being cut short by `FACE_WAIT_MS`.

    Without this the orderings above are satisfied by the failure they exist to
    catch: a face whose `load()` never settles renders the page three seconds late,
    every other face is long since loaded, and each `loaded <= firstKatex` holds. It
    has happened on this branch once already, as `KaTeX_Main normal 700` never
    loading on the Linux runner. The record is where it shows: a request the
    deadline beat is left `pending`, and a render past the bound is the deadline
    having won even where the record cannot say so.
    """
    first = probe["firstKatex"]
    assert first is not None
    pending = [entry for entry in probe["wait"] if entry["outcome"] == "pending"]
    assert pending == [], f"the deadline cut the wait short\n{_report(probe)}"
    assert first < FACE_WAIT_BOUND_MS, (
        f"the first .katex was inserted at {first:.1f}ms, past the {FACE_WAIT_BOUND_MS}ms"
        f" bound on the init's {FACE_WAIT_MS}ms ceiling\n{_report(probe)}"
    )


def _covered(probe: PaintProbe) -> list[FaceTiming]:
    """The faces the init's wait actually covered: the ones its requests matched.

    A request that came back empty, or was rejected, waited on nothing -- it is
    reported by `_report` but it is not a face the fix promises anything about.
    """
    keys = {
        key for entry in probe["wait"] if entry["outcome"] == "loaded" for key in entry["faces"]
    }
    return [face for face in probe["faces"] if _face_key(face) in keys]


def _required(probe: PaintProbe) -> list[FaceTiming]:
    """The KaTeX faces every expression on the fixture page needs."""
    found: list[FaceTiming] = []
    for family, style, weight in REQUIRED_KATEX_FACES:
        matches = [
            face
            for face in _faces(probe, family)
            if face["style"] == style and face["weight"] == weight
        ]
        assert matches, f"no {family} {style} {weight} face on the page\n{_report(probe)}"
        found += matches
    return found


def test_math_paints_once_in_its_final_faces(tmp_path: Path) -> None:
    """No expression reaches the page before the faces that draw it.

    KaTeX renders into the live DOM, so an expression is painted in whatever
    faces have decoded by then; the composite's slots are separate `@font-face`
    rules from the prose PT Serif and are fetched only when a formula first asks
    for them. Rendering first therefore paints the letters and digits in the next
    family of the stack and repaints them from the reading face a moment later,
    which reads as the digits in every formula changing font. `katex-init.js`
    loads the faces the mode will use and renders after they settle.

    Four things are asserted, which is exactly what the wait promises: the
    composite's eight faces are loaded first in the mode that draws from them;
    every face the wait's own record says it covered is loaded first; the two
    KaTeX faces every expression here is drawn from -- upright `KaTeX_Main` and
    italic `KaTeX_Math` -- are loaded first in both modes; and the wait settled
    rather than being released by its own deadline, without which each of the
    other three is satisfied by a page that renders three seconds late. A KaTeX
    face the fixture never asks for and the browser did not load is not a
    failure; the record says which those were.

    Relative times and the init's own ceiling only, so the assertions are the
    ordering and the wait's contract, not this machine's speed.
    """
    default = _paint_probe(tmp_path / "prose", None)
    assert default["firstKatex"] is not None, (
        f"no .katex node was ever inserted\n{_report(default)}"
    )

    # The init asked for every face of both KaTeX families by name, whatever the
    # browser then made of the request.
    for family, count in KATEX_FACE_COUNTS.items():
        asked = [entry for entry in default["wait"] if entry["request"].startswith(f"{family}|")]
        assert len(asked) == count, f"{family} faces asked for: {asked}\n{_report(default)}"

    _settled_before_the_deadline(default)
    composite = _faces(default, TEXT_FACE_FAMILY)
    # Four slots, each two faces: the reading face and the KaTeX face for Greek.
    assert len(composite) == 8, _report(default)
    _loaded_first(default, composite, "the composite the mode draws from")
    _loaded_first(default, _covered(default), "a face the wait covered")
    _loaded_first(default, _required(default), "a face every expression here uses")

    # The opt-out mode uses none of the composite, and waits on none of it: the
    # KaTeX faces it does draw from are ready before the first expression.
    katex = _paint_probe(tmp_path / "katex", "katex")
    assert katex["firstKatex"] is not None, f"no .katex node was ever inserted\n{_report(katex)}"
    assert [face for face in _faces(katex, TEXT_FACE_FAMILY) if face["loaded"] is not None] == [], (
        _report(katex)
    )
    assert [entry for entry in katex["wait"] if TEXT_FACE_FAMILY in entry["request"]] == [], (
        _report(katex)
    )
    _settled_before_the_deadline(katex)
    _loaded_first(katex, _covered(katex), "a face the wait covered")
    _loaded_first(katex, _required(katex), "a face every expression here uses")
