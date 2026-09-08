"""Real-browser regression for the drawn list marker.

The marker used to be the glyph U+25AA, which none of the faces KPress ships carries. It
therefore fell down whichever stack the rule inherited -- to Georgia on a Mac for the
prose lists, to some other fallback for the sans-family ``.claim`` marker, and to
something else again on Linux. A printed PDF embedded 16 KB of Georgia for 48 bullets.

It is now a ``currentColor`` box with ``content: ""``, so a list item contains no marker
text at all. That is what this measures, through ``CSS.getPlatformFontsForNode``: every
face Chromium resolves for a list item is a custom font, which is only true when nothing
in the item -- marker included -- fell through to the machine.

A drawn box does not inherit two things a glyph got for free, and the other two tests
here hold on to them. In forced colors (Windows High Contrast) the UA rewrites
``background-color`` to ``Canvas``, so the box painted the page background onto the page
background and vanished; the fix is a ``forced-color-adjust: none`` rule that paints
``CanvasText`` instead. And the box is positioned by an inset rather than carried by the
line, so a physical ``left`` put it on the far side of a right-to-left item; the fix is
``inset-inline-start``.
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

#: The three rules that draw the square: the prose list, the nested list print.css
#: restyles, and the claim marker, whose sans stack found a different fallback and drew
#: it 60% oversized.
_ITEMS = (".kpress-prose ul > li", ".kpress-prose ol ul > li", ".kpress .claim")

#: Every mark KPress paints rather than sets, which is the set the forced-colors rule
#: names. The disclosure chevron belongs with the three squares because it fails the
#: same way: it is a mask filled with `background-color`.
_PAINTED_MARKS = (
    ".kpress-prose ul > li",
    ".kpress .concepts ul > li",
    ".kpress .claim",
    ".kpress summary",
)

#: The markers positioned by an inline-start inset, so direction is theirs to get wrong.
#: The disclosure chevron is not one of them: it is a flex item in the summary row, so
#: the row's own direction moves it and it reports no inset at all.
_INSET_MARKERS = (".kpress-prose ul > li", ".kpress .concepts ul > li", ".kpress .claim")


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _build_fixture_site(tmp_path: Path) -> Path:
    (tmp_path / "content").mkdir(parents=True)
    # The concepts list and the disclosure are here so the forced-colors test can assert
    # on every selector the rule names. Both are containers the renderer only emits for
    # markup that asks for them, so nothing else in the fixture would produce one.
    (tmp_path / "content" / "index.md").write_text(
        "# Marker smoke\n\n"
        "- A bulleted item, whose marker is the probe.\n"
        "- A second item.\n\n"
        "1. An ordered item that carries a nested list.\n"
        "   - The nested bullet, which print.css restyles.\n\n"
        '<div class="claim">A claim, whose marker is the same square.</div>\n\n'
        '<div class="concepts">\n\n'
        "- A concept, whose marker is the same square.\n"
        "- A second concept.\n\n"
        "</div>\n\n"
        "<details>\n"
        "<summary>A disclosure, whose chevron is drawn the same way.</summary>\n\n"
        "Body text behind the disclosure.\n\n"
        "</details>\n",
        encoding="utf-8",
    )
    (tmp_path / "kpress.yml").write_text(
        "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n",
        encoding="utf-8",
    )
    build_site(tmp_path / "kpress.yml")
    return tmp_path / "public"


def _launch_chromium(playwright: Any, sync_api: Any) -> Any:
    """The bundled browser, else the system one, else a skip rather than a failure."""
    try:
        return playwright.chromium.launch(headless=True)
    except sync_api.Error:
        try:
            return playwright.chromium.launch(headless=True, channel="chrome")
        except sync_api.Error as exc:
            pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")


@contextmanager
def _marker_page(tmp_path: Path, sync_api: Any) -> Generator[Any]:
    """The fixture site, served locally and open in Chromium with its fonts settled.

    The server and the browser each have to come down whatever the body does, and every
    test in this file needs the same sequence to bring them up. Yielding the page keeps
    the two teardowns in one place instead of three.
    """
    public = _build_fixture_site(tmp_path)
    handler = partial(_QuietHandler, directory=str(public))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_api.sync_playwright() as playwright:
            browser = _launch_chromium(playwright, sync_api)
            try:
                context = browser.new_context(viewport={"width": 900, "height": 900})
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                page.wait_for_selector(_ITEMS[0])
                page.evaluate("document.fonts.ready")
                yield page
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


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


def _forced_canvas_color(page: Any) -> str:
    """The color the UA is currently forcing unprotected backgrounds to.

    Read off a throwaway box declared exactly as the marker was before the fix. That is
    the reference the marker has to differ from, and it has to be measured rather than
    written down, because the forced palette is the reader's, not ours. `document.body`
    cannot stand in for it: the body's own background computes to transparent under
    forced colors, so it names no color at all.
    """
    return cast(
        str,
        page.evaluate(
            "() => {"
            "  const probe = document.createElement('div');"
            "  probe.style.background = 'currentColor';"
            "  document.body.appendChild(probe);"
            "  const forced = getComputedStyle(probe).backgroundColor;"
            "  probe.remove();"
            "  return forced;"
            "}"
        ),
    )


def _painted_mark(page: Any, selector: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        page.evaluate(
            "(sel) => {"
            "  const before = getComputedStyle(document.querySelector(sel), '::before');"
            "  return {background: before.backgroundColor,"
            "          forcedColorAdjust: before.forcedColorAdjust,"
            "          width: parseFloat(before.width),"
            "          height: parseFloat(before.height)};"
            "}",
            selector,
        ),
    )


def _marker_insets(page: Any, selector: str) -> dict[str, float]:
    """The marker's resolved physical offsets, which is where `inset-inline-start` lands."""
    return cast(
        dict[str, float],
        page.evaluate(
            "(sel) => {"
            "  const before = getComputedStyle(document.querySelector(sel), '::before');"
            "  return {left: parseFloat(before.left), right: parseFloat(before.right)};"
            "}",
            selector,
        ),
    )


def test_list_markers_draw_no_text(tmp_path: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    with _marker_page(tmp_path, sync_api) as page:
        fonts: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for media in ("screen", "print"):
            page.emulate_media(media=media)
            page.evaluate("document.fonts.ready")
            for item in _ITEMS:
                fonts[item, media] = _platform_fonts(page, item)
        page.emulate_media(media="screen")
        boxes = {item: _marker_box(page, item) for item in _ITEMS}

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


def test_list_markers_stay_visible_in_forced_colors(tmp_path: Path) -> None:
    """A painted mark survives the high-contrast palette a reader chose for legibility.

    Forced colors is the one place where a drawn box is worse than the glyph it replaced.
    The UA rewrites `background-color` to `Canvas` on everything that has not opted out,
    so a `currentColor` box paints the page background onto the page background: measured
    in Chromium, zero ink pixels where the glyph painted 196.
    """
    sync_api = pytest.importorskip("playwright.sync_api")
    with _marker_page(tmp_path, sync_api) as page:
        page.emulate_media(forced_colors="active")
        page.evaluate("document.fonts.ready")
        canvas = _forced_canvas_color(page)
        marks = {mark: _painted_mark(page, mark) for mark in _PAINTED_MARKS}

    for mark, drawn in marks.items():
        # The opt-out is what lets any color of ours through at all.
        assert drawn["forcedColorAdjust"] == "none", (mark, drawn)
        # And having opted out, the mark has to be some color other than the surface it
        # sits on. Without the rule this is the failure: both read as the Canvas color.
        assert drawn["background"] != canvas, (mark, drawn, canvas)
        # A mark with no area is invisible whatever color it is.
        assert drawn["width"] > 0, (mark, drawn)
        assert drawn["height"] > 0, (mark, drawn)


def test_list_markers_follow_the_text_direction(tmp_path: Path) -> None:
    """The marker hangs off the side the text starts on, in either direction.

    The offset was physical `left` while the marker was a glyph and stayed physical when
    it became a box, which put it past the end of a right-to-left item with its ink nudge
    pointing away from the text. `inset-inline-start` resolves to `right` under
    `dir="rtl"`, and this is that resolution, read back through the computed style.
    """
    sync_api = pytest.importorskip("playwright.sync_api")
    with _marker_page(tmp_path, sync_api) as page:
        ltr = {marker: _marker_insets(page, marker) for marker in _INSET_MARKERS}
        page.evaluate("document.documentElement.setAttribute('dir', 'rtl')")
        page.evaluate("document.fonts.ready")
        rtl = {marker: _marker_insets(page, marker) for marker in _INSET_MARKERS}

    for marker in _INSET_MARKERS:
        # The offset derives from --kpress-font-size-base, so the left-to-right reading
        # is the expectation and the right-to-left reading has to match it on the other
        # side. Writing the number here would only pin the current type scale.
        start = ltr[marker]["left"]
        assert start < 0, (marker, ltr[marker])
        assert rtl[marker]["right"] == pytest.approx(start, abs=0.01), (
            marker,
            ltr[marker],
            rtl[marker],
        )
        # The negative offset moved rather than being drawn on both sides: whichever side
        # is the inline end holds the marker inside the item.
        assert ltr[marker]["right"] >= 0, (marker, ltr[marker])
        assert rtl[marker]["left"] >= 0, (marker, rtl[marker])
