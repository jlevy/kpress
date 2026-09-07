"""Real-browser regression for the math text face.

The feature routes the Latin letters and digits inside KaTeX mathematics to the
reading face through the ``KPress Math Text`` composite (see kpress-design.md
"Math Text Face"), and hands KaTeX the reading face's metrics before it renders.
Neither can be checked without a real cascade and real glyphs: which face drew a
glyph shows only in its advance, and whether KaTeX's boxes fit the glyphs shows
only in a layout.

Two invariants, each measured on a rendered page:

- a digit inside math advances by PT Serif's 0.533em rather than KaTeX_Main's
  0.500em, and reverts when the document opts out (``format.math_text_font:
  katex``) and when the reader's persisted font set is ``system``, which the
  pre-paint bootstrap stamps on ``<html>`` and which loads no reading face;
- a display fraction is laid out for the taller PT Serif digits: KaTeX sizes the
  fraction's vertical list from its metric table, so the list is taller with the
  reading face's table installed than with KaTeX's own, which is what the metrics
  asset buys and what a CSS-only swap would leave undone.
"""

from __future__ import annotations

import threading
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
