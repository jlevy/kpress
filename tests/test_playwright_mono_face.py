"""Real-browser regression for the face code is actually set in.

``--kpress-font-mono`` names ``Planetaire Mono Text`` and then the platform stack
behind it, and computed style reports the whole list whichever one drew the glyphs. The
question this module asks -- did the reader get the shipped face or their own Menlo? --
is only answerable from the browser, through ``CSS.getPlatformFontsForNode``, which
names the face Chromium resolved and says whether it came from a web font.

Two documents, four readings:

- the default: an inline ``code`` span and a fenced block both resolve to a custom face
  whose family is ``Planetaire Mono Text``, on screen and under print media alike (the
  faces are declared outside ``@media``, so print must not change the answer);
- ``format.mono_font: system``: the same span resolves to a face that is **not** a web
  font, and the page never asks the server for a Planetaire file, because none is
  declared and none was published.

The system case deliberately does not name a family. Chromium reports the platform's
mono under whatever name that platform gives it -- ``Menlo`` on macOS, ``DejaVu Sans
Mono`` or ``Liberation Mono`` on a Linux runner -- so ``isCustomFont`` is the portable
form of "this came from the machine, not from KPress", the same reasoning
``test_playwright_print_sans_face.py`` uses for its own platform-independent reads.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

import pytest

from devtools.subset_mono import FAMILY
from kpress.publish import build_site

#: An inline code span inside a paragraph, and a fenced block: the two shapes a reader
#: meets code in, and two different rules in components.css.
_INLINE = ".kpress-prose p code"
_BLOCK = ".kpress-prose pre code"

_BODY = (
    "# Mono face\n\n"
    "A paragraph that mentions `render_page(document, options)` inline.\n\n"
    "```python\n"
    "def measure(face: str) -> int:\n"
    "    return len(face)  # 0123456789\n"
    "```\n"
)


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


def _build_fixture_site(tmp_path: Path, *, mono_font: str | None) -> Path:
    (tmp_path / "content").mkdir(parents=True)
    (tmp_path / "content" / "index.md").write_text(_BODY, encoding="utf-8")
    fmt = "" if mono_font is None else f"format:\n  mono_font: {mono_font}\n"
    (tmp_path / "kpress.yml").write_text(
        f"sources:\n  - path: content\npublish:\n  output_dir: public\n  asset_mode: linked\n{fmt}",
        encoding="utf-8",
    )
    build_site(tmp_path / "kpress.yml")
    return tmp_path / "public"


def _platform_font(session: Any, selector: str) -> dict[str, Any]:
    """The face Chromium drew most of a node's glyphs with, as it reports it."""
    root = cast(dict[str, Any], session.send("DOM.getDocument", {"depth": -1}))
    found = cast(
        dict[str, Any],
        session.send("DOM.querySelector", {"nodeId": root["root"]["nodeId"], "selector": selector}),
    )
    assert found["nodeId"], f"no node for {selector}"
    result = cast(
        dict[str, Any],
        session.send("CSS.getPlatformFontsForNode", {"nodeId": found["nodeId"]}),
    )
    fonts = cast(list[dict[str, Any]], result["fonts"])
    assert fonts, f"no platform fonts reported for {selector}"
    return max(fonts, key=lambda font: cast(int, font["glyphCount"]))


def _settled(
    page: Any, session: Any, selector: str, media: str, want: str | None
) -> dict[str, Any]:
    """Switch media, let the face load, and read it back.

    One session serves every read: detaching one resets the emulated media on the
    tested Chromium, so a fresh session per read would measure the page back on screen.
    ``want`` is the family the reading has to arrive at; ``None`` means any answer will
    do, which is the system case, where the face is already installed and never loads.
    """
    page.emulate_media(media=media)
    page.evaluate("document.fonts.ready")
    if want is None:
        return _platform_font(session, selector)
    for _ in range(30):
        font = _platform_font(session, selector)
        if cast(str, font["familyName"]) == want:
            return font
        page.wait_for_timeout(100)
        page.evaluate("document.fonts.ready")
    return _platform_font(session, selector)


def _launch(playwright: Any, sync_api: Any) -> Any:
    try:
        return playwright.chromium.launch(headless=True)
    except sync_api.Error:
        try:
            return playwright.chromium.launch(headless=True, channel="chrome")
        except sync_api.Error as exc:
            pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")


def _read_faces(
    public: Path, reads: list[tuple[str, str]], want: str | None
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Read one face per (selector, media) pair, and every URL the page requested."""
    sync_api = pytest.importorskip("playwright.sync_api")
    handler = partial(_QuietHandler, directory=str(public))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    requested: list[str] = []
    faces: dict[str, dict[str, Any]] = {}
    try:
        with sync_api.sync_playwright() as playwright:
            browser = _launch(playwright, sync_api)
            try:
                context = browser.new_context(viewport={"width": 900, "height": 900})
                page = context.new_page()
                page.on("request", lambda request: requested.append(cast(str, request.url)))  # pyright: ignore[reportUnknownLambdaType]
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
                page.wait_for_selector(_INLINE)
                session = context.new_cdp_session(page)
                try:
                    session.send("DOM.enable")
                    session.send("CSS.enable")
                    for selector, media in reads:
                        faces[f"{selector}|{media}"] = _settled(
                            page, session, selector, media, want
                        )
                finally:
                    session.detach()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    return faces, requested


def test_code_is_set_in_the_shipped_mono_face_on_screen_and_in_print(tmp_path: Path) -> None:
    public = _build_fixture_site(tmp_path, mono_font=None)
    reads = [(selector, media) for selector in (_INLINE, _BLOCK) for media in ("screen", "print")]

    faces, requested = _read_faces(public, reads, FAMILY)

    for selector, media in reads:
        font = faces[f"{selector}|{media}"]
        assert font["isCustomFont"], (selector, media, font)
        assert font["familyName"] == FAMILY, (selector, media, font)
        # The regular subset, by the name upstream gives it: the subsetting keeps the
        # upstream identity rather than renaming, so this is the PostScript name a PDF
        # would carry too.
        assert font["postScriptName"] == "PlanetaireMonoText-Regular", (selector, media, font)

    # And the reader paid for the three styles this page reaches, not the four it
    # declares. That gap is the whole argument for the default set: declaring a face
    # is not loading it, so covering every style the stylesheets ask for costs a page
    # nothing until the style appears on it.
    #
    # This fixture is Python: the fenced block sets keywords at 700 and its comment at
    # italic 400, so three faces load. Nothing here is italic AND 700 -- Pygments'
    # Python lexer emits no such token; C's `#include` does -- so bold-italic is
    # declared, never requested, and the reader never pays for it.
    fetched = sorted({url.rsplit("/", 1)[-1] for url in requested if "planetaire-mono-text" in url})
    assert fetched == [
        "planetaire-mono-text-latin-400-italic.woff2",
        "planetaire-mono-text-latin-400-normal.woff2",
        "planetaire-mono-text-latin-700-normal.woff2",
    ], fetched
    declared = sorted({url.rsplit("/", 1)[-1] for url in requested if "mono-planetaire" in url})
    assert declared == [
        "mono-planetaire-400-italic.css",
        "mono-planetaire-400-normal.css",
        "mono-planetaire-700-italic.css",
        "mono-planetaire-700-normal.css",
    ], declared


def test_system_mono_leaves_code_to_the_platform(tmp_path: Path) -> None:
    public = _build_fixture_site(tmp_path, mono_font="system")

    faces, requested = _read_faces(public, [(_INLINE, "screen"), (_INLINE, "print")], None)

    for media in ("screen", "print"):
        font = faces[f"{_INLINE}|{media}"]
        # Not a web font, whatever this platform calls its mono.
        assert not font["isCustomFont"], (media, font)
        assert font["familyName"] != FAMILY, (media, font)
    # Nothing was declared, so nothing was asked for -- and nothing was published:
    # `mono_font: system` prunes the faces from the build, not just from the cascade.
    assert not [url for url in requested if "planetaire" in url], requested
    assert not list((public / "_kpress" / "assets" / "fonts").glob("planetaire*"))
    assert not list((public / "_kpress" / "assets" / "css").glob("mono-planetaire*"))
