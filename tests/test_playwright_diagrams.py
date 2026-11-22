"""Real-browser checks of the diagram module's security claims, with real Mermaid.

The Vitest suite drives `diagrams.js` with a stand-in Mermaid, so it cannot show what
Mermaid itself does with a hostile label or directive. These tests load the pinned
Mermaid development dependency (`package.json`) beside the shipped module, in a page
whose content security policy admits no inline style, and check:

- image placement loads nothing a label names, in every kind of diagram, whatever the
  host config or the diagram's own `%%{init}%%` or front matter asks for, and keeps the
  label's formatting; Mermaid's image shape is the known exception (strict xfail);
- a host's or a diagram's `securityLevel: "loose"` is refused;
- two bindings drawing at once each draw in their own configuration;
- the measuring host's style survives a policy without `'unsafe-inline'`.

The dedicated browser CI requires these tests rather than permitting skips.
"""

from __future__ import annotations

import json
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

    from playwright.sync_api import Page

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src/kpress/format/static"
MERMAID_DIST = ROOT / "node_modules/mermaid/dist"

# No inline style of any kind: no `<style>` element and no `style` attribute.
POLICY = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:"

# A label whose HTML, drawn as an HTML label, loads an image from the host's origin.
PAYLOAD = "A[\"<b>bold</b><br/><img src='/pixel.svg?from=label' width='8'> start\"] --> B[end]"

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Diagrams</title></head>
<body>{body}</body></html>
"""


def figure(source: str) -> str:
    escaped = source.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        '<figure class="kpress-diagram kpress-mermaid" data-kpress-diagram="mermaid" '
        'data-kpress-diagram-status="source"><pre class="kpress-diagram-source">'
        f'<code class="language-mermaid">{escaped}</code></pre></figure>'
    )


class _Handler(SimpleHTTPRequestHandler):
    """Serves the shipped modules, the pinned Mermaid, and one page, recording requests."""

    pages: ClassVar[dict[str, str]] = {}
    requests: ClassVar[list[str]] = []

    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)

    def end_headers(self) -> None:
        self.send_header("Content-Security-Policy", POLICY)
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def translate_path(self, path: str) -> str:
        path = path.split("?", 1)[0]
        for prefix, root in (("/kpress/", STATIC), ("/mermaid/", MERMAID_DIST)):
            if path.startswith(prefix):
                return str(root / path[len(prefix) :])
        return str(ROOT / "tests/fixtures/__missing__")

    def do_GET(self) -> None:
        self.requests.append(self.path)
        name = self.path.split("?", 1)[0].lstrip("/")
        if name in self.pages:
            body = self.pages[name].encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if name == "pixel.svg":
            body = b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>'
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


@pytest.fixture
def page() -> Iterator[tuple[Page, str]]:
    required = os.environ.get("KPRESS_REQUIRE_BROWSER") == "1"
    if not (MERMAID_DIST / "mermaid.esm.min.mjs").is_file():
        if required:
            pytest.fail("Mermaid is not installed: run `npm ci`")
        pytest.skip("Mermaid is not installed: run `npm ci`")
    api = (
        import_module("playwright.sync_api")
        if required
        else pytest.importorskip("playwright.sync_api")
    )
    _Handler.pages = {}
    _Handler.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with api.sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
            except api.Error as exc:
                if required:
                    raise
                pytest.skip(f"No Playwright chromium available: {exc}")
            try:
                tab = browser.new_page()
                yield tab, f"http://127.0.0.1:{server.server_address[1]}"
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


def draw(page: Page, origin: str, body: str, bindings: list[dict[str, Any]]) -> Any:
    """Load *body*, bind each `{root, options}` at once, and return each figure's result."""

    _Handler.pages["page.html"] = PAGE.format(body=body)
    page.goto(f"{origin}/page.html")
    return page.evaluate(
        """async (bindings) => {
          const { initKpressDiagrams } = await import('/kpress/js/diagrams.js');
          const mermaid = await import('/mermaid/mermaid.esm.min.mjs');
          const started = bindings.map(({ root, options }) =>
            initKpressDiagrams(root ? document.getElementById(root) : document, {
              mermaid,
              subscribeTheme: () => () => {},
              yieldBetween: () => Promise.resolve(),
              ...options,
            }));
          await Promise.all(started.map((binding) => binding.ready));
          // An <img> decodes after the binding settles; let any label image load too.
          await Promise.all([...document.images].map((image) => image.decode().catch(() => {})));
          await new Promise((resolve) => setTimeout(resolve, 300));
          const theme = (figure) => {
            const css = figure.querySelector('.kpress-diagram-rendered style')?.textContent ?? '';
            return /#ececff/i.test(css) ? 'default' : /#1f2020/i.test(css) ? 'dark' : null;
          };
          return {
            figures: [...document.querySelectorAll('figure')].map((figure) => {
              const image = figure.querySelector('.kpress-diagram-rendered > img');
              return {
                section: figure.closest('section')?.id ?? null,
                status: figure.dataset.kpressDiagramStatus,
                error: figure.querySelector('.kpress-diagram-error-detail')?.textContent ?? null,
                drawing: image ? 'img' : figure.querySelector('.kpress-diagram-rendered > svg') ? 'svg' : null,
                width: image?.naturalWidth ?? 0,
                svg: image ? decodeURIComponent(image.src.slice(image.src.indexOf(',') + 1))
                  : figure.querySelector('.kpress-diagram-rendered')?.innerHTML ?? '',
                theme: theme(figure),
              };
            }),
            securityLevel: mermaid.default.mermaidAPI.getSiteConfig().securityLevel,
          };
        }""",
        bindings,
    )


HOSTILE_HOST_CONFIG = {
    "securityLevel": "loose",
    "htmlLabels": True,
    "dompurifyConfig": {"ADD_TAGS": ["img"], "ADD_ATTR": ["src", "style"]},
}


def test_image_placement_loads_nothing_a_label_names(page: tuple[Page, str]) -> None:
    tab, origin = page
    sources = [
        f"flowchart LR\n  {PAYLOAD}",
        '%%{init: {"securityLevel": "loose", '
        '"dompurifyConfig": {"ADD_TAGS": ["img"], "ADD_ATTR": ["src"]}}}%%\n'
        f"flowchart LR\n  {PAYLOAD}",
        "---\nconfig:\n  htmlLabels: true\n  flowchart:\n    htmlLabels: true\n---\n"
        f"flowchart LR\n  {PAYLOAD}",
    ]
    result = draw(
        tab,
        origin,
        "".join(figure(source) for source in sources),
        [{"root": None, "options": {"placement": "image", "config": HOSTILE_HOST_CONFIG}}],
    )

    assert [f["status"] for f in result["figures"]] == ["rendered"] * 3, result["figures"]
    assert [f["drawing"] for f in result["figures"]] == ["img"] * 3
    assert all(f["width"] > 0 for f in result["figures"])
    # The labels are SVG text: no HTML label, and the payload is inert text in the image.
    assert not [path for path in _Handler.requests if "pixel.svg" in path], _Handler.requests
    # The label keeps its formatting, as GitHub draws it.
    assert all("<b>bold</b>" in f["svg"] for f in result["figures"]), result["figures"]
    assert result["securityLevel"] == "strict"


def pixel(name: str) -> str:
    return f"<img src='/pixel.svg?from={name}' width='8'>"


# Every place a diagram puts author text, and each way Mermaid itself loads a resource.
EVERY_KIND = {
    "edge": f'flowchart LR\n  A -->|"{pixel("edge")} go"| B',
    "subgraph": f'flowchart LR\n  subgraph S["{pixel("subgraph")} group"]\n    A\n  end',
    "shape": 'flowchart LR\n  A@{ img: "/pixel.svg?from=shape", label: "x", w: 60, h: 60 }\n  A --> B',
    "css": "flowchart LR\n  A --> B\n  style A fill:url(/pixel.svg?from=css)",
    "class-css": (
        "flowchart LR\n  A:::bg --> B\n  classDef bg background-image:url(/pixel.svg?from=classdef)"
    ),
    "sequence": (
        f"sequenceDiagram\n  Alice->>Bob: {pixel('message')} hi\n"
        f"  Note over Alice: {pixel('note')} note"
    ),
    "state": f"stateDiagram-v2\n  s1 : {pixel('state')} state\n  [*] --> s1",
    "class": f'classDiagram\n  class Animal["{pixel("class")} Animal"]',
    "mindmap": f"mindmap\n  root(({pixel('mindmap')} root))\n    child",
}


@pytest.mark.parametrize(
    "kind",
    [
        pytest.param(
            kind,
            marks=pytest.mark.xfail(
                strict=True,
                reason="Mermaid loads an image shape's URL itself during layout; "
                "a host bounds it with img-src",
            ),
        )
        if kind == "shape"
        else kind
        for kind in sorted(EVERY_KIND)
    ],
)
def test_image_placement_loads_nothing_in_any_diagram(page: tuple[Page, str], kind: str) -> None:
    tab, origin = page
    result = draw(
        tab,
        origin,
        figure(EVERY_KIND[kind]),
        [{"root": None, "options": {"placement": "image", "config": HOSTILE_HOST_CONFIG}}],
    )
    [drawn] = result["figures"]
    assert drawn["status"] in {"rendered", "error"}, drawn
    assert not [path for path in _Handler.requests if "pixel.svg" in path], (
        _Handler.requests,
        drawn["status"],
        drawn["error"],
    )


def test_the_payload_is_live_in_document_placement(page: tuple[Page, str]) -> None:
    """The control: the same label does load in document placement, for trusted content."""

    tab, origin = page
    result = draw(
        tab,
        origin,
        figure(f"flowchart LR\n  {PAYLOAD}"),
        [{"root": None, "options": {"placement": "document"}}],
    )
    assert result["figures"][0]["drawing"] == "svg"
    assert [path for path in _Handler.requests if "pixel.svg" in path]


def test_a_diagram_cannot_lower_the_security_level(page: tuple[Page, str]) -> None:
    tab, origin = page
    source = (
        '%%{init: {"securityLevel": "loose"}}%%\n'
        'flowchart LR\n  A --> B\n  click A href "javascript:globalThis.__clicked=1"\n'
    )
    result = draw(tab, origin, figure(source), [{"root": None, "options": {}}])

    [drawn] = result["figures"]
    assert drawn["status"] == "rendered", drawn
    assert "javascript:" not in drawn["svg"]
    assert result["securityLevel"] == "strict"


def test_bindings_drawing_at_once_keep_their_own_configuration(
    page: tuple[Page, str],
) -> None:
    tab, origin = page
    body = (
        '<section id="light" data-kpress-resolved-theme="light">'
        + figure("flowchart LR\n  A1 --> B1\n  B1 --> C1")
        + figure("flowchart LR\n  A2 --> B2")
        + '</section><section id="dark" data-kpress-resolved-theme="dark">'
        + figure("flowchart LR\n  X1 --> Y1")
        + figure("flowchart LR\n  X2 --> Y2")
        + "</section>"
    )
    result = draw(
        tab,
        origin,
        body,
        [
            {"root": "light", "options": {}},
            {"root": "dark", "options": {}},
        ],
    )
    themes = {(f["section"], f["theme"]) for f in result["figures"]}
    assert themes == {("light", "default"), ("dark", "dark")}, json.dumps(result["figures"])


def test_image_placement_measures_under_a_policy_without_inline_style(
    page: tuple[Page, str],
) -> None:
    """Mermaid measures labels in KPress's host, in Mermaid's font, though the page admits
    no `style` attribute; measured in the page's font, the image's labels would clip.

    The policy still reports violations here, from Mermaid's own inline styles and from
    parsing its SVG into the image; those cost nothing, since the image applies its styles
    outside the page.
    """

    tab, origin = page
    _Handler.pages["page.html"] = PAGE.format(
        body=figure("flowchart LR\n  A[A label wide enough to clip] --> B[Another long label]")
    )
    tab.goto(f"{origin}/page.html")
    result = tab.evaluate(
        """async () => {
          const { initKpressDiagrams } = await import('/kpress/js/diagrams.js');
          const real = (await import('/mermaid/mermaid.esm.min.mjs')).default;
          const measured = [];
          const mermaid = {
            initialize: (config) => real.initialize(config),
            render: (id, text, container) => {
              const style = getComputedStyle(container);
              measured.push({ position: style.position, visibility: style.visibility,
                family: style.fontFamily, size: style.fontSize });
              return real.render(id, text, container);
            },
          };
          const binding = initKpressDiagrams(document, {
            mermaid, placement: 'image', subscribeTheme: () => () => {},
          });
          await binding.ready;
          const figure = document.querySelector('figure');
          const image = figure.querySelector('.kpress-diagram-rendered > img');
          await image?.decode();
          return { measured, status: figure.dataset.kpressDiagramStatus,
            width: image?.naturalWidth ?? 0 };
        }"""
    )
    assert result["status"] == "rendered" and result["width"] > 0, result
    [measured] = result["measured"]
    assert measured["position"] == "fixed"
    assert measured["visibility"] == "hidden"
    assert measured["size"] == "16px"
    assert "trebuchet ms" in measured["family"]
