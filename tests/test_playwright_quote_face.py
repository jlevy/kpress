"""Real-browser regression for the shipped quote face.

``KPress Quotes`` leads ``--kpress-font-prose`` over six code points and passes every
other character down to PT Serif, which is a claim about font matching and not about the
cascade: computed style reports the whole stack for both, and says nothing about which
face drew which glyph. Chromium answers directly through ``CSS.getPlatformFontsForNode``,
which lists every face a node's glyphs came from, whether each is a web font, and how
many glyphs each drew.

One paragraph carries the whole test. Its quotation marks must come from a custom face
whose family is ``KPress Quotes``, and the letters between them from PT Serif, on screen
and under print media alike -- the borrowing this replaced was a ``local()`` face, so it
answered differently on a reader without Georgia and differently again on paper.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

import pytest

from devtools.subset_quotes import CODE_POINTS, FAMILY, POSTSCRIPT_NAME
from kpress.publish import build_site

#: The reading face, as Chromium names the vendored static PT Serif.
PROSE_FACE = "PT Serif"

#: The prose paragraph the fixture puts the marks in.
_PARAGRAPH = ".kpress-prose p"

#: A sentence whose quotation marks and apostrophe are the only characters outside PT
#: Serif's reach, so the two faces the node reports are exactly the two under test.
_QUOTED = "She said “the marks are shipped,” and that’s ‘the whole rule’.\n"

#: How many of that sentence's characters the quote face is the only candidate for.
_MARKS = sum(1 for character in _QUOTED if ord(character) in CODE_POINTS)


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _build_fixture_site(tmp_path: Path) -> Path:
    (tmp_path / "content").mkdir(parents=True)
    (tmp_path / "content" / "index.md").write_text(
        f"# Quotation marks\n\n{_QUOTED}", encoding="utf-8"
    )
    (tmp_path / "kpress.yml").write_text(
        "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n",
        encoding="utf-8",
    )
    build_site(tmp_path / "kpress.yml")
    return tmp_path / "public"


def _platform_fonts(session: Any, selector: str) -> list[dict[str, Any]]:
    """Every face Chromium drew a node's glyphs with, as it reports them."""
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
    return fonts


def _settled(page: Any, session: Any, selector: str, media: str) -> dict[str, dict[str, Any]]:
    """Switch media, let the faces load, and read back the faces by family name.

    One session serves every read: detaching one resets the emulated media, so a fresh
    session per read would measure the page back on screen.
    """
    page.emulate_media(media=media)
    page.evaluate("document.fonts.ready")
    for _ in range(30):
        fonts = _platform_fonts(session, selector)
        by_family = {cast(str, font["familyName"]): font for font in fonts}
        if FAMILY in by_family and PROSE_FACE in by_family:
            return by_family
        page.wait_for_timeout(100)
        page.evaluate("document.fonts.ready")
    return {cast(str, font["familyName"]): font for font in _platform_fonts(session, selector)}


def test_quotation_marks_come_from_the_shipped_quote_face(tmp_path: Path) -> None:
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
                page.wait_for_selector(_PARAGRAPH)

                session = context.new_cdp_session(page)
                try:
                    session.send("DOM.enable")
                    session.send("CSS.enable")
                    screen = _settled(page, session, _PARAGRAPH, "screen")
                    printed = _settled(page, session, _PARAGRAPH, "print")
                finally:
                    session.detach()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    for media, fonts in (("screen", screen), ("print", printed)):
        # The marks: a face KPress ships, under the name the generator gives it.
        quotes = fonts.get(FAMILY)
        assert quotes is not None, (media, sorted(fonts))
        assert quotes["isCustomFont"], (media, quotes)
        assert quotes["postScriptName"] == POSTSCRIPT_NAME, (media, quotes)
        # Every mark in the sentence, and nothing that is not one.
        assert quotes["glyphCount"] == _MARKS, (media, quotes, _MARKS)

        # The letters between them: still the reading face, undisturbed.
        prose = fonts.get(PROSE_FACE)
        assert prose is not None, (media, sorted(fonts))
        assert prose["isCustomFont"], (media, prose)
        assert prose["glyphCount"] > quotes["glyphCount"], (media, prose, quotes)

        # And nothing else drew a glyph in that paragraph.
        assert set(fonts) == {FAMILY, PROSE_FACE}, (media, sorted(fonts))
