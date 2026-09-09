"""Real-browser regression for history-aware section navigation.

The browserless Vitest suite dispatches synthetic ``popstate`` events and
cancels native navigation, so it cannot establish the actual browser lifecycle
this feature exists to repair. The reload cases drive all three supported
engines through actual reload and Back/Forward; the Chromium section-navigation
checks also cover unstamped entries and the TOC "Contents" bare-# case. The
dedicated browser CI requires these tests rather than permitting skips.
"""

from __future__ import annotations

import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from kpress.publish import build_site

if TYPE_CHECKING:
    from playwright.sync_api import ConsoleMessage


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


FILLER = "\n\n".join(f"Paragraph {index} of filler prose." for index in range(40))


@pytest.mark.parametrize("browser_name", ["chromium", "firefox", "webkit"])
@pytest.mark.parametrize("fragment", ["", "#details"], ids=["plain", "fragment"])
@pytest.mark.parametrize("document_scroller", [False, True], ids=["pane", "document"])
def test_reload_restores_reader_pane_in_real_browser(
    tmp_path: Path, browser_name: str, fragment: str, document_scroller: bool
) -> None:
    required = os.environ.get("KPRESS_REQUIRE_BROWSER") == "1"
    api = (
        import_module("playwright.sync_api")
        if required
        else pytest.importorskip("playwright.sync_api")
    )
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "index.md").write_text(
        f"# Reload smoke\n\n[Details](#details)\n\n{FILLER}\n\n"
        f"## Details\n\n{FILLER}\n\n## Later\n\n{FILLER}\n",
        encoding="utf-8",
    )
    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n",
        encoding="utf-8",
    )
    build_site(config)
    # A minimal embedding host marks the document scroller. It uses the same
    # shipped history module but owns native layout and reload restoration.
    if document_scroller:
        (tmp_path / "public" / "native.html").write_text(
            "<!doctype html><html data-kpress-viewport><head>"
            "<style>body{margin:0;height:6500px}#details{margin-top:1800px}</style>"
            '<script type="module" src="/_kpress/assets/js/history.js"></script>'
            '</head><body><h1>Native host</h1><h2 id="details">Details</h2></body></html>',
            encoding="utf-8",
        )
    handler = partial(_QuietHandler, directory=str(tmp_path / "public"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with api.sync_playwright() as playwright:
            try:
                browser = getattr(playwright, browser_name).launch(headless=True)
            except api.Error as exc:
                if required:
                    raise
                pytest.skip(f"No Playwright {browser_name} available: {exc}")
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 720})
                lifecycle: list[str] = []

                def record_console(message: ConsoleMessage) -> None:
                    lifecycle.append(message.text)

                page.on("console", record_console)
                page.add_init_script(
                    """if (window === top) {
                      globalThis.__historyScrollCalls = [];
                      for (const owner of [window, Element.prototype]) {
                        const scrollTo = owner.scrollTo;
                        owner.scrollTo = function(...args) {
                          if (this === window || this === document.scrollingElement) {
                            globalThis.__historyScrollCalls.push(args);
                          }
                          return scrollTo.apply(this, args);
                        };
                      }
                      for (const type of ['pageshow', 'beforeunload', 'pagehide', 'popstate']) {
                        window.addEventListener(type, () => console.debug(
                          'history-lifecycle', JSON.stringify({type, state: history.state,
                            top: document.querySelector('[data-kpress-viewport]')?.scrollTop})));
                      }
                    }"""
                )

                def settle() -> None:
                    # Module readiness and a fresh document are distinct from the
                    # navigation event; the page also owns a blank video iframe.
                    page.wait_for_function(
                        "!globalThis.__reloadOldDocument && globalThis.kpress?.isReady "
                        "&& document.readyState === 'complete'"
                    )
                    page.evaluate(
                        """async () => {
                          await document.fonts.ready;
                          await new Promise(resolve => requestAnimationFrame(() =>
                            requestAnimationFrame(resolve)));
                        }"""
                    )

                def await_offset(offset: float) -> None:
                    try:
                        page.wait_for_function(
                            "offset => Math.abs(document.querySelector('[data-kpress-viewport]')"
                            ".scrollTop - offset) <= 1",
                            arg=offset,
                        )
                    except api.TimeoutError:
                        pytest.fail(f"{browser_name} {fragment} lifecycle: {lifecycle}")

                filename = "native.html" if document_scroller else ""
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/{filename}{fragment}")
                settle()
                page.evaluate(
                    """() => {
                      history.replaceState({...history.state, hostValue: 'retained'}, '');
                      document.querySelector('[data-kpress-viewport]')
                        .scrollTo({top: 2500, behavior: 'instant'});
                    }"""
                )
                # Establish that the shipped history behavior captured the pane,
                # rather than manufacturing the state the restoration must read.
                page.wait_for_function(
                    "history.state?.kpressScroll > 2400 && history.state.kpressScroll === "
                    "document.querySelector('[data-kpress-viewport]').scrollTop"
                )
                before = page.evaluate("document.querySelector('[data-kpress-viewport]').scrollTop")
                assert before > 2400
                with page.expect_navigation(wait_until="load"):
                    # Use the browser's reload action. Playwright's WebKit reload
                    # protocol resets scroll even for plain document-scrolled pages.
                    page.evaluate("globalThis.__reloadOldDocument = true; location.reload()")
                settle()
                after = page.evaluate("document.querySelector('[data-kpress-viewport]').scrollTop")
                native_fragment = document_scroller and browser_name == "webkit" and bool(fragment)
                if document_scroller:
                    assert page.evaluate("globalThis.__historyScrollCalls") == []
                if not native_fragment:
                    assert abs(after - before) <= 1, (
                        f"{browser_name} reload: {before} -> {after}; {lifecycle}"
                    )
                assert page.evaluate("history.state.hostValue") == "retained"
                assert page.evaluate("location.hash") == fragment
                assert (
                    page.evaluate("performance.getEntriesByType('navigation')[0].type") == "reload"
                )
                if native_fragment:
                    # Unchanged KPress 4a868bb reproduces WebKit preferring a real
                    # fragment over the native document offset. Preserve that
                    # browser behavior; the spy above rejects scripted restoration.
                    return

                # Reload in the same task as the scroll cannot wait for the
                # trailing stamp. The pane must flush before the browser takes
                # its reload snapshot; document hosts retain native restoration.
                with page.expect_navigation(wait_until="load"):
                    page.evaluate(
                        """() => {
                          document.querySelector('[data-kpress-viewport]')
                            .scrollTo({top: 2800, behavior: 'instant'});
                          globalThis.__reloadOldDocument = true;
                          location.reload();
                        }"""
                    )
                settle()
                await_offset(2800)
                assert page.evaluate("history.state.hostValue") == "retained"
                assert page.evaluate("location.hash") == fragment

                # A separate document exercises pagehide/pageshow and actual
                # Back/Forward, including browsers that use their page cache.
                page.goto("about:blank")
                page.go_back(wait_until="load")
                settle()
                await_offset(2800)
                assert page.evaluate("history.state.hostValue") == "retained"
                assert page.evaluate("location.hash") == fragment
                page.go_forward(wait_until="load")
                page.wait_for_url("about:blank")
                assert page.url == "about:blank"
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_hash_history_and_viewport_restoration_in_real_browser(tmp_path: Path) -> None:
    required = os.environ.get("KPRESS_REQUIRE_BROWSER") == "1"
    sync_api = (
        import_module("playwright.sync_api")
        if required
        else pytest.importorskip("playwright.sync_api")
    )
    (tmp_path / "content").mkdir()
    sections = "\n\n".join(f"## Part {index}\n\n{FILLER}" for index in range(1, 6))
    # Seven headings and forty paragraphs a section clears both TOC thresholds
    # (toc_min_headings, toc_min_words), so the Contents link exists.
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
                if required:
                    raise
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

                # Re-activating the current fragment matches native history:
                # no duplicate entry is pushed, the pane just scrolls.
                length_before = page.evaluate("history.length")
                page.locator('.kpress-prose a[href="#details"]').first.click()
                page.wait_for_function(
                    f"Math.abs(document.querySelector('[data-kpress-viewport]')"
                    f".scrollTop - {jumped}) < 200"
                )
                assert page.url.endswith("#details")
                assert page.evaluate("history.length") == length_before
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_unicode_anchor_consumers_agree_in_real_browser(tmp_path: Path) -> None:
    required = os.environ.get("KPRESS_REQUIRE_BROWSER") == "1"
    sync_api = (
        import_module("playwright.sync_api")
        if required
        else pytest.importorskip("playwright.sync_api")
    )
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "index.md").write_text(
        "# Unicode anchor smoke\n\n"
        "[Preview Café](#caf%C3%A9-notes)\n\n"
        f"## Early\n\n{FILLER}\n\n"
        f"## Café Notes\n\n{FILLER}\n\n"
        f"## Café Notes\n\n{FILLER}\n\n"
        f"## Привет 世界\n\n{FILLER}\n\n"
        # Padding sections: the anchors under test are the three above, but the
        # TOC they are read from is only rendered once the document clears
        # toc_min_headings.
        f"## Padding One\n\n{FILLER}\n\n"
        f"## Padding Two\n\n{FILLER}\n\n"
        "## Last\n\nDone.\n",
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
                if required:
                    raise
                try:
                    browser = playwright.chromium.launch(headless=True, channel="chrome")
                except sync_api.Error as exc:
                    pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")
            try:
                page = browser.new_page(viewport={"width": 1400, "height": 700})
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")

                authored_link = page.locator('.kpress-prose a[href="#caf%C3%A9-notes"]')
                authored_link.hover()
                tooltip = page.locator(".kpress-tooltip")
                tooltip.wait_for(state="visible", timeout=3_000)
                assert "Café Notes" in tooltip.inner_text()
                page.keyboard.press("Escape")

                first_toc = page.locator('.kpress-toc a[href="#café-notes"]')
                first_toc.click()
                page.wait_for_url("**/#caf%C3%A9-notes")
                assert page.evaluate("document.getElementById('café-notes')?.textContent") == (
                    "Café Notes"
                )

                duplicate_toc = page.locator('.kpress-toc a[href="#café-notes-1"]')
                duplicate_toc.click()
                page.wait_for_url("**/#caf%C3%A9-notes-1")
                assert page.evaluate("document.getElementById('café-notes-1')?.textContent") == (
                    "Café Notes"
                )

                page.go_back()
                page.wait_for_url("**/#caf%C3%A9-notes")
                assert page.evaluate("document.getElementById('café-notes')?.id") == "café-notes"

                page.evaluate(
                    """(() => {
                      const pane = document.querySelector('[data-kpress-viewport]');
                      const heading = document.getElementById('привет-世界');
                      pane.scrollTop = heading.offsetTop - 20;
                    })()"""
                )
                page.wait_for_function(
                    """document.querySelector(
                      '.kpress-toc a[href="#привет-世界"]'
                    )?.getAttribute('data-active') === 'true'"""
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
