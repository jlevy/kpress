"""Real-browser regression for the reading measure: the width chain honours
``--kpress-measure``, and honours it identically in every band.

Both claims are container-query and cascade behaviour that browserless DOM
emulation does not evaluate, so neither can be asserted anywhere but a real
engine. They are the two halves of one bug: ``--kpress-measure`` is a pinned
public fragment token documented as *the* reading-width knob, but the three caps
that bound the column each hard-coded or under-counted it, so a host that set it
moved the article and left the text where it was — and the same token meant "the
text" in the wide band and "the text plus two insets" in the single-column one,
a 10rem step in reading width across the 75rem boundary.

Panes are sized inside a wider window throughout, so a viewport-keyed rule shows
up as a mismatch rather than passing by coincidence.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from kpress.format import DocumentInput, RenderOptions, read_package_text, render_fragment

WINDOW_WIDTH_PX = 2000
# One pane either side of the 75rem sidebar floor. Both are wide enough to show
# the whole measure, so the comparison is about the bands agreeing and not about
# a pane running out: the measure is a max-width, and a single-column pane below
# measure + 2x inset + 2x gutter (912px at the defaults) legitimately clamps.
WIDE_PANE_PX = 1300
TABLET_PANE_PX = 1000

_SECTION_BODY = " ".join(["body"] * 120)
LONG = "# Title\n\nintro\n\n" + "".join(f"## Section {i}\n\n{_SECTION_BODY}\n\n" for i in range(8))


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _page_html(
    pane_px: int,
    measure: str | None = None,
    host_base: str | None = None,
    include_toc: str = "auto",
    toc_rail: str = "reserved",
) -> str:
    """Render the long fixture in a pane, with optional host overrides.

    ``measure`` goes on the ``.kpress`` scope, which is where kpress-design.md
    tells embedding hosts to set fragment tokens; ``host_base`` goes on
    ``:root``, which is where it tells them to pin the type base.
    """

    rendered = render_fragment(
        DocumentInput(
            title="Doc",
            source_text=LONG,
            source_path="doc.md",
            body_markdown=LONG,
            trust_mode="sanitized",
            metadata={},
        ),
        RenderOptions(
            widgets={"settings": "off"},
            toc_rail=toc_rail,  # pyright: ignore[reportArgumentType]
            include_toc=include_toc,  # pyright: ignore[reportArgumentType]
        ),
    )
    css = "\n".join(
        read_package_text(rel_path)
        for rel_path in ("css/style-tokens.css", "css/document.css", "css/components.css")
    )
    override = f".kpress {{ --kpress-measure: {measure}; }}" if measure else ""
    if host_base:
        override += f":root {{ --kpress-host-font-size-base: {host_base}; }}"
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{css}{override}</style></head><body style='margin:0'>"
        '<div class="kpress-frame">'
        f'<div class="kpress-viewport" style="inline-size: {pane_px}px">'
        f"{rendered.html}</div></div></body></html>"
    )


# The reading measure is the TEXT width, so the probe subtracts the column's own
# padding. Measuring the column box instead would hide exactly the defect here:
# the box can be right while the text inside it is an inset-pair too narrow.
_PROBE = """(() => {
  const prose = document.querySelector('.kpress-long-text');
  const rect = prose.getBoundingClientRect();
  const styles = getComputedStyle(prose);
  return Math.round(
    rect.width - parseFloat(styles.paddingLeft) - parseFloat(styles.paddingRight)
  );
})()"""


def _run_probe(tmp_path: Path, pages: dict[str, str], probe: str) -> dict[str, Any]:
    """Serve each named page, evaluate ``probe`` in Chromium, return the results."""

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
                    browser = playwright.chromium.launch(headless=True, channel="chrome")
                except sync_api.Error as exc:
                    pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")
            try:
                page = browser.new_page(viewport={"width": WINDOW_WIDTH_PX, "height": 900})
                measured: dict[str, Any] = {}
                for name in pages:
                    page.goto(f"http://127.0.0.1:{server.server_address[1]}/{name}.html")
                    measured[name] = page.evaluate(probe)
                return measured
            finally:
                browser.close()
    finally:
        server.shutdown()
        thread.join()


def _measure_text_widths(tmp_path: Path, pages: dict[str, str]) -> dict[str, Any]:
    return _run_probe(tmp_path, pages, _PROBE)


def test_the_reading_measure_is_the_same_width_in_every_band(tmp_path: Path) -> None:
    """One token, one reading width — no step at a band boundary.

    Before the width chain was written from the tokens, crossing 75rem of pane
    moved the text between 48rem and 38rem: the wide band's grid track added the
    inset back, and the single-column cap did not.
    """

    measured = _measure_text_widths(
        tmp_path,
        {
            "wide": _page_html(WIDE_PANE_PX),
            "tablet": _page_html(TABLET_PANE_PX),
        },
    )

    # Sub-pixel layout rounding only; a band that forgets an inset is off by
    # whole rem.
    assert abs(measured["wide"] - measured["tablet"]) <= 1, measured


def test_a_host_measure_override_changes_the_text_width_in_every_band(
    tmp_path: Path,
) -> None:
    """The public token has to actually reach the text.

    Asserted per band because the defect was band-shaped: the single-column cap
    responded weakly (the article's allowance leaked through while the column
    stayed pinned to a literal) and the wide band's fixed track ignored the
    token outright.
    """

    # Well clear of the default and still inside the wide band's floor guard, so
    # the assertion is about the token being read, not about the pane running out.
    override = "calc(var(--kpress-font-size-base) * 30)"
    measured = _measure_text_widths(
        tmp_path,
        {
            "wide_default": _page_html(WIDE_PANE_PX),
            "wide_override": _page_html(WIDE_PANE_PX, measure=override),
            "tablet_default": _page_html(TABLET_PANE_PX),
            "tablet_override": _page_html(TABLET_PANE_PX, measure=override),
        },
    )

    # 30 * the 1rem default base, i.e. 480px of text, in both bands.
    assert measured["wide_override"] == pytest.approx(480, abs=1), measured
    assert measured["tablet_override"] == pytest.approx(480, abs=1), measured
    assert measured["wide_override"] < measured["wide_default"], measured
    assert measured["tablet_override"] < measured["tablet_default"], measured


def test_the_measure_tracks_the_type_base_not_the_root(tmp_path: Path) -> None:
    """A host that pins the type base keeps its characters per line.

    This is why the default is calc(base * N) rather than a root-relative
    length: with a pinned base the column has to scale with the text, or the
    same document reads at a different line length than it was designed for.
    """

    measured = _measure_text_widths(
        tmp_path,
        {
            "default_base": _page_html(WIDE_PANE_PX),
            # Three quarters of the 16px default base; the column should follow.
            "small_base": _page_html(WIDE_PANE_PX, host_base="12px"),
        },
    )

    assert measured["small_base"] == pytest.approx(measured["default_base"] * 0.75, rel=0.02), (
        measured
    )


# The reading column's inner padding, which a host sizing its own surfaces to
# the documented wide track ("measure + 2 x 2.5rem") has to be able to rely on.
_INSET_PROBE = """(() => {
  const prose = document.querySelector('.kpress-long-text');
  const styles = getComputedStyle(prose);
  return Math.round(parseFloat(styles.paddingLeft));
})()"""


def _measure_insets(tmp_path: Path, pages: dict[str, str]) -> dict[str, Any]:
    return _run_probe(tmp_path, pages, _INSET_PROBE)


def test_the_wide_band_inset_does_not_depend_on_whether_a_toc_was_rendered(
    tmp_path: Path,
) -> None:
    """The wide band's inset is the band's, not the grid's.

    0.3.3 applied it through a selector that matched with or without a TOC.
    Gating it on ``:has(.kpress-toc)`` moved every TOC-less wide document from
    2.5rem to 4rem: the text still landed at the measure, because the caps
    follow the inset, so only a host sizing its own surfaces to the documented
    wide track saw it -- its panels no longer lined up with the document inside
    them. Embedding a README with ``include_toc="off"`` is exactly that case.
    """

    measured = _measure_insets(
        tmp_path,
        {
            "with_toc": _page_html(WIDE_PANE_PX),
            "no_toc": _page_html(WIDE_PANE_PX, include_toc="off", toc_rail="auto"),
        },
    )

    assert measured["no_toc"] == measured["with_toc"], measured
    # 2.5rem against the 16px default root.
    assert measured["with_toc"] == 40, measured


def test_a_toc_less_wide_document_still_reads_at_the_measure(tmp_path: Path) -> None:
    """The band-consistency claim, for the embedding case specifically."""

    measured = _measure_text_widths(
        tmp_path,
        {
            "wide_no_toc": _page_html(WIDE_PANE_PX, include_toc="off", toc_rail="auto"),
            "tablet_no_toc": _page_html(TABLET_PANE_PX, include_toc="off", toc_rail="auto"),
        },
    )

    assert abs(measured["wide_no_toc"] - measured["tablet_no_toc"]) <= 1, measured
