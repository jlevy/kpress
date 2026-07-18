"""Real-browser regression for history-aware section navigation.

The browserless Vitest suite dispatches synthetic ``popstate`` events and
cancels native navigation, so it cannot establish the actual browser lifecycle
this feature exists to repair. This optional smoke drives real Chromium
through the flows the plan pins: section-link click -> Back -> Forward
(including the fast traversal into an entry that has not yet received its
debounced stamp), and the TOC "Contents" bare-# case.
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


FILLER = "\n\n".join(f"Paragraph {index} of filler prose." for index in range(40))


def test_hash_history_and_viewport_restoration_in_real_browser(tmp_path: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    (tmp_path / "content").mkdir()
    sections = "\n\n".join(f"## Part {index}\n\n{FILLER}" for index in range(1, 4))
    # Enough headings for the TOC (toc_min_headings) so the Contents link exists.
    (tmp_path / "content" / "index.md").write_text(
        "# History smoke\n\n"
        f"[Jump to details](#details)\n\n## Early\n\n{FILLER}\n\n"
        f"## Details\n\n{FILLER}\n\n{sections}\n",
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
                    # Fall back to an installed Google Chrome so the smoke also
                    # runs on machines without the managed Chromium download.
                    browser = playwright.chromium.launch(headless=True, channel="chrome")
                except sync_api.Error as exc:
                    pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")
            try:
                page = browser.new_page(viewport={"width": 1400, "height": 700})
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                pane = page.locator("[data-kpress-viewport]")

                def pane_top() -> float:
                    return page.evaluate(
                        "document.querySelector('[data-kpress-viewport]').scrollTop"
                    )

                assert pane.count() == 1

                # Section-link click: the history behavior pushes the hash
                # entry and glides the pane, so wait for the scroll to settle
                # (equal across two polls past the threshold) before sampling
                # the landed offset.
                page.locator('.kpress-prose a[href="#details"]').first.click()
                page.wait_for_function(
                    """(() => {
                      const pane = document.querySelector('[data-kpress-viewport]');
                      if (pane.scrollTop <= 200) { window.__kpSettled = undefined; return false; }
                      if (window.__kpSettled === pane.scrollTop) return true;
                      window.__kpSettled = pane.scrollTop;
                      return false;
                    })()"""
                )
                assert page.url.endswith("#details")
                jumped = pane_top()

                # Back immediately (before any debounced stamp lands on the
                # #details entry): the pre-click offset is restored.
                page.go_back()
                page.wait_for_function(
                    "document.querySelector('[data-kpress-viewport]').scrollTop < 50"
                )
                assert "#details" not in page.url

                # Forward into the hash entry: fragment fallback (unstamped) or
                # stamp both land the reader on the section.
                page.go_forward()
                page.wait_for_function(
                    f"Math.abs(document.querySelector('[data-kpress-viewport]')"
                    f".scrollTop - {jumped}) < 200"
                )
                assert page.url.endswith("#details")

                # Contents (bare #): clears the hash, pushes an entry, scrolls
                # the pane to the top; Back returns to the section offset.
                before_top = pane_top()
                page.locator("[data-kpress-toc-top]").click()
                page.wait_for_function(
                    "document.querySelector('[data-kpress-viewport]').scrollTop < 50"
                )
                assert not page.url.endswith("#details")
                page.go_back()
                page.wait_for_function(
                    f"Math.abs(document.querySelector('[data-kpress-viewport]')"
                    f".scrollTop - {before_top}) < 200"
                )
                assert page.url.endswith("#details")
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
