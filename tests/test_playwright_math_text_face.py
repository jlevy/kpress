"""Real-browser regression for the math text face.

The feature routes the Latin letters and digits inside KaTeX mathematics to the
reading face through the ``KPress Math Text`` composite (see kpress-design.md
"Math Text Face"), and hands KaTeX the reading face's metrics before it renders.
Neither can be checked without a real cascade and real glyphs: which face drew a
glyph shows only in its advance, and whether KaTeX's boxes fit the glyphs shows
only in a layout.

Three invariants, each measured on a rendered page:

- a digit inside math advances by PT Serif's 0.533em rather than KaTeX_Main's
  0.500em, and reverts when the document opts out (``format.math_text_font:
  katex``) and when the reader's persisted font set is ``system``, which the
  pre-paint bootstrap stamps on ``<html>`` and which loads no reading face;
- a display fraction is laid out for the taller PT Serif digits: KaTeX sizes the
  fraction's vertical list from its metric table, so the list is taller with the
  reading face's table installed than with KaTeX's own, which is what the metrics
  asset buys and what a CSS-only swap would leave undone;
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
from typing import TypedDict, cast

import pytest

from kpress.publish import build_site

#: Advance width of the digit glyphs, per em, in the two faces a digit can come
#: from. PT Serif's tabular figures are 533 units; KaTeX_Main's are 500.
PT_SERIF_DIGIT_ADVANCE = 0.533
KATEX_DIGIT_ADVANCE = 0.500


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


@contextmanager
def _serve(public: Path) -> Generator[str]:
    """Serve a built site on a loopback port, so the page loads its assets as a
    browser would rather than over ``file:``."""
    handler = partial(_QuietHandler, directory=str(public))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _build_fixture_site(tmp_path: Path, *, math_text_font: str | None) -> Path:
    (tmp_path / "content").mkdir(parents=True)
    (tmp_path / "content" / "index.md").write_text(
        "# Math text face smoke\n\n"
        "Stromquist settled $s(10) = 3 + 1/\\sqrt{2}$ in 2003, and the mass is\n\n"
        "$$\\mu(Q) = \\frac{4001}{4000} = 1.00025.$$\n",
        encoding="utf-8",
    )
    fmt = "" if math_text_font is None else f"format:\n  math_text_font: {math_text_font}\n"
    (tmp_path / "kpress.yml").write_text(
        "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n" + fmt,
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
    with _serve(public) as url, sync_api.sync_playwright() as playwright:
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
            page.goto(url)
            page.wait_for_selector('[data-kpress-math-rendered="true"]', timeout=30_000)
            page.evaluate("document.fonts.ready")
            return cast(Probe, page.evaluate(_PROBE))
        finally:
            browser.close()


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


#: Recorded from the moment the page starts, before any of its own scripts run:
#: when the first `.katex` node was inserted, and when each `@font-face` in
#: `document.fonts` finished loading. Every face is watched as soon as it enters
#: the set, while its `loaded` promise is still pending, so the time recorded is
#: when the load settled and not when the probe happened to look -- an
#: `requestAnimationFrame` poll would be a whole blocked frame late, and KaTeX
#: blocks the frame it renders in.
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
  const watch = () => {
    document.fonts.forEach((face) => {
      if (watched.has(face)) return;
      watched.add(face);
      const record = {
        family: face.family,
        style: face.style,
        weight: face.weight,
        unicodeRange: face.unicodeRange,
        loaded: null,
      };
      probe.faces.push(record);
      face.loaded.then(
        () => {
          record.loaded = performance.now();
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


class PaintProbe(TypedDict):
    """When the first typeset expression reached the DOM, against the faces."""

    firstKatex: float | None
    faces: list[FaceTiming]


#: The families the mathematics is drawn from: the composite, and the two KaTeX
#: families every rule in katex-text-face.css names after it (and that draw the
#: letters and digits themselves when the face is off).
TEXT_FACE_FAMILY = "KPress Math Text"
KATEX_MATH_FAMILIES = ("KaTeX_Main", "KaTeX_Math")


def _paint_probe(tmp_path: Path, math_text_font: str | None) -> PaintProbe:
    sync_api = pytest.importorskip("playwright.sync_api")
    public = _build_fixture_site(tmp_path, math_text_font=math_text_font)
    with _serve(public) as url, sync_api.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except sync_api.Error:
            try:
                browser = playwright.chromium.launch(headless=True, channel="chrome")
            except sync_api.Error as exc:
                pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")
        try:
            context = browser.new_context(viewport={"width": 900, "height": 900})
            context.add_init_script(_PAINT_PROBE_INIT)
            page = context.new_page()
            page.goto(url)
            page.wait_for_selector('[data-kpress-math-rendered="true"]', timeout=30_000)
            page.evaluate("document.fonts.ready")
            return cast(PaintProbe, page.evaluate("globalThis.__kpressPaintProbe"))
        finally:
            browser.close()


def _faces(probe: PaintProbe, family: str) -> list[FaceTiming]:
    return [face for face in probe["faces"] if face["family"] == family]


def test_math_paints_once_in_its_final_faces(tmp_path: Path) -> None:
    """No expression reaches the page before the faces that draw it.

    KaTeX renders into the live DOM, so an expression is painted in whatever
    faces have decoded by then; the composite's slots are separate `@font-face`
    rules from the prose PT Serif and are fetched only when a formula first asks
    for them. Rendering first therefore paints the letters and digits in the next
    family of the stack and repaints them from the reading face a moment later,
    which reads as the digits in every formula changing font. `katex-init.js`
    loads the faces the mode will use and renders after they settle.

    Relative times only, so the assertion is the ordering and not this machine's
    speed.
    """
    default = _paint_probe(tmp_path / "prose", None)
    first = default["firstKatex"]
    assert first is not None, "no .katex node was ever inserted"

    composite = _faces(default, TEXT_FACE_FAMILY)
    # Four slots, each two faces: the reading face and the KaTeX face for Greek.
    assert len(composite) == 8
    for face in composite + [
        face for family in KATEX_MATH_FAMILIES for face in _faces(default, family)
    ]:
        loaded = face["loaded"]
        assert loaded is not None, f"{face} never loaded"
        assert loaded <= first, f"{face} loaded {loaded - first:.1f}ms after the first .katex"

    # The opt-out mode uses none of the composite, and waits on none of it: the
    # KaTeX faces it does draw from are ready before the first expression.
    katex = _paint_probe(tmp_path / "katex", "katex")
    katex_first = katex["firstKatex"]
    assert katex_first is not None, "no .katex node was ever inserted"
    assert [face for face in _faces(katex, TEXT_FACE_FAMILY) if face["loaded"] is not None] == []
    for family in KATEX_MATH_FAMILIES:
        for face in _faces(katex, family):
            loaded = face["loaded"]
            assert loaded is not None, f"{face} never loaded"
            assert loaded <= katex_first, f"{face} loaded after the first .katex"
