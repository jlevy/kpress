"""Observe visible mathematics during delayed loads, including its native fallback."""

from __future__ import annotations

import os
import re
from collections.abc import Generator
from contextlib import contextmanager
from importlib import import_module
from pathlib import Path
from typing import Any, TypedDict

import pytest

from .math_font_probe import FONT_ADVANCE_INIT
from .test_playwright_math_text_face import (
    _build_fixture_site,  # pyright: ignore[reportPrivateUsage]
    _launch,  # pyright: ignore[reportPrivateUsage]
    _serve,  # pyright: ignore[reportPrivateUsage]
)

_DELAY_ALL = """(() => {
  const gate = new Promise(resolve => { globalThis.releaseMathFonts = resolve; });
  const faceLoad = FontFace.prototype.load;
  FontFace.prototype.load = function(...args) {
    return faceLoad.apply(this, args).then(face => gate.then(() => face));
  };
  const fontSet = Object.getPrototypeOf(document.fonts);
  const setLoad = fontSet.load;
  fontSet.load = function(...args) {
    return setLoad.apply(this, args).then(faces => gate.then(() => faces));
  };
})();"""

_DELAY_CONSTRUCT = """(() => {
  const gate = new Promise(resolve => { globalThis.releaseMathFonts = resolve; });
  const fontSet = Object.getPrototypeOf(document.fonts);
  const check = fontSet.check;
  fontSet.check = function(spec, text) {
    return spec.includes('KaTeX_Size2') ? false : check.call(this, spec, text);
  };
  const load = fontSet.load;
  fontSet.load = function(spec, text) {
    const faces = load.call(this, spec, text);
    if (!spec.includes('KaTeX_Size2')) return faces;
    globalThis.constructRequested = true;
    return faces.then(value => gate.then(() => value));
  };
})();"""


def _omit_native(route: Any) -> None:
    route.fulfill(body="")


@contextmanager
def _page(
    public: Path, *, script: str = "", javascript: bool = True, native: bool = True
) -> Generator[Any]:
    required = os.environ.get("KPRESS_REQUIRE_BROWSER") == "1"
    api = (
        import_module("playwright.sync_api")
        if required
        else pytest.importorskip("playwright.sync_api")
    )
    server, thread = _serve(public)
    try:
        with api.sync_playwright() as playwright:
            browser = (
                playwright.chromium.launch(headless=True) if required else _launch(playwright, api)
            )
            try:
                context = browser.new_context(java_script_enabled=javascript)
                context.add_init_script(FONT_ADVANCE_INIT)
                if not native:
                    context.route("**/katex-init.js", _omit_native)
                if script:
                    context.add_init_script(script)
                page = context.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_address[1]}/", wait_until="domcontentloaded"
                )
                yield page
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_native_fallback_does_not_flash_during_font_preparation(tmp_path: Path) -> None:
    public = _build_fixture_site(tmp_path, math_text_font=None)
    with _page(public, script=_DELAY_ALL) as page:
        page.wait_for_function("globalThis.kpressMathFaceWait?.length > 0")
        assert page.locator(".kpress-math-semantic").count() == 2
        assert not page.locator(".kpress-math-semantic").first.is_visible()
        assert page.locator(".katex").count() == 0
        page.evaluate("releaseMathFonts()")
        page.wait_for_selector(".katex")
        page.wait_for_function("!document.documentElement.dataset.kpressMathPending")
        assert page.locator(".kpress-math-semantic").first.evaluate(
            "el => getComputedStyle(el).clipPath === 'inset(50%)'"
        )


def test_mathml_stays_readable_without_javascript(tmp_path: Path) -> None:
    public = _build_fixture_site(tmp_path, math_text_font=None)
    with _page(public, javascript=False) as page:
        assert page.locator(".kpress-math-semantic").first.is_visible()
        assert page.locator(".katex").count() == 0


def test_large_operator_waits_for_its_font_without_loading_every_family(tmp_path: Path) -> None:
    public = _build_fixture_site(
        tmp_path, math_text_font=None, markdown="# Sum\n\n$$\\sum_{i=1}^n i$$\n"
    )
    with _page(public, script=_DELAY_CONSTRUCT) as page:
        page.wait_for_function(
            "globalThis.constructRequested === true || !document.documentElement.dataset.kpressMathPending"
        )
        assert page.evaluate("globalThis.constructRequested === true")
        assert page.locator(".katex").count() == 1
        assert not page.locator(".katex").is_visible()
        assert not page.evaluate(
            "[...document.fonts].some(f => f.family === 'KaTeX_AMS' && f.status === 'loaded')"
        )
        page.evaluate("releaseMathFonts()")
        page.wait_for_selector(".katex")
        assert page.locator(".katex").is_visible()


def test_failed_required_font_restores_readable_mathml(tmp_path: Path) -> None:
    public = _build_fixture_site(
        tmp_path, math_text_font=None, markdown="# Sum\n\n$$\\sum_{i=1}^n i$$\n"
    )
    broken = _DELAY_CONSTRUCT.replace(
        "return faces.then(value => gate.then(() => value));",
        "return faces.then(() => Promise.reject(new Error('font unavailable')));",
    )
    with _page(public, script=broken) as page:
        page.wait_for_function(
            "globalThis.constructRequested === true || !document.documentElement.dataset.kpressMathPending"
        )
        assert page.evaluate("globalThis.constructRequested === true")
        page.wait_for_function("!document.documentElement.dataset.kpressMathPending")
        assert page.locator(".kpress-math-semantic").is_visible()
        assert not page.locator(".katex").is_visible()
        assert page.locator('[data-kpress-math-rendered="true"]').count() == 0


def test_host_first_render_waits_keeps_latest_and_supports_mixed_faces(tmp_path: Path) -> None:
    public = _build_fixture_site(tmp_path, math_text_font=None)
    with _page(public, script=_DELAY_ALL, native=False) as page:
        page.evaluate("""() => {
          const article = document.querySelector('.kpress');
          for (const id of ['host-sans', 'host-serif', 'host-stock']) {
            const node = document.createElement('span');
            node.id = id;
            article.append(node);
          }
          const target = document.getElementById('host-sans');
          const context = { isSansContext: () => true };
          const first = kpressMathText.render('9', target, {}, context);
          const latest = kpressMathText.render('1', target, {}, context);
          Promise.all([first, latest]).then(results => {
            globalThis.hostResults = results;
          });
        }""")
        assert page.locator("#host-sans .katex").count() == 0
        page.evaluate("releaseMathFonts()")
        page.wait_for_function("globalThis.hostResults?.length === 2")
        assert page.evaluate("hostResults.map(result => result.status)") == [
            "superseded",
            "ready",
        ]
        assert page.locator("#host-sans .katex-html").inner_text() == "1"
        page.evaluate("""async () => {
          await kpressMathText.render('1', document.getElementById('host-serif'));
          const stock = document.getElementById('host-stock');
          stock.dataset.kpressMathText = 'katex';
          await kpressMathText.render('1', stock);
          const sansParent = document.createElement('span');
          sansParent.dataset.kpressMathFace = 'sans';
          document.querySelector('.kpress').append(sansParent);
          const nested = document.createElement('span');
          nested.id = 'host-nested-stock';
          nested.dataset.kpressMathText = 'katex';
          sansParent.append(nested);
          await kpressMathText.render('1', nested);
          const tooltip = document.createElement('div');
          tooltip.className = 'kpress-tooltip kpress-tooltip-footnote';
          tooltip.dataset.kpressMathText = 'prose';
          const clone = stock.cloneNode(true);
          clone.id = 'host-tooltip-stock';
          tooltip.append(clone);
          document.body.append(tooltip);
          kpressMathText.complete();
        }""")
        advances = page.evaluate("""() => ['sans', 'serif', 'stock', 'nested-stock', 'tooltip-stock'].map(kind => {
          const glyph = document.querySelector('#host-' + kind + ' .katex-html .mord');
          return __kpressFontAdvance(glyph);
        })""")
        assert advances == pytest.approx([0.497, 0.533, 0.500, 0.500, 0.500], abs=0.001)
        assert page.locator('[data-kpress-math-face="katex"] .katex').evaluate_all(
            "nodes => nodes.every(node => !getComputedStyle(node).fontFamily.includes('KPress Math Text'))"
        )
        assert page.locator(".kpress-math-render .katex").count() == 0


_FALLBACK_MARKDOWN = (
    "# Composite fallback\n\n"
    "In prose $\\frac{4001}{4000}$.\n\n"
    "| Caption math |\n| --- |\n| $\\frac{4001}{4000}$ |\n"
)
_FALLBACK_PROBE = """() => [...document.querySelectorAll('.kpress-math-render')].map(node => {
  const digits = [...node.querySelectorAll('.katex-html .mord')].find(
    el => el.textContent === '4001' && !el.children.length
  );
  return {
    advance: __kpressFontAdvance(digits) / 4,
    height: parseFloat(node.querySelector('.mfrac .vlist').style.height),
    family: getComputedStyle(digits).fontFamily,
    profile: node.dataset.kpressMathFace ?? 'prose',
  };
})"""


class _MathFaceProbe(TypedDict):
    advance: float
    height: float
    family: str
    profile: str


@pytest.mark.parametrize("missing", ["stylesheet", "both", "serif"])
def test_missing_composite_uses_matching_stock_fonts_and_metrics(
    tmp_path: Path, missing: str
) -> None:
    references: dict[str, list[_MathFaceProbe]] = {}
    for name, mode in (("custom", None), ("stock", "katex")):
        public = _build_fixture_site(
            tmp_path / name, math_text_font=mode, markdown=_FALLBACK_MARKDOWN
        )
        with _page(public) as page:
            page.wait_for_function("!document.documentElement.dataset.kpressMathPending")
            references[name] = page.evaluate(_FALLBACK_PROBE)

    public = _build_fixture_site(
        tmp_path / "missing", math_text_font=None, markdown=_FALLBACK_MARKDOWN
    )
    stylesheet = public / "_kpress/assets/katex/katex-text-face.css"
    if missing == "stylesheet":
        stylesheet.unlink()
    else:
        css = re.sub(r"/\*.*?\*/", "", stylesheet.read_text(), flags=re.DOTALL)

        def omit_composite(match: re.Match[str]) -> str:
            block = match.group()
            if 'font-family: "KPress Math Text";' in block or (
                missing == "both" and 'font-family: "KPress Math Text Sans";' in block
            ):
                return ""
            return block

        stylesheet.write_text(re.sub(r"@font-face\s*\{[^}]*\}", omit_composite, css))

    with _page(public) as page:
        page.wait_for_function("!document.documentElement.dataset.kpressMathPending")
        actual: list[_MathFaceProbe] = page.evaluate(_FALLBACK_PROBE)
        assert page.locator('[data-kpress-math-rendered="true"]').count() == 2
        assert any(entry["outcome"] == "empty" for entry in page.evaluate("kpressMathFaceWait"))

    for index, result in enumerate(actual):
        reference = references["custom" if missing == "serif" and index == 1 else "stock"][index]
        assert result["family"] == reference["family"]
        assert result["advance"] == pytest.approx(reference["advance"], abs=0.001)
        assert result["height"] == pytest.approx(reference["height"], abs=0.001)
        assert result["profile"] == ("sans" if missing == "serif" and index == 1 else "katex")


@pytest.mark.parametrize("weight", ["400", "700"])
def test_required_font_failure_differs_from_an_unused_weight(tmp_path: Path, weight: str) -> None:
    public = _build_fixture_site(
        tmp_path, math_text_font=None, markdown="# Fonts\n\n$\\frac{4001}{4000}$.\n"
    )
    (public / f"_kpress/assets/fonts/pt-serif-latin-{weight}-normal.woff2").unlink()
    with _page(public) as page:
        page.wait_for_function("!document.documentElement.dataset.kpressMathPending")
        assert any(entry["outcome"] == "error" for entry in page.evaluate("kpressMathFaceWait"))
        if weight == "400":
            assert page.locator('[data-kpress-math-rendered="true"]').count() == 0
            assert page.locator(".kpress-math-semantic").is_visible()
        else:
            assert page.locator('[data-kpress-math-rendered="true"]').count() == 1
            result = page.evaluate(_FALLBACK_PROBE)[0]
            assert result["profile"] == "prose"
            assert "KPress Math Text" in result["family"]
            assert result["advance"] == pytest.approx(0.533, abs=0.001)
