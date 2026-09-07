"""Real-browser regression for the drawn list marker.

The marker used to be the glyph U+25AA, which none of the faces KPress ships carries. It
therefore fell down whichever stack the rule inherited -- to Georgia on a Mac for the
prose lists, to some other fallback for the sans-family ``.claim`` marker, and to
something else again on Linux. A printed PDF embedded 16 KB of Georgia for 48 bullets.

It is now a ``currentColor`` box with ``content: ""``, so a list item contains no marker
text at all. That is what this measures, through ``CSS.getPlatformFontsForNode``: every
face Chromium resolves for a list item is a custom font, which is only true when nothing
in the item -- marker included -- fell through to the machine.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

import pytest

from kpress.publish import build_site

#: The three rules that draw the square: the prose list, the nested list print.css
#: restyles, and the claim marker, whose sans stack found a different fallback and drew
#: it 60% oversized.
_ITEMS = (".kpress-prose ul > li", ".kpress-prose ol ul > li", ".kpress .claim")


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _build_fixture_site(tmp_path: Path) -> Path:
    (tmp_path / "content").mkdir(parents=True)
    (tmp_path / "content" / "index.md").write_text(
        "# Marker smoke\n\n"
        "- A bulleted item, whose marker is the probe.\n"
        "- A second item.\n\n"
        "1. An ordered item that carries a nested list.\n"
        "   - The nested bullet, which print.css restyles.\n\n"
        '<div class="claim">A claim, whose marker is the same square.</div>\n',
        encoding="utf-8",
    )
    (tmp_path / "kpress.yml").write_text(
        "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n",
        encoding="utf-8",
    )
    build_site(tmp_path / "kpress.yml")
    return tmp_path / "public"


def _platform_fonts(page: Any, selector: str) -> list[dict[str, Any]]:
    """Every face Chromium drew a glyph of this node with, as it reports them."""
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
        return cast(list[dict[str, Any]], result["fonts"])
    finally:
        session.detach()


def _marker_box(page: Any, selector: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        page.evaluate(
            "(sel) => {"
            "  const before = getComputedStyle(document.querySelector(sel), '::before');"
            "  return {content: before.content, width: parseFloat(before.width),"
            "          height: parseFloat(before.height),"
            "          background: before.backgroundColor};"
            "}",
            selector,
        ),
    )


def test_list_markers_draw_no_text(tmp_path: Path) -> None:
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
                page.wait_for_selector(_ITEMS[0])
                page.evaluate("document.fonts.ready")

                fonts: dict[tuple[str, str], list[dict[str, Any]]] = {}
                for media in ("screen", "print"):
                    page.emulate_media(media=media)
                    page.evaluate("document.fonts.ready")
                    for item in _ITEMS:
                        fonts[item, media] = _platform_fonts(page, item)
                page.emulate_media(media="screen")
                boxes = {item: _marker_box(page, item) for item in _ITEMS}
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    for where, faces in fonts.items():
        assert faces, where
        borrowed = [face for face in faces if not face["isCustomFont"]]
        assert not borrowed, (where, borrowed)

    # The marker is a box, not a glyph: no content, and a painted background.
    for item, box in boxes.items():
        assert box["content"] in ('""', "none"), (item, box)
        assert box["background"] not in ("rgba(0, 0, 0, 0)", "transparent"), (item, box)
        assert box["width"] == pytest.approx(box["height"], abs=0.01), (item, box)

    # And one square for every bulleted list, which the glyph never managed: the sans
    # claim marker used to resolve a different fallback and come out 60% larger.
    widths = {round(box["width"], 3) for box in boxes.values()}
    assert len(widths) == 1, boxes
