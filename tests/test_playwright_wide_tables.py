"""Real-browser regression for the wide-table pane cap in no-TOC embeds.

The base wide-table bleed is column-centred and keyed off ``100cqw`` so it
caps at the kpress-doc pane. The failure this pins down: a document rendered
with the TOC off, embedded in a host pane narrower than the browser window,
has no ``has-toc`` band reset — only the base rule positions the marked
table, and a viewport-keyed width (``100vw``) let the bleed exceed the pane.
With stock tokens the bleed's other term caps at ``max(100%, 48rem)``, below
any wide-band pane, so the spill needs the host to widen the public
``--kpress-measure`` token past the pane — a supported host tuning this test
applies. Browserless DOM emulation evaluates neither container queries nor
container-relative units, so the geometry is asserted in real Chromium at a
wide window with a narrower pane.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from kpress.format import DocumentInput, RenderOptions, read_package_text, render_fragment


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


# 6 columns x ~20-char cells: over the default wide cutoff on both axes, so
# the server marks the wrap data-kpress-table-scale="wide".
_HEADER = "| " + " | ".join(f"Column heading {i}" for i in range(6)) + " |"
_DIVIDER = "| " + " | ".join("---" for _ in range(6)) + " |"
_ROW = "| " + " | ".join(f"verbose cell text {i}" for i in range(6)) + " |"
TABLE_MARKDOWN = "\n".join([_HEADER, _DIVIDER, _ROW, _ROW])

# The pane is 1300px (>= the 75rem wide band, so no narrower band's reset
# hides the base rule) while the window is 2000px: a viewport-keyed bleed
# would exceed the pane by ~700px.
PANE_WIDTH_PX = 1300
WINDOW_WIDTH_PX = 2000


def test_wide_table_stays_inside_a_narrow_no_toc_host_pane(tmp_path: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    markdown = f"# Embedded results\n\n{TABLE_MARKDOWN}\n"
    rendered = render_fragment(
        DocumentInput(
            title="Embedded results",
            source_text=markdown,
            source_path="results.md",
            body_markdown=markdown,
            trust_mode="sanitized",
        ),
        RenderOptions(include_toc="off", widgets={"settings": "off"}),
    )
    assert 'data-kpress-table-scale="wide"' in rendered.html

    css = "\n".join(
        read_package_text(rel_path)
        for rel_path in (
            "css/style-tokens.css",
            "css/theme-light.css",
            "css/document.css",
            "css/components.css",
        )
    )
    # Host tuning after the packaged CSS so the cascade honors it: a roomy
    # reading measure wider than the pane, the configuration under which a
    # viewport-keyed bleed spills past the pane edges.
    host_css = ":root, .kpress { --kpress-measure: 100rem; }"
    (tmp_path / "index.html").write_text(
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{css}</style><style>{host_css}</style></head><body style='margin:0'>"
        '<div class="kpress-frame">'
        f'<div class="kpress-viewport" style="inline-size: {PANE_WIDTH_PX}px">'
        f"{rendered.html}</div></div></body></html>",
        encoding="utf-8",
    )

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
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                rects = page.evaluate(
                    """(() => {
                      const pane = document.querySelector('.kpress-viewport');
                      const wrap = document.querySelector(
                        '.kpress-table-wrap[data-kpress-table-scale="wide"]');
                      return {
                        pane: pane.getBoundingClientRect().toJSON(),
                        wrap: wrap ? wrap.getBoundingClientRect().toJSON() : null,
                      };
                    })()"""
                )
                assert rects["wrap"] is not None, "wide-marked wrap missing from render"
                # Sub-pixel rounding tolerance only: the wrap must not spill
                # past either pane edge.
                assert rects["wrap"]["left"] >= rects["pane"]["left"] - 1
                assert rects["wrap"]["right"] <= rects["pane"]["right"] + 1
            finally:
                browser.close()
    finally:
        server.shutdown()
        thread.join()
