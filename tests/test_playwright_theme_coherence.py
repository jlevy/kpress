"""Real-browser regressions for theme ownership and coherent CSS resolution.

style-tokens.css keys every palette (and `color-scheme`) on exactly one input,
``data-kpress-resolved-theme``, read from either an ancestor scope (`:root` or
any host wrapper) or the element itself, with the element winning (see the
SELECTOR GRAMMAR comment there). These assertions need a real cascade: they
exercise :where()-flattened source-order ties and specificity across scopes,
which browserless DOM emulation does not resolve.

The harness embeds the SAME theme-agnostic fragment twice — one article gets
stamped per scenario, the sibling stays ambient — and snapshots computed
background, ``color-scheme``, and the code-surface token per state:

- ancestor scoping works from `:root` and from a plain host wrapper;
- a stamped element is a coherent island in BOTH directions (dark-in-light and
  light-in-dark), with `color-scheme` agreeing with the palette in every state
  (the historical split-brain: palette dark + color-scheme light);
- the mode attribute (``data-kpress-theme``) never keys CSS;
- the warm palette composes with both themes, including the explicit
  warm+light element combination.

The second harness loads every selected fragment module after document ready.
It proves those assets cannot overwrite a host-stamped theme, consult KPress
theme storage, or bind an OS-theme listener unless the render explicitly opts
into the standalone resolver.
"""

from __future__ import annotations

import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from kpress.format import (
    AssetManifest,
    DocumentInput,
    RenderOptions,
    materialize_package_assets,
    read_package_text,
    render_fragment,
)


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


_SNAPSHOT_SCRIPT = """(() => {
  const pick = (selector) => {
    const article = document.querySelector(selector);
    const style = getComputedStyle(article);
    return {
      bg: style.backgroundColor,
      scheme: style.colorScheme,
      codeBg: style.getPropertyValue('--kpress-doc-code-bg').trim(),
    };
  };
  return { a: pick('#wrap-a .kpress'), b: pick('#wrap-b .kpress') };
})()"""


def _late_load_page(fragment_html: str, module_urls: list[str]) -> str:
    """Return a host-owned theme shell that loads fragment modules after ready."""

    return f"""<!doctype html>
<html data-kpress-resolved-theme="light">
<head>
  <meta charset="utf-8">
  <script>
    localStorage.setItem("kpress.theme", "dark");
    window.__kpressThemeAudit = {{ done: false, listeners: 0, mutations: [] }};
    const audit = window.__kpressThemeAudit;
    new MutationObserver((records) => {{
      for (const record of records) {{
        audit.mutations.push({{
          attribute: record.attributeName,
          oldValue: record.oldValue,
          value: document.documentElement.getAttribute(record.attributeName),
        }});
      }}
    }}).observe(document.documentElement, {{
      attributes: true,
      attributeOldValue: true,
      attributeFilter: ["data-kpress-theme", "data-kpress-resolved-theme"],
    }});
    window.matchMedia = (query) => ({{
      matches: query === "(prefers-color-scheme: dark)",
      media: query,
      onchange: null,
      addEventListener(type) {{
        if (type === "change") audit.listeners += 1;
      }},
      removeEventListener(type) {{
        if (type === "change") audit.listeners -= 1;
      }},
      addListener() {{ audit.listeners += 1; }},
      removeListener() {{ audit.listeners -= 1; }},
      dispatchEvent() {{ return true; }},
    }});
    addEventListener("load", async () => {{
      for (const url of {json.dumps(module_urls)}) await import(url);
      await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      audit.done = true;
    }}, {{ once: true }});
  </script>
</head>
<body>
  <div class="kpress-widget kpress-settings" data-kpress-widget="settings"></div>
  {fragment_html}
</body>
</html>
"""


def _module_entry_urls(manifest: AssetManifest) -> list[str]:
    urls: list[str] = []
    for asset in manifest.browser_entry_points():
        if asset.loading != "module":
            continue
        assert asset.public_url is not None
        urls.append(asset.public_url)
    return urls


def test_resolved_theme_is_coherent_at_every_scope(tmp_path: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    fragment = render_fragment(
        DocumentInput(
            title="Theme smoke",
            source_text="# Theme smoke\n\nBody with `code`.\n",
            source_path="doc.md",
            body_markdown="# Theme smoke\n\nBody with `code`.\n",
        ),
        RenderOptions(include_toc="off", widgets={"settings": "off"}),
    )
    css = "\n".join(
        read_package_text(rel_path)
        for rel_path in ("css/style-tokens.css", "css/document.css", "css/components.css")
    )
    (tmp_path / "index.html").write_text(
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{css}</style></head><body style='margin:0'>"
        f'<div id="wrap-a">{fragment.html}</div>'
        f'<div id="wrap-b">{fragment.html}</div>'
        "</body></html>",
        encoding="utf-8",
    )

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
                    # System Chrome fallback, matching the other Playwright smokes.
                    browser = playwright.chromium.launch(headless=True, channel="chrome")
                except sync_api.Error as exc:
                    pytest.skip(f"No Playwright Chromium or system Chrome available: {exc}")
            try:
                page = browser.new_page(viewport={"width": 900, "height": 700})
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/")

                def snapshot(setup: list[list[str]]) -> dict[str, dict[str, str]]:
                    page.evaluate(
                        """(setup) => {
                          const root = document.documentElement;
                          const articleA = document.querySelector('#wrap-a .kpress');
                          const wrapB = document.querySelector('#wrap-b');
                          for (const el of [root, articleA, wrapB]) {
                            el.removeAttribute('data-kpress-resolved-theme');
                            el.removeAttribute('data-kpress-theme');
                            el.removeAttribute('data-kpress-palette');
                          }
                          for (const [target, attr, value] of setup) {
                            const el = target === 'root' ? root
                              : target === 'article-a' ? articleA : wrapB;
                            el.setAttribute(attr, value);
                          }
                        }""",
                        setup,
                    )
                    return page.evaluate(_SNAPSHOT_SCRIPT)

                resolved = "data-kpress-resolved-theme"

                baseline = snapshot([])
                light_bg = baseline["a"]["bg"]
                assert baseline["b"]["bg"] == light_bg
                assert baseline["a"]["scheme"] == "light"

                # Ancestor scope at :root themes every article (the standalone
                # shell and the metabrowser-style root-stamping host).
                root_dark = snapshot([["root", resolved, "dark"]])
                dark_bg = root_dark["a"]["bg"]
                assert dark_bg != light_bg
                assert root_dark["b"]["bg"] == dark_bg
                assert root_dark["a"]["scheme"] == "dark"
                assert root_dark["b"]["scheme"] == "dark"

                # Ancestor scope on a plain host wrapper (no :root access):
                # only the wrapped article follows it.
                wrapped = snapshot([["wrap-b", resolved, "dark"]])
                assert wrapped["b"]["bg"] == dark_bg
                assert wrapped["b"]["scheme"] == "dark"
                assert wrapped["a"]["bg"] == light_bg
                assert wrapped["a"]["scheme"] == "light"

                # Element beats ancestor, both directions, color-scheme in
                # agreement — a stamped element is a coherent island, never the
                # historical dark-palette-with-light-controls split.
                dark_island = snapshot([["article-a", resolved, "dark"]])
                assert dark_island["a"]["bg"] == dark_bg
                assert dark_island["a"]["scheme"] == "dark"
                assert dark_island["b"]["bg"] == light_bg
                light_island = snapshot(
                    [["root", resolved, "dark"], ["article-a", resolved, "light"]]
                )
                assert light_island["a"]["bg"] == light_bg
                assert light_island["a"]["scheme"] == "light"
                assert light_island["b"]["bg"] == dark_bg

                # The mode attribute is resolver state: it never keys CSS.
                mode_only = snapshot([["article-a", "data-kpress-theme", "dark"]])
                assert mode_only["a"]["bg"] == light_bg
                assert mode_only["a"]["scheme"] == "light"

                # Palette composes with both themes; the explicit warm+light
                # element combination binds at full strength under a dark root.
                neutral_light_code = baseline["a"]["codeBg"]
                warm_light = snapshot([["root", "data-kpress-palette", "warm"]])
                assert warm_light["a"]["codeBg"] != neutral_light_code
                warm_dark = snapshot(
                    [["root", resolved, "dark"], ["root", "data-kpress-palette", "warm"]]
                )
                assert warm_dark["a"]["codeBg"] != warm_light["a"]["codeBg"]
                assert warm_dark["a"]["bg"] == dark_bg
                warm_light_island = snapshot(
                    [
                        ["root", resolved, "dark"],
                        ["article-a", resolved, "light"],
                        ["article-a", "data-kpress-palette", "warm"],
                    ]
                )
                assert warm_light_island["a"]["bg"] == light_bg
                assert warm_light_island["a"]["codeBg"] == warm_light["a"]["codeBg"]
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_late_fragment_assets_preserve_host_theme_ownership(tmp_path: Path) -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    markdown = """# Theme host

[Jump to details](#details)

```python
print("theme")
```

## Details

| Owner | Theme |
| --- | --- |
| Host | Light |
"""
    document = DocumentInput(
        title="Theme host",
        source_text=markdown,
        source_path="theme-host.md",
        body_markdown=markdown,
    )
    host_owned = render_fragment(
        document,
        RenderOptions(
            asset_url_prefix="/assets/",
            include_toc="on",
            widgets={"settings": "on"},
        ),
    )
    resolver_owned = render_fragment(
        document,
        RenderOptions(
            asset_url_prefix="/assets/",
            include_toc="on",
            widgets={"settings": "on"},
            include_theme_resolver=True,
        ),
    )

    host_entries = {asset.id for asset in host_owned.assets.browser_entry_points()}
    assert "js/settings-widget.js" in host_entries
    assert "js/theme.js" not in host_entries
    assert "js/theme.js" in {asset.id for asset in resolver_owned.assets.browser_entry_points()}

    materialize_package_assets(
        host_owned.assets.merged(resolver_owned.assets),
        tmp_path / "assets",
    )
    (tmp_path / "host-owned.html").write_text(
        _late_load_page(host_owned.html, _module_entry_urls(host_owned.assets)),
        encoding="utf-8",
    )
    (tmp_path / "resolver-owned.html").write_text(
        _late_load_page(resolver_owned.html, _module_entry_urls(resolver_owned.assets)),
        encoding="utf-8",
    )

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
                page = browser.new_page(viewport={"width": 900, "height": 700})
                origin = f"http://127.0.0.1:{server.server_address[1]}"

                page.goto(f"{origin}/host-owned.html")
                page.wait_for_function("window.__kpressThemeAudit.done === true")
                host_state = page.evaluate(
                    """() => ({
                      mode: document.documentElement.getAttribute('data-kpress-theme'),
                      resolved: document.documentElement.dataset.kpressResolvedTheme,
                      stored: localStorage.getItem('kpress.theme'),
                      listeners: window.__kpressThemeAudit.listeners,
                      mutations: window.__kpressThemeAudit.mutations,
                    })"""
                )
                assert host_state == {
                    "mode": None,
                    "resolved": "light",
                    "stored": "dark",
                    "listeners": 0,
                    "mutations": [],
                }

                requested = page.evaluate(
                    """() => {
                      const requests = [];
                      window.kpress.on('theme:request', (detail) => requests.push(detail));
                      document.querySelector('[data-kpress-theme-choice="dark"]').click();
                      return {
                        requests,
                        mode: document.documentElement.getAttribute('data-kpress-theme'),
                        resolved: document.documentElement.dataset.kpressResolvedTheme,
                        stored: localStorage.getItem('kpress.theme'),
                      };
                    }"""
                )
                assert requested == {
                    "requests": [{"mode": "dark"}],
                    "mode": None,
                    "resolved": "light",
                    "stored": "dark",
                }

                page.goto(f"{origin}/resolver-owned.html")
                page.wait_for_function("window.__kpressThemeAudit.done === true")
                resolver_state = page.evaluate(
                    """() => ({
                      mode: document.documentElement.dataset.kpressTheme,
                      resolved: document.documentElement.dataset.kpressResolvedTheme,
                      stored: localStorage.getItem('kpress.theme'),
                      listeners: window.__kpressThemeAudit.listeners,
                      mutations: window.__kpressThemeAudit.mutations.length,
                    })"""
                )
                assert resolver_state == {
                    "mode": "dark",
                    "resolved": "dark",
                    "stored": "dark",
                    "listeners": 1,
                    "mutations": 2,
                }
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
