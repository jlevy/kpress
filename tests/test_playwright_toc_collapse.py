"""Real-browser regression for the collapsible TOC.

The browserless Vitest suite drives the grouping predicate and ARIA state with
synthetic clicks, but it cannot observe the IntersectionObserver scroll-spy or
the CSS row-collapse motion. This optional smoke drives real Chromium through
the flows the plan pins: initial collapsed state, expand-all / collapse-all,
scroll-follow group handoff, TOC click into a collapsed group, and the
reduced-motion suppression of the collapse transition.
"""

from __future__ import annotations

import re
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from kpress.publish import build_site


def _class_pattern(class_name: str) -> re.Pattern[str]:
    return re.compile(rf"(^|\s){class_name}(\s|$)")


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


FILLER = "\n\n".join(f"Paragraph {index} of filler prose." for index in range(30))


def _build_collapse_site(tmp_path: Path) -> Path:
    (tmp_path / "content").mkdir()
    sections = "\n\n".join(
        f"## Part {index}\n\n{FILLER}\n\n"
        f"### Sub {index}.1\n\n{FILLER}\n\n"
        f"### Sub {index}.2\n\n{FILLER}"
        for index in range(1, 4)
    )
    (tmp_path / "content" / "index.md").write_text(
        f"# Collapse smoke\n\n{sections}\n", encoding="utf-8"
    )
    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: content\n"
        "publish:\n  output_dir: public\n  asset_mode: linked\n"
        "format:\n  toc_collapse_depth: 1\n",
        encoding="utf-8",
    )
    build_site(config)
    return tmp_path / "public"


def _launch_browser(sync_api: Any) -> tuple[Any, Any]:
    """Start Playwright and launch headless Chromium, skipping if unavailable.

    The playwright module arrives via importorskip, so it is typed as Any.
    """
    playwright = sync_api.sync_playwright().start()
    try:
        browser = playwright.chromium.launch(headless=True)
    except sync_api.Error:
        try:
            # Fall back to an installed Google Chrome so the smoke also runs on
            # machines without the managed Chromium download.
            browser = playwright.chromium.launch(headless=True, channel="chrome")
        except sync_api.Error as exc:
            playwright.stop()
            pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")
    return playwright, browser


def test_toc_collapse_expand_all_and_scroll_follow_in_real_browser(tmp_path: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    public = _build_collapse_site(tmp_path)

    handler = partial(_QuietHandler, directory=str(public))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    playwright, browser = _launch_browser(sync_api)
    try:
        page = browser.new_page(viewport={"width": 1400, "height": 700})
        page.goto(f"http://127.0.0.1:{server.server_address[1]}/")

        def row(href: str):
            return page.locator(f'.kpress-toc .toc-list li:has(a[href="{href}"])')

        collapsed = "kpress-toc-collapsed"
        expect = sync_api.expect

        # Initial state: at the top the scroll-spy activates Part 1, so its
        # group rides scroll-follow while the other groups start collapsed.
        expect(row("#sub-1-1")).not_to_have_class(_class_pattern(collapsed))
        expect(row("#sub-2-1")).to_have_class(_class_pattern(collapsed))
        expect(row("#sub-3-1")).to_have_class(_class_pattern(collapsed))
        # A collapsed row occupies no space once the motion settles.
        expect(row("#sub-2-1")).not_to_be_visible()

        # Expand-all: every group opens and the button flips state.
        button = page.locator("[data-kpress-toc-expand-all]")
        button.click()
        expect(button).to_have_attribute("aria-expanded", "true")
        expect(button).to_have_attribute("aria-label", "Collapse all sections")
        expect(row("#sub-2-1")).not_to_have_class(_class_pattern(collapsed))
        expect(row("#sub-2-1")).to_be_visible()

        # Collapse-all returns to the baseline, which keeps the active group.
        button.click()
        expect(button).to_have_attribute("aria-expanded", "false")
        expect(row("#sub-1-1")).not_to_have_class(_class_pattern(collapsed))
        expect(row("#sub-2-1")).to_have_class(_class_pattern(collapsed))

        # Scroll-follow handoff: reaching Part 3 expands its group and
        # collapses Part 1's.
        page.evaluate("document.getElementById('sub-3-1').scrollIntoView()")
        expect(row("#sub-3-1")).not_to_have_class(_class_pattern(collapsed))
        expect(row("#sub-1-1")).to_have_class(_class_pattern(collapsed))

        # TOC click into a collapsed group: the spine entry stays clickable and
        # its group expands on arrival.
        page.locator('.kpress-toc a[href="#part-2"]').click()
        expect(row("#sub-2-1")).not_to_have_class(_class_pattern(collapsed))
        expect(row("#sub-3-1")).to_have_class(_class_pattern(collapsed))
    finally:
        browser.close()
        playwright.stop()
        server.shutdown()
        thread.join(timeout=5)


def test_toc_collapse_applies_without_transition_under_reduced_motion(tmp_path: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    public = _build_collapse_site(tmp_path)

    handler = partial(_QuietHandler, directory=str(public))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    playwright, browser = _launch_browser(sync_api)
    try:
        page = browser.new_page(viewport={"width": 1400, "height": 700}, reduced_motion="reduce")
        page.goto(f"http://127.0.0.1:{server.server_address[1]}/")

        # The global prefers-reduced-motion block must suppress the row motion.
        duration = page.evaluate(
            "getComputedStyle(document.querySelector('.kpress-toc .toc-list li'))"
            ".transitionDuration"
        )
        assert all(part.strip() in {"0.00001s", "1e-05s"} for part in duration.split(",")), duration

        # State changes still apply instantly.
        button = page.locator("[data-kpress-toc-expand-all]")
        button.click()
        sync_api.expect(
            page.locator('.kpress-toc .toc-list li:has(a[href="#sub-2-1"])')
        ).to_be_visible()
    finally:
        browser.close()
        playwright.stop()
        server.shutdown()
        thread.join(timeout=5)
