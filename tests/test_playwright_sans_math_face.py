"""Real-browser regression for the sans math composite.

`KPress Math Text Sans` draws the Latin letters and digits inside KaTeX from Source Sans
3 in a document's sans roles -- a table cell, a footnote -- while prose keeps PT Serif
(see kpress-design.md "Math Text Face"). Two engines have to agree for that to be true:
the cascade has to resolve the composite to Source Sans there and to PT Serif elsewhere,
and `katex-init.js` has to install the matching metric table before each node renders.

Neither shows in computed style. Both composites resolve to the same CSS family list, and
Source Sans sets its digits on 0.497em against KaTeX_Main's 0.500em, so unlike the serif
regression this one cannot tell the faces apart by advance either. Chromium answers
directly through ``CSS.getPlatformFontsForNode``, which names the face it resolved, and
that is what this measures.

Four invariants on one document, and a fifth on the reader control that moves it:

- the digits of mathematics in a table cell resolve to Source Sans 3 and the digits of
  the same expression in prose resolve to PT Serif;
- under print media the table cell's digits come from a static `KPress Print Sans`
  instance rather than the variable face, so a PDF embeds a font instead of Type3
  outline paths;
- the table cell's fraction is laid out from the sans table: Source Sans's digits are
  0.638em tall against PT Serif's 0.712em, so KaTeX's vertical list for `4001/4000` is
  shorter there than in prose, which is what per-node table selection buys and what a
  CSS-only swap would leave undone;
- a footnote preview overlay draws the sans composite too. The overlay is a clone of
  math already typeset from the sans table, mounted outside every `.kpress`, so drawing
  it in the serif composite would put PT Serif glyphs on Source Sans metrics. This is
  the one place the two engines are decoupled -- nothing re-renders in the overlay --
  so only the cascade can keep them together.

And one on a reader control: the reading-font chooser moves prose between the two
composites, so it moves prose between the two table sets as well. The chooser reloads
into the persisted choice for that reason, and the measurement here is that the reload
re-selects the tables -- prose comes back laid out from the sans set, not merely drawn
from the sans faces.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, TypedDict, cast

import pytest

from devtools.instance_sans import FAMILY
from devtools.katex_text_metrics import ASSET_PATH, SANS_KEY, SANS_REGULAR_WEIGHT, parse_asset
from kpress.publish import build_site

from .test_playwright_math_text_face import (
    _PAINT_PROBE_INIT,  # pyright: ignore[reportPrivateUsage]
    TEXT_FACE_FAMILY,
    PaintProbe,
    WaitEntry,
    _covered,  # pyright: ignore[reportPrivateUsage]
    _faces,  # pyright: ignore[reportPrivateUsage]
    _loaded_first,  # pyright: ignore[reportPrivateUsage]
    _report,  # pyright: ignore[reportPrivateUsage]
    _served_page,  # pyright: ignore[reportPrivateUsage]
    _settled_before_the_deadline,  # pyright: ignore[reportPrivateUsage]
)

#: What Chromium calls the variable face: a variable web font is reported by its default
#: instance, and Source Sans 3 Variable's default position is 200, its ExtraLight.
VARIABLE_FACE = "Source Sans 3 ExtraLight"
#: The static instance the composite's regular slot layers in under print media, named by
#: its family and weight in `devtools/instance_sans.py`. The instances carry a family of
#: their own because the upstream licence reserves the name "Source".
PRINT_INSTANCE = f"{FAMILY.replace(' ', '')}-{SANS_REGULAR_WEIGHT}"
SERIF_FACE = "PT Serif"

#: KaTeX sets a text-style fraction's numerator one style down, in script style, at 0.7
#: of the size around it. The multiplier is KaTeX's (`Style.SCRIPT.sizeMultiplier`), not
#: this face's, and it is the same in both modes.
SCRIPT_STYLE_MULTIPLIER = 0.7
#: The numerator of the fixture's fraction, whose digits the vertical list is built over.
NUMERATOR = "4001"


def _numerator_height_em(tables: dict[str, Any]) -> float:
    """How tall `4001` stands in one table set: the tallest row among its digits."""
    regular = cast("dict[str, list[float]]", tables["Main-Regular"])
    return max(regular[str(ord(digit))][1] for digit in NUMERATOR)


def _expected_fraction_shrink_em() -> float:
    """How much shorter the sans set makes the `4001/4000` vertical list, from the tables.

    KaTeX gives the list a height of `numShift + numerator height`: the numerator's box
    is the topmost thing in it and `numShift` is how far above the baseline it sits.
    That shift is computed from KaTeX's own global metrics -- `num2`, the axis height,
    the default rule thickness -- which `__setFontMetrics` does not replace, so it is
    the same number in both modes and cancels out of the difference. The denominator
    sets the list's DEPTH rather than its height, and the two tables give `4000` the
    same depth in any case. What is left is the numerator: the tallest of its digits'
    height rows, taken at script style.

    So the expected shrink is read off the two shipped tables instead of being a band
    around a remembered number. PT Serif puts its digits at 0.712em and Source Sans at
    0.65em, and 0.7 of that 0.062em difference is the 0.0434em the browser reports. Any
    sans set that is only half installed -- serif rows left in a sans slot, or a table
    the loop never swapped -- moves this figure, which is what the old (0.02, 0.15) band
    was too wide to notice: it accepted anything from 46% of the real shrink to 3.5x it.
    """
    metrics = parse_asset(ASSET_PATH.read_text("utf-8"))
    serif = _numerator_height_em(metrics)
    sans = _numerator_height_em(cast("dict[str, Any]", metrics[SANS_KEY]))
    return SCRIPT_STYLE_MULTIPLIER * (serif - sans)


EXPECTED_FRACTION_SHRINK_EM = _expected_fraction_shrink_em()
#: KaTeX writes the list's height into a style attribute rounded to four decimals, and
#: the shrink is a difference of two such readings. The tolerance is that rounding and
#: float noise, not room for a table set that is wrong.
FRACTION_SHRINK_TOLERANCE_EM = 0.001


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _build_fixture_site(tmp_path: Path, *, choosers: str | None = None) -> Path:
    """A document with the same expression in prose and in a sans role.

    A table cell, not a figure caption: kpress escapes an image caption's text, so
    `![... $x$ ...](img.png)` never produces mathematics at all, and the inline raw-HTML
    forms of the other container roles leave `$x$` literal too. What a caption needs is
    the BLOCK form, raw HTML with blank lines around the content. Table cells and
    footnotes carry mathematics from plain Markdown, which is why they are the fixture.
    The footnote is the second role and rides along on the same page.

    `choosers` renders the settings widget's menu, for the one test that switches the
    reading face through the control a reader has rather than by stamping the attribute.
    """
    (tmp_path / "content").mkdir(parents=True)
    (tmp_path / "content" / "index.md").write_text(
        "# Sans math smoke\n\n"
        "In prose the mass is $s(n) = \\frac{4001}{4000}$, near one.[^a]\n\n"
        "| Quantity | Value |\n"
        "| --- | --- |\n"
        "| Mass | $s(n) = \\frac{4001}{4000}$ |\n\n"
        "[^a]: The note repeats $s(n) = \\frac{4001}{4000}$ in the sans face.\n",
        encoding="utf-8",
    )
    config = "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n"
    if choosers is not None:
        config += f"format:\n  widgets:\n    settings:\n      choosers: [{choosers}]\n"
    (tmp_path / "kpress.yml").write_text(config, encoding="utf-8")
    build_site(tmp_path / "kpress.yml")
    return tmp_path / "public"


class Probe(TypedDict):
    """What the page reports once KaTeX has typeset it."""

    prose: float
    table: float
    footnote: float
    rendered: int


#: Tags the first all-digit glyph run inside each of the three expressions so CDP can be
#: pointed at it by selector, and reads back the height KaTeX gave each fraction's
#: vertical list, in em, which it computes from whichever metric table was installed.
_PROBE = """(() => {
  const where = {
    prose: '.kpress-prose > p .katex',
    table: '.kpress-table td .katex',
    footnote: '.kpress-footnotes .katex',
  };
  const heights = {};
  for (const [name, selector] of Object.entries(where)) {
    const root = document.querySelector(selector);
    if (!root) { throw new Error('no math for ' + name); }
    const digits = [...root.querySelectorAll('.mord')].find(
      (el) => el.children.length === 0 && /^[0-9]+$/.test(el.textContent.trim())
    );
    if (!digits) { throw new Error('no digit run for ' + name); }
    digits.id = 'kpress-probe-' + name;
    heights[name] = parseFloat(root.querySelector('.mfrac .vlist').style.height);
  }
  heights.rendered = document.querySelectorAll('[data-kpress-math-rendered="true"]').length;
  return heights;
})()"""


#: Opens a footnote preview and tags the digit run inside the CLONE it carries, so the
#: same CDP probe can name the face Chromium drew the overlay with. Focus is the trigger
#: with no timer in front of it; the pointer path goes through a 500ms show delay.
_OVERLAY_PROBE = """(() => {
  const tooltip = document.querySelector('.kpress-tooltip-footnote');
  if (!tooltip) { throw new Error('no footnote preview opened'); }
  const root = tooltip.querySelector('.katex');
  if (!root) { throw new Error('the preview carries no rendered math'); }
  const digits = [...root.querySelectorAll('.mord')].find(
    (el) => el.children.length === 0 && /^[0-9]+$/.test(el.textContent.trim())
  );
  if (!digits) { throw new Error('no digit run in the preview'); }
  digits.id = 'kpress-probe-overlay';
  return {
    stamp: tooltip.getAttribute('data-kpress-math-text'),
    // The overlay leaves the document's subtree, so this has to be false for the test
    // to be about the stamp rather than about inheritance.
    inWrapper: Boolean(tooltip.closest('.kpress')),
  };
})()"""


def _platform_font(session: Any, selector: str) -> dict[str, Any]:
    """The face Chromium drew most of a node's glyphs with, as it reports it."""
    root = cast(dict[str, Any], session.send("DOM.getDocument", {"depth": -1}))
    found = cast(
        dict[str, Any],
        session.send("DOM.querySelector", {"nodeId": root["root"]["nodeId"], "selector": selector}),
    )
    assert found["nodeId"], f"no node for {selector}"
    result = cast(
        dict[str, Any],
        session.send("CSS.getPlatformFontsForNode", {"nodeId": found["nodeId"]}),
    )
    fonts = cast(list[dict[str, Any]], result["fonts"])
    assert fonts, f"no platform fonts reported for {selector}"
    return max(fonts, key=lambda font: cast(int, font["glyphCount"]))


def _settled(page: Any, session: Any, selector: str, media: str) -> dict[str, Any]:
    """Switch media, let the faces the new layout needs load, and read the face back.

    The caller keeps one CDP session attached across retries: detaching a sample
    resets print emulation, so the next attempt would read screen fonts instead.
    """
    page.emulate_media(media=media)
    page.evaluate("document.fonts.ready")
    # A face declared inside `@media print` only starts loading once print media matches
    # and a layout asks for it, so the first report can still name the screen's face.
    for _ in range(30):
        font = _platform_font(session, selector)
        if font["isCustomFont"] and VARIABLE_FACE not in font["familyName"]:
            return font
        page.wait_for_timeout(100)
        page.evaluate("document.fonts.ready")
    return _platform_font(session, selector)


# One `build_site`, one browser, three KaTeX renders, a footnote preview and a print
# re-layout with a retry loop behind it: 3s to 13s across runs on a warm Apple-silicon
# machine and 34.5s measured on a cold font cache, against the 60s `timeout`
# pyproject.toml sets for every test, which is too thin a margin on a shared runner.
@pytest.mark.timeout(180)
def test_sans_roles_draw_and_lay_out_mathematics_from_source_sans(tmp_path: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    public = _build_fixture_site(tmp_path)
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
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                page.wait_for_selector('[data-kpress-math-rendered="true"]', timeout=30_000)
                page.evaluate("document.fonts.ready")
                session = context.new_cdp_session(page)
                try:
                    session.send("DOM.enable")
                    session.send("CSS.enable")
                    probe = cast(Probe, page.evaluate(_PROBE))
                    screen = {
                        name: _platform_font(session, f"#kpress-probe-{name}")
                        for name in ("prose", "table", "footnote")
                    }
                    page.focus('.kpress-footnote-ref a[href^="#fn-"]')
                    page.wait_for_selector(".kpress-tooltip-footnote", timeout=10_000)
                    page.evaluate("document.fonts.ready")
                    stamped = cast(dict[str, Any], page.evaluate(_OVERLAY_PROBE))
                    overlay = _platform_font(session, "#kpress-probe-overlay")
                    printed = _settled(page, session, "#kpress-probe-table", "print")
                    assert page.evaluate("matchMedia('print').matches")
                finally:
                    session.detach()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert probe["rendered"] == 3

    # Drawn: the sans roles resolve the composite to Source Sans, prose to PT Serif.
    for name in ("table", "footnote"):
        assert screen[name]["isCustomFont"], screen[name]
        assert screen[name]["familyName"] == VARIABLE_FACE, (name, screen[name])
    assert screen["prose"]["isCustomFont"], screen["prose"]
    assert screen["prose"]["familyName"] == SERIF_FACE, screen["prose"]

    # Print: the static instance layered into the same composite, so a PDF embeds a font.
    assert printed["isCustomFont"], printed
    assert printed["familyName"].startswith(FAMILY), printed
    assert printed["familyName"] != VARIABLE_FACE, printed
    assert printed["postScriptName"] == PRINT_INSTANCE, printed

    # The preview overlay: a clone of the footnote's math, mounted outside every
    # `.kpress`, drawn from the same composite the metrics it carries were built for.
    assert stamped["inWrapper"] is False, stamped
    assert stamped["stamp"] == "prose", stamped
    assert overlay["isCustomFont"], overlay
    assert overlay["familyName"] == VARIABLE_FACE, overlay

    # Laid out: the sans table makes KaTeX size the fraction for the shorter digits it
    # now draws there, so the vertical list is shorter than the prose one's -- by the
    # amount the two shipped tables say, which is what makes a half-installed set fail.
    shrink = probe["prose"] - probe["table"]
    assert shrink == pytest.approx(EXPECTED_FRACTION_SHRINK_EM, abs=FRACTION_SHRINK_TOLERANCE_EM), (
        probe["prose"],
        probe["table"],
    )
    assert probe["footnote"] == pytest.approx(probe["table"], abs=0.001)


# ---- The mathematics of a sans role paints once too ----


#: The sans composite, whose faces a caption, a footnote and a table cell are drawn from.
#: The serif one rides along on the same page: this fixture has prose mathematics too, so
#: the wait covers both composites and both have to be ready before the first insertion.
SANS_FACE_FAMILY = "KPress Math Text Sans"


def _sans_paint_probe(tmp_path: Path) -> PaintProbe:
    """The paint probe of tests/test_playwright_math_text_face.py, on the sans fixture.

    Same instrumentation, a different document: this one puts the same expression in
    prose, in a table cell and in a footnote, so one page draws from both composites.
    """
    sync_api = pytest.importorskip("playwright.sync_api")
    public = _build_fixture_site(tmp_path)
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
                context.add_init_script(_PAINT_PROBE_INIT)
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                page.wait_for_selector('[data-kpress-math-rendered="true"]', timeout=30_000)
                page.evaluate("document.fonts.ready")
                probe = cast(PaintProbe, page.evaluate("globalThis.__kpressPaintProbe"))
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


# A second `build_site` and browser, with the face wait's own font loading in front of
# the render this one measures. As heavy as the test above and more variable: 2s to 21s
# across runs on the same warm machine, so it takes the same allowance.
@pytest.mark.timeout(180)
def test_sans_role_mathematics_paints_once_in_its_final_faces(tmp_path: Path) -> None:
    """A table cell's and a footnote's mathematics waits for the sans composite.

    The serif half of this is tested next door; what is new here is that a page with
    mathematics in a sans role draws from a SECOND composite, whose eight faces the
    original wait knew nothing about. Left out, a caption, a footnote and a table cell
    would each paint their digits in KaTeX_Main and repaint them in Source Sans while
    prose beside them stayed still -- the flash confined to exactly the roles the sans
    composite exists to set, which is the hardest kind to notice.

    Both composites, because the fixture has mathematics in prose and in two sans
    roles, so both are wanted and both are asked for. The four assertions are the
    ones the serif test makes, and for the same reasons: every face of each composite
    loaded before the first `.katex` node existed, every face the wait's own record
    says it covered did too, and the wait settled rather than being released by its
    three-second deadline -- without which the orderings are satisfied by a page that
    simply rendered very late.
    """
    probe = _sans_paint_probe(tmp_path)
    assert probe["firstKatex"] is not None, f"no .katex node was ever inserted\n{_report(probe)}"

    _settled_before_the_deadline(probe)
    for family in (TEXT_FACE_FAMILY, SANS_FACE_FAMILY):
        composite = _faces(probe, family)
        # Four slots, each two faces: the reading face and the KaTeX face for Greek.
        assert len(composite) == 8, f"{family}\n{_report(probe)}"
        _loaded_first(probe, composite, f"the composite {family} draws from")
    _loaded_first(probe, _covered(probe), "a face the wait covered")

    # The record says the sans slots were asked for at the sans weights, and that
    # each request in fact matched a face: an `empty` here would mean the wait
    # bought nothing for that slot, which is how a weight typo would look.
    sans = [entry for entry in probe["wait"] if SANS_FACE_FAMILY in entry["request"]]
    assert [entry["request"] for entry in sans] == [
        f"{weight} 1em '{SANS_FACE_FAMILY}'"
        for weight in ("400", "italic 400", "650", "italic 650")
    ], _report(probe)
    assert {entry["outcome"] for entry in sans} == {"loaded"}, _report(probe)


# ---- The reading-face chooser moves prose between the two table sets ----


def _choose_reading_font(page: Any, value: str) -> None:
    """Click a segment of the reading-font chooser and wait out the reload it triggers.

    Waiting on `data-kpress-math-rendered` alone would race the navigation: the document
    on its way out carries that attribute too, so the wait can return against it and
    leave the probe reading a page that is being replaced. The marker is set on the
    document that exists before the click and cannot survive into the one after it.

    A chooser that stamped the attribute without reloading therefore fails here rather
    than in an assertion: nothing else on the page would ever clear the marker.
    """
    page.evaluate("globalThis.__kpressBeforeSwitch = true")
    page.locator(".kpress-settings-btn").first.click()
    page.locator(f'[data-kpress-prose-choice="{value}"]').first.click()
    page.wait_for_function("globalThis.__kpressBeforeSwitch === undefined", timeout=30_000)
    page.wait_for_selector('[data-kpress-math-rendered="true"]', timeout=30_000)
    page.evaluate("document.fonts.ready")


# One more `build_site` and browser, and a full reload of the page inside it: 2s to 6s
# warm, with the same cold-cache exposure as the two above.
@pytest.mark.timeout(180)
def test_the_reading_face_chooser_carries_typeset_mathematics_with_it(tmp_path: Path) -> None:
    """Choosing the sans reading face re-lays prose out, rather than only redrawing it.

    The chooser used to stamp `data-kpress-prose-font` and persist it, which was
    harmless while the attribute changed text alone. It no longer does: katex-init.js
    selects a node's table set from its list of sans contexts, and
    `[data-kpress-prose-font="sans"]` is one of them, so the stamp moves every
    expression on the page into the sans composite while KaTeX goes on holding the PT
    Serif tables it was handed at load. That is Source Sans glyphs on PT Serif boxes --
    6.8% too narrow on a `2`, 14.4% on `\\mathbf{D}` -- and it persists until the reader
    happens to reload.

    So the chooser reloads, and this is the measurement that the reload does the work:
    prose comes back not merely drawn from the sans faces (the stamp alone would do
    that) but laid out from the sans table, shrinking by exactly the amount the two
    shipped tables differ by and landing on the height the table cell was already at.
    """
    public = _build_fixture_site(tmp_path, choosers="theme, reading-font")
    with _served_page(public) as page:
        session = page.context.new_cdp_session(page)
        try:
            session.send("DOM.enable")
            session.send("CSS.enable")
            before = cast(Probe, page.evaluate(_PROBE))
            serif_prose = _platform_font(session, "#kpress-probe-prose")
            _choose_reading_font(page, "sans")
            after = cast(Probe, page.evaluate(_PROBE))
            sans_prose = _platform_font(session, "#kpress-probe-prose")
            persisted = cast(str, page.evaluate("localStorage.getItem('kpress.proseFont')"))
        finally:
            session.detach()

    assert before["rendered"] == 3
    assert after["rendered"] == 3
    assert persisted == "sans"

    # Drawn: prose was PT Serif and is Source Sans now. The stamp alone would have got
    # this far, which is why it is the layout below that carries the finding.
    assert serif_prose["familyName"] == SERIF_FACE, serif_prose
    assert sans_prose["familyName"] == VARIABLE_FACE, sans_prose

    # Laid out: prose shrank by the table sets' own difference and now matches the cell
    # it shares a composite with. Without the reload it would still read `before`.
    shrink = before["prose"] - after["prose"]
    assert shrink == pytest.approx(EXPECTED_FRACTION_SHRINK_EM, abs=FRACTION_SHRINK_TOLERANCE_EM), (
        before["prose"],
        after["prose"],
    )
    assert after["prose"] == pytest.approx(before["table"], abs=0.001)
    assert after["prose"] == pytest.approx(after["table"], abs=0.001)
