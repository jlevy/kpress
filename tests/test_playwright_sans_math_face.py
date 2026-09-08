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

Four invariants on one document:

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
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, TypedDict, cast

import pytest

from devtools.instance_sans import FAMILY
from devtools.katex_text_metrics import SANS_REGULAR_WEIGHT
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

#: How much shorter KaTeX's vertical list for `4001/4000` comes out from the sans table
#: than from the serif one: the digits are 0.074em shorter (0.638 against 0.712), and the
#: fraction's shift rules take a little off that. Bounded on both sides, so a page that
#: never switched sets (zero) and one that installed something wild both fail.
FRACTION_SHRINK_EM = (0.02, 0.15)


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _build_fixture_site(tmp_path: Path) -> Path:
    """A document with the same expression in prose and in a sans role.

    A table cell, not a figure caption: kpress escapes a figcaption's text, so the one
    sans role a Markdown document cannot put mathematics into is the caption. The
    footnote is the second role and rides along on the same page.
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
    (tmp_path / "kpress.yml").write_text(
        "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n",
        encoding="utf-8",
    )
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


def _platform_font(page: Any, selector: str) -> dict[str, Any]:
    """The face Chromium drew most of a node's glyphs with, as it reports it."""
    session = page.context.new_cdp_session(page)
    try:
        session.send("DOM.enable")
        session.send("CSS.enable")
        root = cast(dict[str, Any], session.send("DOM.getDocument", {"depth": -1}))
        found = cast(
            dict[str, Any],
            session.send(
                "DOM.querySelector", {"nodeId": root["root"]["nodeId"], "selector": selector}
            ),
        )
        assert found["nodeId"], f"no node for {selector}"
        result = cast(
            dict[str, Any],
            session.send("CSS.getPlatformFontsForNode", {"nodeId": found["nodeId"]}),
        )
        fonts = cast(list[dict[str, Any]], result["fonts"])
        assert fonts, f"no platform fonts reported for {selector}"
        return max(fonts, key=lambda font: cast(int, font["glyphCount"]))
    finally:
        session.detach()


def _settled(page: Any, selector: str, media: str) -> dict[str, Any]:
    """Switch media, let the faces the new layout needs load, and read the face back."""
    page.emulate_media(media=media)
    page.evaluate("document.fonts.ready")
    # A face declared inside `@media print` only starts loading once print media matches
    # and a layout asks for it, so the first report can still name the screen's face.
    for _ in range(30):
        font = _platform_font(page, selector)
        if font["isCustomFont"] and VARIABLE_FACE not in font["familyName"]:
            return font
        page.wait_for_timeout(100)
        page.evaluate("document.fonts.ready")
    return _platform_font(page, selector)


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
                probe = cast(Probe, page.evaluate(_PROBE))
                screen = {
                    name: _platform_font(page, f"#kpress-probe-{name}")
                    for name in ("prose", "table", "footnote")
                }
                page.focus('.kpress-footnote-ref a[href^="#fn-"]')
                page.wait_for_selector(".kpress-tooltip-footnote", timeout=10_000)
                page.evaluate("document.fonts.ready")
                stamped = cast(dict[str, Any], page.evaluate(_OVERLAY_PROBE))
                overlay = _platform_font(page, "#kpress-probe-overlay")
                printed = _settled(page, "#kpress-probe-table", "print")
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
    # now draws there, so the vertical list is shorter than the prose one's.
    shrink = probe["prose"] - probe["table"]
    low, high = FRACTION_SHRINK_EM
    assert low <= shrink <= high, (probe["prose"], probe["table"])
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
