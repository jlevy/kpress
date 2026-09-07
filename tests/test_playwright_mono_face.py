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
"""

from __future__ import annotations

import threading
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


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _build_fixture_site(tmp_path: Path) -> Path:
    (tmp_path / "content").mkdir(parents=True)
    (tmp_path / "content" / "index.md").write_text(
        "# Mono face smoke\n\n"
        "A paragraph of prose with `inline_code(x)` set inside it.\n\n"
        "```python\n"
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
                page.wait_for_selector(_INLINE_CODE)

                faces = {
                    (selector, media): _settled(page, selector, media)
                    for selector in (_INLINE_CODE, _CODE_BLOCK)
                    for media in ("screen", "print")
                }
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    for where, font in faces.items():
        assert font["familyName"], where
        _assert_is_the_vendored_mono(font)
