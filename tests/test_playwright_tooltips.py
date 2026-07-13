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


def test_tooltip_hover_position_and_escape_in_real_browser(tmp_path: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "index.md").write_text(
        "# Tooltip smoke\n\n[Jump to details](#details)\n\n"
        "## Details\n\nPositioned preview content.\n",
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
            except sync_api.Error as exc:
                pytest.skip(f"Playwright Chromium is not installed: {exc}")
            try:
                page = browser.new_page(viewport={"width": 1000, "height": 700})
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                page.locator('a[href="#details"]').hover()
                tooltip = page.locator(".kpress-tooltip")
                tooltip.wait_for(state="visible", timeout=3_000)

                box = tooltip.bounding_box()
                assert box is not None
                assert box["x"] >= 0 and box["y"] >= 0
                assert box["x"] + box["width"] <= 1000
                assert box["y"] + box["height"] <= 700

                page.keyboard.press("Escape")
                tooltip.wait_for(state="hidden", timeout=1_000)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
