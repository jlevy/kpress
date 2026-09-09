from __future__ import annotations

import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from kpress.publish import build_site


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _launch_browser(playwright: Any, sync_api: Any) -> Any:
    try:
        return playwright.chromium.launch(headless=True)
    except sync_api.Error:
        try:
            return playwright.chromium.launch(headless=True, channel="chrome")
        except sync_api.Error as exc:
            message = f"No Playwright Chromium or system Chrome available: {exc}"
            if os.environ.get("CI"):
                pytest.fail(message)
            pytest.skip(message)


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
            browser = _launch_browser(playwright, sync_api)
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


def test_footnote_keyboard_activation_navigates_in_real_browser(tmp_path: Path) -> None:
    """Keyboard path for footnote content: the preview is a pointer/touch
    affordance, so Enter on the focused ref must run native navigation to the
    in-document footnote, dismiss the preview, and leave the footnote's inner
    link reachable with Tab."""
    sync_api = pytest.importorskip("playwright.sync_api")
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "index.md").write_text(
        "# Footnote keyboard smoke\n\nA claim with a source.[^1]\n\n"
        "[^1]: See the [reference site](https://example.com) for detail.\n",
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
            browser = _launch_browser(playwright, sync_api)
            try:
                page = browser.new_page(viewport={"width": 1000, "height": 700})
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")

                ref = page.locator('a[href^="#fn-"]').first
                ref.focus()
                tooltip = page.locator(".kpress-tooltip")
                tooltip.wait_for(state="visible", timeout=3_000)

                page.keyboard.press("Enter")
                tooltip.wait_for(state="hidden", timeout=1_000)
                assert "#fn-" in page.url

                # Focus stays on the ref after native hash navigation; the
                # footnote's real link is reachable by keyboard from there.
                page.keyboard.press("Tab")
                focused_href = page.evaluate("document.activeElement?.getAttribute('href')")
                assert focused_href == "https://example.com"
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_mobile_footnote_preview_has_explicit_and_tap_dismissal(tmp_path: Path) -> None:
    """The touch sheet closes from its x, a repeat tap, its body, or outside it."""
    sync_api = pytest.importorskip("playwright.sync_api")
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "index.md").write_text(
        "# Footnote touch smoke\n\nA claim with a source.[^1]\n\n"
        "[^1]: Footnote body text without a link.\n",
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
            browser = _launch_browser(playwright, sync_api)
            try:
                context = browser.new_context(
                    viewport={"width": 390, "height": 700},
                    has_touch=True,
                    is_mobile=True,
                )
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                ref = page.locator('a[href^="#fn-"]').first
                tooltip = page.locator(".kpress-tooltip")

                ref.tap()
                tooltip.wait_for(state="visible", timeout=3_000)
                close = tooltip.locator(".kpress-tooltip-close")
                assert close.get_attribute("aria-label") == "Close tooltip"
                assert close.text_content() == "×"
                box_style = tooltip.evaluate(
                    """node => {
                      const style = getComputedStyle(node);
                      return {
                        paddingLeft: style.paddingLeft,
                        paddingRight: style.paddingRight,
                        borderLeftWidth: style.borderLeftWidth,
                        borderRightWidth: style.borderRightWidth,
                        borderLeftColor: style.borderLeftColor,
                        borderRightColor: style.borderRightColor,
                      };
                    }"""
                )
                assert box_style["paddingLeft"] == box_style["paddingRight"] == "16px"
                assert box_style["borderLeftWidth"] == box_style["borderRightWidth"] == "1px"
                assert box_style["borderLeftColor"] == box_style["borderRightColor"]

                close.tap()
                tooltip.wait_for(state="hidden", timeout=1_000)

                ref.tap()
                tooltip.wait_for(state="visible", timeout=3_000)
                ref.tap()
                tooltip.wait_for(state="hidden", timeout=1_000)

                ref.tap()
                tooltip.wait_for(state="visible", timeout=3_000)
                tooltip.locator(".kpress-tooltip-content").tap(position={"x": 8, "y": 8})
                tooltip.wait_for(state="hidden", timeout=1_000)

                ref.tap()
                tooltip.wait_for(state="visible", timeout=3_000)
                page.get_by_role("heading", name="Footnote touch smoke").tap()
                tooltip.wait_for(state="hidden", timeout=1_000)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
