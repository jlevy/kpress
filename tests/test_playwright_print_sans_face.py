"""Real-browser regression for the print sans faces.

Which face actually drew a glyph is not visible in the cascade: the print stack names
both the static ``KPress Print Sans`` instances and the variable ``Source Sans 3
Variable`` as fallback, and computed style reports the whole list either way. Chromium
answers the question directly through ``CSS.getPlatformFontsForNode``, which names the
face it resolved and whether it came from a web font, so that is what this measures.

Two invariants, on one document:

- under print media the glyphs come from a static instance -- upright on the footnote
  body, italic on an ``h4``, and, on a probe span per row of ``EXPECTED_LANDING``, the
  instance CSS font matching is supposed to pick;
- under screen media they still come from the variable face, and no request for an
  instance is made at all, so nothing about the reading experience changed and no
  reader downloads one.

One weight assertion lives here too. The tab label is written twice -- a screen rule on
the button and a print rule on the panel title that replaces it -- and whether the two
agree is a question about what a browser resolved, not about what the stylesheets say.
``test_print_sans_faces.py`` reads the declarations; only a real browser can put the two
resolved values side by side, and a browser is already running here.

What the faces exist for -- the PDF -- is in ``test_playwright_print_pdf_fonts.py``.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

import pytest

from devtools.instance_sans import FAMILY, STYLES, WEIGHTS
from kpress.publish import build_site

from .test_print_sans_faces import EXPECTED_LANDING, WEIGHT_TOKENS, match_weight

#: The face the print stack must not resolve to, as Chromium names it: a variable web
#: font is reported by its default instance, and Source Sans 3 Variable's default
#: position is 200, which its own name table calls ExtraLight.
VARIABLE_FACE = "Source Sans 3 ExtraLight"
#: The variable face's own PostScript name. macOS appends the named instance
#: (``SourceSans3-Roman_Regular``); Linux reports it bare, so only the prefix is fixed.
VARIABLE_POSTSCRIPT = "SourceSans3-Roman"
#: The PostScript prefix of the static set, as `devtools/instance_sans.py` builds it.
STATIC_POSTSCRIPT = FAMILY.replace(" ", "")

#: The footnote body: sans by default (--kpress-font-footnote derives from the sans
#: token), plain text, and no image or math asset needed to put it on the page.
_FOOTNOTE = ".kpress-footnotes li p"
#: An h4: the one heading level that is sans, italic and at a weight with no instance
#: of its own (540, which rises to 550), so it exercises the italic half of the set.
_H4 = ".kpress-prose h4"
#: One probe span per row of the landing table, in both styles, each asking for its own
#: weight inside the print sans scope.
_PROBE_ROWS = [[weight, style] for weight in EXPECTED_LANDING for style in STYLES]

#: The tab label a reader sees. `js/tabs.js` builds the tab strip from the authored
#: panels, so the button exists only once the page has hydrated.
_TAB_BUTTON = ".kpress-tab-button"
#: The tab label a reader prints. Print media hides the tab strip and unhides every
#: panel, so print.css draws each panel's own title on this pseudo-element instead.
_TAB_PANEL = ".kpress-tab-panel"

_PROBE_JS = """
(rows) => {
  const host = document.querySelector(".kpress-prose");
  for (const [weight, style] of rows) {
    const span = document.createElement("span");
    span.dataset.printSansProbe = `${weight}-${style}`;
    span.style.fontFamily = "var(--kpress-font-sans)";
    span.style.fontWeight = String(weight);
    span.style.fontStyle = style;
    span.textContent = "Aa Gg 0123";
    host.append(span);
  }
}
"""


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _write_site(root: Path, body: str) -> Path:
    (root / "content").mkdir(parents=True)
    (root / "content" / "index.md").write_text(body, encoding="utf-8")
    (root / "kpress.yml").write_text(
        "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n",
        encoding="utf-8",
    )
    build_site(root / "kpress.yml")
    return root / "public"


def _build_fixture_site(tmp_path: Path) -> Path:
    return _write_site(
        tmp_path,
        "# Print sans smoke\n\n"
        "A paragraph of prose with a note attached to it.[^a]\n\n"
        "#### An italic fourth level heading\n\n"
        "A paragraph under it.\n\n"
        "[^a]: The footnote body is set in the sans face at the small size.\n",
    )


def _build_tab_fixture_site(tmp_path: Path) -> Path:
    """A page with an authored tab group, in the markdown a document author writes."""
    return _write_site(
        tmp_path,
        "# Tab label weight\n\n"
        "A paragraph before the tabs.\n\n"
        "::::: tabs\n"
        "::: tab Overview\n"
        "Tab overview copy.\n"
        ":::\n\n"
        "::: tab Details\n"
        "Tab detail copy.\n"
        ":::\n"
        ":::::\n",
    )


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

    One session serves every read: detaching one resets the emulated media on the
    tested Chromium, so a fresh session per read would measure the page back on screen.
    """
    page.emulate_media(media=media)
    page.evaluate("document.fonts.ready")
    # A face declared inside `@media print` only starts loading once print media
    # matches and a layout asks for it, so the first report can still name a fallback.
    # The guard names the family that has to arrive: `isCustomFont` is satisfied by the
    # variable face too, so a slow load would have ended the wait on the wrong answer.
    want = FAMILY if media == "print" else VARIABLE_FACE
    for _ in range(30):
        font = _platform_font(session, selector)
        if cast(str, font["familyName"]).startswith(want):
            return font
        page.wait_for_timeout(100)
        page.evaluate("document.fonts.ready")
    return _platform_font(session, selector)


def _computed_weight(page: Any, selector: str, pseudo: str | None = None) -> int:
    """The weight the cascade resolved for a node, under whatever media is emulated.

    Computed style reports a number whatever the declaration was spelled as, so this
    reads what the reader gets rather than what either stylesheet says.
    """
    element = "null" if pseudo is None else repr(pseudo)
    return int(
        cast(
            str,
            page.evaluate(
                f"getComputedStyle(document.querySelector({selector!r}), {element}).fontWeight"
            ),
        )
    )


def _recorder(urls: list[str]) -> Callable[[Any], None]:
    """A ``page.on("request")`` handler that keeps every URL the page asked for."""

    def record(request: Any) -> None:
        urls.append(cast(str, request.url))

    return record


def _launch(playwright: Any, sync_api: Any) -> Any:
    try:
        return playwright.chromium.launch(headless=True)
    except sync_api.Error:
        try:
            return playwright.chromium.launch(headless=True, channel="chrome")
        except sync_api.Error as exc:
            pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")


def test_print_media_draws_the_sans_from_a_static_instance(tmp_path: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    public = _build_fixture_site(tmp_path)
    handler = partial(_QuietHandler, directory=str(public))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    requested: list[str] = []
    probes: dict[str, dict[str, Any]] = {}
    try:
        with sync_api.sync_playwright() as playwright:
            browser = _launch(playwright, sync_api)
            try:
                context = browser.new_context(viewport={"width": 900, "height": 900})
                page = context.new_page()
                page.on("request", _recorder(requested))
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                page.wait_for_selector(_FOOTNOTE)

                session = context.new_cdp_session(page)
                try:
                    session.send("DOM.enable")
                    session.send("CSS.enable")
                    screen = _settled(page, session, _FOOTNOTE, "screen")
                    # What the reader's browser fetched, before print media is emulated
                    # and the instances become legitimately reachable.
                    screen_requests = list(requested)

                    page.evaluate(_PROBE_JS, _PROBE_ROWS)
                    printed = _settled(page, session, _FOOTNOTE, "print")
                    heading = _settled(page, session, _H4, "print")
                    for row in _PROBE_ROWS:
                        key = f"{row[0]}-{row[1]}"
                        probes[key] = _settled(
                            page, session, f'[data-print-sans-probe="{key}"]', "print"
                        )
                    # Read the weight while print media still holds, so the assertion
                    # below compares the printed face against the printed request.
                    assert page.evaluate("matchMedia('print').matches")
                    weight = int(
                        page.evaluate(
                            f"getComputedStyle(document.querySelector({_FOOTNOTE!r})).fontWeight"
                        )
                    )
                finally:
                    session.detach()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    # Print: a static instance, embeddable in a PDF and smoothed like any other font.
    assert printed["isCustomFont"], printed
    assert printed["familyName"].startswith(FAMILY), printed
    assert printed["familyName"] != VARIABLE_FACE, printed
    # And the instance the weight-matching rule predicts, named by its weight.
    assert printed["postScriptName"] == f"{STATIC_POSTSCRIPT}-{match_weight(weight, WEIGHTS)}", (
        printed,
        weight,
    )
    # The italic half of the set: an h4 is italic at 540, which has no instance and
    # rises to 550.
    assert heading["postScriptName"] == f"{STATIC_POSTSCRIPT}-550Italic", heading

    # Every row of the landing table, measured rather than restated: the weights the
    # stylesheets ask for, in both styles, against the instance each one lands on.
    assert {key: font["postScriptName"] for key, font in probes.items()} == {
        f"{weight}-{style}": (
            f"{STATIC_POSTSCRIPT}-{landing}{'Italic' if style == 'italic' else ''}"
        )
        for weight, landing in EXPECTED_LANDING.items()
        for style in STYLES
    }

    # Screen: unchanged, still the variable face at whatever weight the context asks for.
    assert screen["isCustomFont"], screen
    assert screen["familyName"] == VARIABLE_FACE, screen
    assert screen["postScriptName"].startswith(VARIABLE_POSTSCRIPT), screen
    # And no reader pays for the print set: the faces are declared inside `@media
    # print`, so a screen session never asks the server for one.
    assert not [url for url in screen_requests if "kpress-print-sans" in url], screen_requests


def test_the_tab_label_and_its_print_counterpart_share_one_weight(tmp_path: Path) -> None:
    """The screen tab button and the print panel title resolve to the same weight.

    The label is written twice: components.css styles the button a reader clicks, and
    print.css styles the panel title that stands in for it once the tab strip is hidden.
    Each rule is free to name its own number, and for a while the button's was a literal
    600 against the print rule's 550, so the same label came out heavier on screen than
    on paper. Nothing in the suite saw the split -- no test reads a tab weight, and a
    change to either rule surfaces only as a different golden hash -- which is why the
    two resolved values are compared here, in a browser that has applied both rules.
    """
    sync_api = pytest.importorskip("playwright.sync_api")
    public = _build_tab_fixture_site(tmp_path)
    handler = partial(_QuietHandler, directory=str(public))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_api.sync_playwright() as playwright:
            browser = _launch(playwright, sync_api)
            try:
                context = browser.new_context(viewport={"width": 900, "height": 900})
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                # The renderer emits panels, not buttons: js/tabs.js builds the tab
                # strip from them, so the wait is for hydration and not for the markup.
                page.wait_for_selector(_TAB_BUTTON)
                page.evaluate("document.fonts.ready")

                page.emulate_media(media="screen")
                assert page.evaluate("matchMedia('screen').matches")
                screen_weight = _computed_weight(page, _TAB_BUTTON)
                # The token as the page itself defines it, so the comparison below is
                # against what the stylesheets ship rather than a number restated here.
                token_weight = int(
                    cast(
                        str,
                        page.evaluate(
                            f"getComputedStyle(document.querySelector({_TAB_BUTTON!r}))"
                            ".getPropertyValue('--kpress-font-weight-sans-medium')"
                        ),
                    )
                )

                page.emulate_media(media="print")
                assert page.evaluate("matchMedia('print').matches")
                print_weight = _computed_weight(page, _TAB_PANEL, "::before")
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    # One label, one weight, whichever medium the reader is in.
    assert screen_weight == print_weight, (screen_weight, print_weight)
    # And the weight is the medium token's, so a literal typed back into either rule --
    # which is how the split happened the first time -- fails here rather than passing
    # quietly behind a regenerated golden file.
    assert screen_weight == token_weight, (screen_weight, token_weight)
    assert token_weight == WEIGHT_TOKENS["medium"], token_weight
