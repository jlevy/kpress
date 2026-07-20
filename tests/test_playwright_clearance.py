"""Real-browser regression for the floating TOC-toggle clearance.

The clearance is a cascade property with a deliberate split: the narrow-band
rule reserves ``max(1rem, var(--kpress-toc-toggle-clearance))`` on
``.kpress-doc`` at mid widths, while the later phone rule drops the
reservation entirely — on a phone every rem of gutter is reading width, and
the toggle's translucent document-background fill keeps slight text overlap
legible (design review decision; see the phone-gutter comment in
components.css). Browserless DOM emulation does not evaluate container
queries, so the computed padding is asserted in real Chromium at one phone
width and one tablet width.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from kpress.publish import build_site


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


FILLER = "\n\n".join(f"Paragraph {index} of filler prose." for index in range(10))


def test_toc_toggle_clearance_survives_the_phone_breakpoint(tmp_path: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    (tmp_path / "content").mkdir()
    sections = "\n\n".join(f"## Part {index}\n\n{FILLER}" for index in range(1, 5))
    # Enough headings for the TOC (toc_min_headings) so the floating toggle band applies.
    (tmp_path / "content" / "index.md").write_text(
        f"# Clearance smoke\n\n{sections}\n",
        encoding="utf-8",
    )
    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n",
        encoding="utf-8",
    )
    build_site(config)

    handler = partial(_QuietHandler, directory=str(tmp_path / "public"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_api.sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
            except sync_api.Error:
                try:
                    # System Chrome fallback, matching the history smoke, so the
                    # test runs on machines without the managed Chromium download.
                    browser = playwright.chromium.launch(headless=True, channel="chrome")
                except sync_api.Error as exc:
                    pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")
            try:
                page = browser.new_page(viewport={"width": 390, "height": 800})
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")

                def doc_metrics() -> dict[str, float]:
                    return page.evaluate(
                        """(() => {
                          const doc = document.querySelector('.kpress-doc');
                          const style = getComputedStyle(doc);
                          const rootSize = parseFloat(
                            getComputedStyle(document.documentElement).fontSize);
                          const clearance = parseFloat(
                            style.getPropertyValue('--kpress-toc-toggle-clearance')) * rootSize;
                          return {
                            paddingLeft: parseFloat(style.paddingLeft),
                            clearance,
                            rootSize,
                          };
                        })()"""
                    )

                # Phone width: the reservation is deliberately dropped — the
                # gutter is the tight 0.5rem reading inset, well under the
                # clearance (the toggle's translucent fill covers the overlap).
                phone = doc_metrics()
                assert phone["paddingLeft"] == pytest.approx(0.5 * phone["rootSize"])
                assert phone["paddingLeft"] < phone["clearance"]

                # Tablet width, still inside the floating-toggle band: the
                # clearance reservation holds so prose never slides under the
                # control on mid widths.
                page.set_viewport_size({"width": 900, "height": 800})
                tablet = doc_metrics()
                assert tablet["paddingLeft"] >= tablet["clearance"]
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
