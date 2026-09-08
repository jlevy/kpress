"""Real-browser regression for the vendored mono face.

The cascade cannot answer which face drew a run of code: ``--kpress-font-mono`` names
the vendored family and then the system monos behind it, and computed style reports the
whole list either way. Chromium answers directly through ``CSS.getPlatformFontsForNode``,
which names the face it resolved and whether it came from a web font.

Two invariants, on inline ``code`` inside a paragraph of prose, under both media:

- the face is a custom font, so it came from KPress and not from the machine (before the
  vendoring this measured ``Menlo`` with ``isCustomFont: false`` on a Mac, and 56 KB of
  embedded Menlo in a Mac-made PDF);
- it is Source Code Pro, on screen and in print alike. There is no print-only instance
  set for mono the way there is for the sans: both weights are already static, so
  Chromium's PDF writer embeds them instead of drawing Type3 outline paths.

A third check here is the cost of that face rather than the face itself.
``--kpress-font-size-mono`` is set by x-height, matched against PT Serif, and a size
chosen that way carries a wider advance than the system monos the older ratio was tuned
for. What the wider advance spends is measured in columns: how many characters of code
one line of a block holds. That budget is pinned below, at the default reading measure,
so a later retune of the ratio has to move a number in the suite rather than narrow the
block on its own.
"""

from __future__ import annotations

import threading
from collections.abc import Generator
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

import pytest

from kpress.publish import build_site

#: The family as Chromium reports it. Google Fonts instanced the static files from a
#: variable font whose default axis position is ExtraLight and left that name in the
#: table, so both weights call themselves "Source Code Pro ExtraLight" and their
#: PostScript names are SourceCodeProExtraLight-Regular and -Bold -- while the outlines
#: are the real 400 and 700 (usWeightClass says so, and the stems differ). Platforms
#: also disagree about how much of the name they report, the way they do for the
#: variable sans (see test_playwright_print_sans_face.VARIABLE_POSTSCRIPT), so only the
#: prefix is fixed. static/fonts/README.md records the quirk.
MONO_FAMILY = "Source Code Pro"
MONO_POSTSCRIPT = "SourceCodePro"

#: Inline code inside prose: the run whose face was the system's before this landed.
_INLINE_CODE = ".kpress-prose p code"
#: A code fence, which reads the same token at the same size.
_CODE_BLOCK = ".kpress-code"

#: The floor the mono size has to clear. Eighty columns is the standard code-line
#: budget, and it is the reason the size is worth measuring at all: the block has to
#: hold a line of code that was written to fit a terminal.
MIN_COLUMN_BUDGET = 80

#: What a block actually holds at the default reading measure and the 16px base. The
#: usable inner width is 700px there, and 700 / 8.5100 is 82.26, so 82 columns fit at
#: 697.8px and 83 do not at 706.3px. The 0.82 mono size this replaced held 92.
COLUMN_BUDGET = 82

#: The letter-spacing the size rule carries with it, in em: document.css sets both
#: ``font-size: var(--kpress-font-size-mono)`` and ``letter-spacing: -0.025em`` on the
#: one ``.kpress code, .kpress-code`` rule, so the spacing is part of the sizing choice
#: and not a separate knob.
MONO_LETTER_SPACING_EM = -0.025

#: A column of code, in em of the mono size. Source Code Pro advances 0.600em, the
#: negative letter-spacing takes 0.025em back, and the column is what is left: 0.575em,
#: which at the 0.925 size against a 16px base is 14.8 * 0.575 = 8.5100px. Computing a
#: budget from 0.600em instead is what makes the block look narrower than it is.
MONO_ADVANCE_EM = 0.600 + MONO_LETTER_SPACING_EM

#: A source line at exactly the budget, so the fixture carries a line of the width being
#: pinned instead of only asserting about one.
_BUDGET_LINE = "# " + "-" * (COLUMN_BUDGET - 2)

#: The pane the budget is measured in. The reading column clamps to the pane below
#: roughly 1000 CSS px and legitimately holds fewer columns there, so a narrower
#: viewport would pin the wrong number: 900px wide gives 624px of usable width and 73
#: columns. Anything at or above 1000px reaches the full measure and reports the same
#: 700px, so the exact width here is not load-bearing.
_BUDGET_VIEWPORT = {"width": 1200, "height": 1000}


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _build_fixture_site(tmp_path: Path) -> Path:
    (tmp_path / "content").mkdir(parents=True)
    (tmp_path / "content" / "index.md").write_text(
        "# Mono face smoke\n\n"
        "A paragraph of prose with `inline_code(x)` set inside it.\n\n"
        "```python\n"
        f"{_BUDGET_LINE}\n"
        "def render(document: str) -> str:\n"
        "    return document\n"
        "```\n",
        encoding="utf-8",
    )
    (tmp_path / "kpress.yml").write_text(
        "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n",
        encoding="utf-8",
    )
    build_site(tmp_path / "kpress.yml")
    return tmp_path / "public"


@contextmanager
def _chromium_page(sync_api: Any, public: Path, viewport: dict[str, int]) -> Generator[Any]:
    """Serve the built site and hand back a Chromium page on its index.

    Both tests below want the same server, the same two-step launch and the same
    teardown; only the pane width and what they read off the page differ.
    """
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
                context = browser.new_context(viewport=viewport)
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                yield page
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


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
    for _ in range(30):
        font = _platform_font(page, selector)
        if font["isCustomFont"]:
            return font
        page.wait_for_timeout(100)
        page.evaluate("document.fonts.ready")
    return _platform_font(page, selector)


def _assert_is_the_vendored_mono(font: dict[str, Any]) -> None:
    assert font["isCustomFont"], font
    assert font["familyName"].startswith(MONO_FAMILY), font
    assert font["postScriptName"].startswith(MONO_POSTSCRIPT), font


def test_code_is_drawn_by_the_vendored_mono_face(tmp_path: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    public = _build_fixture_site(tmp_path)
    with _chromium_page(sync_api, public, {"width": 900, "height": 900}) as page:
        page.wait_for_selector(_INLINE_CODE)

        faces = {
            (selector, media): _settled(page, selector, media)
            for selector in (_INLINE_CODE, _CODE_BLOCK)
            for media in ("screen", "print")
        }

    for where, font in faces.items():
        assert font["familyName"], where
        _assert_is_the_vendored_mono(font)


# The budget is read off the block the way a line of code meets it: a run of characters
# either fits the usable inner width or it does not. Asking the browser that question
# keeps the assertion off the float, so sub-pixel rounding on one platform cannot decide
# it. `x` is used because the face is monospaced -- every glyph advances the same, and a
# letter avoids any digit or punctuation the face might treat as a special case.
# clientWidth is the padding box less any scrollbar, so the two paddings come off it to
# leave the width the text itself has; it is read before the probe is attached, so a
# scrollbar the probe provokes cannot move the number it is compared against.
_BUDGET_PROBE = """(budget) => {
  const block = document.querySelector('.kpress-code');
  const styles = getComputedStyle(block);
  const usable =
    block.clientWidth - parseFloat(styles.paddingLeft) - parseFloat(styles.paddingRight);

  const probe = document.createElement('span');
  probe.style.whiteSpace = 'pre';
  probe.style.display = 'inline-block';
  block.appendChild(probe);
  const widthOf = (columns) => {
    probe.textContent = 'x'.repeat(columns);
    return probe.getBoundingClientRect().width;
  };

  // Differencing two runs cancels whatever the probe's own box contributes and
  // leaves the per-column advance by itself.
  const advance = (widthOf(101) - widthOf(1)) / 100;
  let columns = 0;
  while (columns < 400 && widthOf(columns + 1) <= usable) {
    columns += 1;
  }
  const measured = {
    usable,
    advance,
    columns,
    fontSize: parseFloat(styles.fontSize),
    letterSpacing: parseFloat(styles.letterSpacing),
    fitsAtBudget: widthOf(budget) <= usable,
    fitsPastBudget: widthOf(budget + 1) <= usable,
  };
  probe.remove();
  return measured;
}"""


def test_a_code_block_holds_its_column_budget(tmp_path: Path) -> None:
    """How much code one line of a block holds, at the default reading measure.

    The mono size is chosen by x-height, and this is what that choice costs. Nothing
    else in the suite records the number, so a later retune of the ratio could narrow
    every code block in every document and no test would say so.
    """

    sync_api = pytest.importorskip("playwright.sync_api")
    public = _build_fixture_site(tmp_path)
    with _chromium_page(sync_api, public, _BUDGET_VIEWPORT) as page:
        page.wait_for_selector(_CODE_BLOCK)
        # Measured before the vendored face arrives, this reports the fallback's
        # advance, which is a different number. _settled is the file's existing wait
        # for the face, and it doubles as the guard that the right one is in place.
        _assert_is_the_vendored_mono(_settled(page, _CODE_BLOCK, "screen"))
        measured = cast(dict[str, Any], page.evaluate(_BUDGET_PROBE, COLUMN_BUDGET))

    # The rule, and the reason the budget is recorded at all: a block holds a standard
    # code line. Everything below this says what the margin over it currently is.
    assert measured["columns"] >= MIN_COLUMN_BUDGET, measured

    # The budget itself, as the browser's own fit test rather than a float comparison.
    assert measured["fitsAtBudget"], measured
    assert not measured["fitsPastBudget"], measured
    assert measured["columns"] == COLUMN_BUDGET, measured

    # Where the width of a column comes from. Both halves are asserted because a change
    # to either one moves the budget, and reading the size alone would miss the spacing.
    assert measured["letterSpacing"] == pytest.approx(
        measured["fontSize"] * MONO_LETTER_SPACING_EM, rel=0.01
    ), measured
    assert measured["advance"] == pytest.approx(measured["fontSize"] * MONO_ADVANCE_EM, rel=0.01), (
        measured
    )
