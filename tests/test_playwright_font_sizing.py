"""Real-browser regression for the root-independent sizing contract.

Every KPress font size derives from ``--kpress-font-size-base`` via
``calc(base * ratio)`` (see the SIZING POLICY comment in style-tokens.css and
kpress-design.md "Sizing Policy"). Two invariants follow, and both need a real
cascade — browserless DOM emulation resolves neither ``calc()`` chains over
custom properties nor root font-size changes:

- default base (``1rem``): all sizes scale proportionally with the root font
  size, preserving the designed ratios (reader font preferences keep working);
- pinned base (a host setting ``--kpress-host-font-size-base``): all computed
  sizes are identical regardless of the root font size (an embedded document
  scales as one unit the host controls).

The viewport stays at 700px so the >=64rem heading step-up band never engages
at either tested root (64rem is 832px at 13px and 1024px at 16px): container
bands are deliberately root-relative and out of scope here.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from kpress.publish import build_site

DESIGN_RATIOS = {"h1": 1.7, "h2": 1.32, "code": 0.82, "bullet": 0.9}


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _build_fixture_site(tmp_path: Path) -> Path:
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "index.md").write_text(
        "# Sizing smoke\n\n"
        "Body prose with `inline code` for the mono ratio.\n\n"
        "## Section\n\n"
        "- A bulleted item so the marker renders.\n",
        encoding="utf-8",
    )
    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n",
        encoding="utf-8",
    )
    build_site(config)
    return tmp_path / "public"


_METRICS_SCRIPT = """(() => {
  const px = (value) => parseFloat(value);
  const prose = document.querySelector('.kpress-prose > p, .kpress-prose p');
  const li = document.querySelector('.kpress-prose ul > li');
  return {
    body: px(getComputedStyle(prose).fontSize),
    h1: px(getComputedStyle(document.querySelector('.kpress-prose h1')).fontSize),
    h2: px(getComputedStyle(document.querySelector('.kpress-prose h2')).fontSize),
    code: px(getComputedStyle(document.querySelector('.kpress-prose code')).fontSize),
    bullet: px(getComputedStyle(li, '::before').fontSize),
  };
})()"""


def _assert_design_ratios(sizes: dict[str, float]) -> None:
    for key, ratio in DESIGN_RATIOS.items():
        assert sizes[key] == pytest.approx(sizes["body"] * ratio, abs=0.1), key


def test_sizes_pin_with_base_and_scale_without_it(tmp_path: Path) -> None:
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
                    # System Chrome fallback, matching the clearance smoke.
                    browser = playwright.chromium.launch(headless=True, channel="chrome")
                except sync_api.Error as exc:
                    pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")
            try:
                page = browser.new_page(viewport={"width": 700, "height": 900})
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")

                def sizes_at(root_px: int, host_base: str | None) -> dict[str, float]:
                    page.evaluate(
                        """([rootPx, hostBase]) => {
                          const root = document.documentElement;
                          root.style.fontSize = rootPx + 'px';
                          if (hostBase === null) {
                            root.style.removeProperty('--kpress-host-font-size-base');
                          } else {
                            root.style.setProperty('--kpress-host-font-size-base', hostBase);
                          }
                        }""",
                        [root_px, host_base],
                    )
                    return page.evaluate(_METRICS_SCRIPT)

                # Default base: the document tracks the root (reader preference)
                # and keeps the designed ratios at every root size.
                at_16 = sizes_at(16, None)
                at_13 = sizes_at(13, None)
                assert at_16["body"] == pytest.approx(16.0, abs=0.1)
                assert at_13["body"] == pytest.approx(13.0, abs=0.1)
                _assert_design_ratios(at_16)
                _assert_design_ratios(at_13)
                for key, value in at_13.items():
                    assert value == pytest.approx(at_16[key] * 13 / 16, abs=0.1), key

                # Pinned base: one host knob makes every size root-independent —
                # identical computed pixels at both roots, ratios intact.
                pinned_16 = sizes_at(16, "17px")
                pinned_13 = sizes_at(13, "17px")
                assert pinned_16["body"] == pytest.approx(17.0, abs=0.1)
                _assert_design_ratios(pinned_16)
                for key, value in pinned_13.items():
                    assert value == pytest.approx(pinned_16[key], abs=0.05), key
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
