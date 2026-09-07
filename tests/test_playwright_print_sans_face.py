"""Real-browser regression for the print sans faces.

Which face actually drew a glyph is not visible in the cascade: the print stack names
both the static ``Source Sans 3`` instances and the variable ``Source Sans 3 Variable``
as fallback, and computed style reports the whole list either way. Chromium answers the
question directly through ``CSS.getPlatformFontsForNode``, which names the face it
resolved and whether it came from a web font, so that is what this measures.

Two invariants, on one document, on the footnote text that reads
``--kpress-font-footnote`` (the sans token by default):

- under print media the glyphs come from a static instance -- a custom font whose family
  starts with ``Source Sans 3`` and is not the variable face, which reports itself by its
  default instance, ``Source Sans 3 ExtraLight``;
- under screen media they still come from the variable face, so nothing about the
  reading experience changed and no reader downloads an instance.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

import pytest

from devtools.instance_sans import WEIGHTS
from kpress.publish import build_site

from .test_print_sans_faces import match_weight

#: The face the print stack must not resolve to, as Chromium names it: a variable web
#: font is reported by its default instance, and Source Sans 3 Variable's default
#: position is 200, which its own name table calls ExtraLight.
VARIABLE_FACE = "Source Sans 3 ExtraLight"
#: The variable face's own PostScript name. macOS appends the named instance
#: (``SourceSans3-Roman_Regular``); Linux reports it bare, so only the prefix is fixed.
VARIABLE_POSTSCRIPT = "SourceSans3-Roman"

#: The footnote body: sans by default (--kpress-font-footnote derives from the sans
#: token), plain text, and no image or math asset needed to put it on the page.
_FOOTNOTE = ".kpress-footnotes li p"


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _build_fixture_site(tmp_path: Path) -> Path:
    (tmp_path / "content").mkdir(parents=True)
    (tmp_path / "content" / "index.md").write_text(
        "# Print sans smoke\n\n"
        "A paragraph of prose with a note attached to it.[^a]\n\n"
        "[^a]: The footnote body is set in the sans face at the small size.\n",
        encoding="utf-8",
    )
    (tmp_path / "kpress.yml").write_text(
        "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n",
        encoding="utf-8",
    )
    build_site(tmp_path / "kpress.yml")
    return tmp_path / "public"


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
    for _ in range(30):
        font = _platform_font(session, selector)
        if font["isCustomFont"]:
            return font
        page.wait_for_timeout(100)
        page.evaluate("document.fonts.ready")
    return _platform_font(session, selector)


def test_print_media_draws_the_sans_from_a_static_instance(tmp_path: Path) -> None:
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
                page.wait_for_selector(_FOOTNOTE)

                session = context.new_cdp_session(page)
                try:
                    session.send("DOM.enable")
                    session.send("CSS.enable")
                    screen = _settled(page, session, _FOOTNOTE, "screen")
                    printed = _settled(page, session, _FOOTNOTE, "print")
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
    assert printed["familyName"].startswith("Source Sans 3"), printed
    assert printed["familyName"] != VARIABLE_FACE, printed
    assert "Variable" not in printed["familyName"], printed
    # And the instance the weight-matching rule predicts, named by its weight.
    assert printed["postScriptName"] == f"SourceSans3-{match_weight(weight, WEIGHTS)}", (
        printed,
        weight,
    )

    # Screen: unchanged, still the variable face at whatever weight the context asks for.
    assert screen["isCustomFont"], screen
    assert screen["familyName"] == VARIABLE_FACE, screen
    assert screen["postScriptName"].startswith(VARIABLE_POSTSCRIPT), screen
