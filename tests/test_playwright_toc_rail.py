"""Real-browser regression for the reserved TOC rail's geometry.

The wide band's two-column grid, the ``cqw``-keyed table cap, and the
``@container kpress-doc`` band selection are all container-query machinery that
browserless DOM emulation does not evaluate, so the claim this option exists to
make — *the reading column lands in the same place with and without a TOC* — can
only be asserted in a real engine.

The pane is 1300px inside a 1800px window: wide band, and narrower than the
window so a viewport-keyed rule would show up as a mismatch rather than passing
by coincidence.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from kpress.format import DocumentInput, RenderOptions, read_package_text, render_fragment

PANE_WIDTH_PX = 1300
WINDOW_WIDTH_PX = 1800

# An "auto" TOC takes both a heading count and a length (see
# RenderOptions.toc_min_headings), so the long fixture clears both: eight
# sections and comfortably more body than toc_min_words. The short one clears
# neither.
_SECTION_BODY = " ".join(["body"] * 120)
LONG = "# Title\n\nintro\n\n" + "".join(f"## Section {i}\n\n{_SECTION_BODY}\n\n" for i in range(8))
SHORT = "# Title\n\nintro\n\n## Only section\n\nbody\n"
# A 1x1 transparent GIF: enough for the thumbnail slot to become a grid item.
THUMBNAIL = "data:image/gif;base64,R0lGODlhAQABAAAAACw="


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _page_html(markdown: str, metadata: dict[str, str] | None = None, **options: object) -> str:
    rendered = render_fragment(
        DocumentInput(
            title="Doc",
            source_text=markdown,
            source_path="doc.md",
            body_markdown=markdown,
            trust_mode="sanitized",
            metadata=metadata or {},
        ),
        RenderOptions(widgets={"settings": "off"}, **options),  # pyright: ignore[reportArgumentType]
    )
    css = "\n".join(
        read_package_text(rel_path)
        for rel_path in ("css/style-tokens.css", "css/document.css", "css/components.css")
    )
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{css}</style></head><body style='margin:0'>"
        '<div class="kpress-frame">'
        f'<div class="kpress-viewport" style="inline-size: {PANE_WIDTH_PX}px">'
        f"{rendered.html}</div></div></body></html>"
    )


_PROBE = """(() => {
  const box = (selector) => {
    const el = document.querySelector(selector);
    if (!el) return null;
    const rect = el.getBoundingClientRect();
    return {left: Math.round(rect.left), right: Math.round(rect.right)};
  };
  const prose = document.querySelector('.kpress-long-text');
  const rect = prose.getBoundingClientRect();
  const styles = getComputedStyle(prose);
  return {
    pane: box('.kpress-viewport'),
    thumbnail: box('.thumbnail'),
    // Where the reader's text actually starts and ends, padding excluded:
    // the column box alone would hide a measure change.
    textLeft: Math.round(rect.left + parseFloat(styles.paddingLeft)),
    textRight: Math.round(rect.right - parseFloat(styles.paddingRight)),
  };
})()"""


def _measure(tmp_path: Path, pages: dict[str, str]) -> dict[str, Any]:
    """Render each named page in Chromium and return its measured geometry."""

    sync_api = pytest.importorskip("playwright.sync_api")
    for name, html in pages.items():
        (tmp_path / f"{name}.html").write_text(html, encoding="utf-8")

    handler = partial(_QuietHandler, directory=str(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_api.sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
            except sync_api.Error:
                try:
                    # System Chrome fallback, matching the other Playwright
                    # smokes, so the test runs without the managed download.
                    browser = playwright.chromium.launch(headless=True, channel="chrome")
                except sync_api.Error as exc:
                    pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")
            try:
                page = browser.new_page(viewport={"width": WINDOW_WIDTH_PX, "height": 900})
                measured: dict[str, Any] = {}
                for name in pages:
                    page.goto(f"http://127.0.0.1:{server.server_address[1]}/{name}.html")
                    measured[name] = page.evaluate(_PROBE)
                return measured
            finally:
                browser.close()
    finally:
        server.shutdown()
        thread.join()


def test_reserved_rail_holds_the_reading_column_in_one_place(tmp_path: Path) -> None:
    measured = _measure(
        tmp_path,
        {
            "with_toc": _page_html(LONG, toc_rail="reserved"),
            "without_toc": _page_html(SHORT, toc_rail="reserved"),
        },
    )

    # Position AND measure: the un-reserved fallback got both wrong, shifting
    # the column left and narrowing the text by the 2.5rem grid-track inset.
    assert measured["without_toc"]["textLeft"] == measured["with_toc"]["textLeft"]
    assert measured["without_toc"]["textRight"] == measured["with_toc"]["textRight"]

    # ...and it is the sidebar layout that both match, not some third position:
    # the column starts past the 15rem rail plus its 3rem gap.
    pane_left = measured["with_toc"]["pane"]["left"]
    assert measured["with_toc"]["textLeft"] - pane_left > 15 * 16


def test_auto_rail_keeps_the_historical_centred_fallback(tmp_path: Path) -> None:
    """The default must not quietly re-lay-out every existing document."""

    measured = _measure(
        tmp_path,
        {
            "with_toc": _page_html(LONG),
            "without_toc": _page_html(SHORT),
        },
    )

    assert measured["without_toc"]["textLeft"] != measured["with_toc"]["textLeft"]
    # The no-TOC column is centred in the pane.
    pane = measured["without_toc"]["pane"]
    left_gap = measured["without_toc"]["textLeft"] - pane["left"]
    right_gap = pane["right"] - measured["without_toc"]["textRight"]
    assert abs(left_gap - right_gap) <= 1


def test_reserved_rail_keeps_the_thumbnail_out_of_the_empty_rail(tmp_path: Path) -> None:
    """The thumbnail has no explicit track, so auto-placement would claim it."""

    measured = _measure(
        tmp_path,
        {"thumbnail": _page_html(SHORT, {"thumbnail_url": THUMBNAIL}, toc_rail="reserved")},
    )
    page = measured["thumbnail"]

    assert page["thumbnail"] is not None, "thumbnail missing from render"
    # It belongs beside the prose, not in the reserved rail to its left.
    assert page["thumbnail"]["left"] >= page["textLeft"] - 1
