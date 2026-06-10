"""Build the wrapped-site example.

This is the "inner library" path. Instead of letting KPress own the whole page
(as the ``static-site/`` example does via ``build_site``), an *outer* builder
(standing in for your CMS or static-site framework) owns the page shell, the
navigation, and the routing. KPress is called per-document to render just the
body, and to tell us which CSS/JS/font assets that body needs.

The wrapper's job, in order:

1. Render each Markdown document to an HTML *fragment* with
   :func:`kpress.format.render_fragment`. The fragment is a fully-styled,
   self-contained ``<article>`` with no page chrome.
2. Collect the asset references the fragments declare, and copy that asset
   bundle out of the KPress package with :func:`kpress.get_static_asset`,
   following both CSS ``url(...)`` references (fonts, KaTeX) and JS ``import``
   statements so the transitive module graph (e.g. ``overlay.js`` ->
   ``viewport.js``) is served too, not just the injected top-level scripts.
3. Drop each fragment into the outer ``templates/layout.html`` shell, wiring up
   the asset ``<link>`` / ``<script>`` tags the same way KPress itself would.
4. Write each page to the URL the outer site map assigns it.

End to end means source -> built site -> navigable / uploadable::

    python build.py            # build ./public
    python build.py --serve    # build, then serve it so you can browse it
    python build.py --zip      # build, then package an uploadable .zip
    python build.py /tmp/out   # build into /tmp/out
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from html import escape
from pathlib import Path, PurePosixPath

from kpress import get_static_asset
from kpress.format import DocumentInput, RenderOptions, render_fragment

HERE = Path(__file__).resolve().parent
# Make the example's own modules (sitemap) and the shared runner importable
# whether run as a script or imported by a test. "sitemap" is named to avoid
# shadowing the stdlib "site" module.
for _path in (HERE, HERE.parent):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from _runner import package_zip, serve  # noqa: E402  (path set up above)
from sitemap import PAGES, Page  # noqa: E402  (path set up above)

CONTENT = HERE / "content"
TEMPLATE = HERE / "templates" / "layout.html"

# Where the copied KPress asset bundle is mounted in the output site. The pages
# are served from the site root, so these are root-absolute URLs.
ASSET_PREFIX = "/assets/kpress"

_CSS_URL_RE = re.compile(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""")
# Static/dynamic ESM specifiers: `... from "./x.js"`, `import "./x.js"`,
# `import("./x.js")`. The reader modules import transitive deps (overlay.js,
# viewport.js) that are NOT in the injected top-level list, so the wrapper must
# walk this graph too or the browser 404s on the imports.
_JS_IMPORT_RE = re.compile(r"""(?:\bfrom\b|\bimport\b)\s*\(?\s*['"]([^'"]+)['"]""")


@dataclass
class RenderedFragment:
    page: Page
    html: str
    css: list[str]
    js: list[str]


def _render_all() -> list[RenderedFragment]:
    """Render every page's Markdown to a KPress fragment + its asset refs."""

    rendered: list[RenderedFragment] = []
    for page in PAGES:
        source = CONTENT / page.source
        markdown = source.read_text(encoding="utf-8")
        document = DocumentInput(
            title=page.nav_title,
            body_markdown=markdown,
            source_text=markdown,
            source_path=str(source),
            logical_path=page.url,
            # These documents are authored by the site owner, so the
            # public-static (full-trust) profile is appropriate. A wrapper
            # rendering untrusted user content would use "sanitized-local".
            trust_mode="public-static",
        )
        fragment = render_fragment(document, RenderOptions(asset_mode="linked"))
        rendered.append(
            RenderedFragment(
                page=page,
                html=fragment.html,
                css=list(fragment.assets.get("css", [])),
                js=list(fragment.assets.get("js", [])),
            )
        )
    return rendered


def _copy_asset(ref: str, output_root: Path, copied: set[str]) -> None:
    """Copy one packaged KPress asset, following the files it references.

    ``ref`` is a package-relative path such as ``css/style-tokens.css`` or
    ``js/toc.js``. Copying preserves that layout under
    ``<output>/assets/kpress/`` so relative references keep resolving, and
    recurses into them: CSS ``url("../fonts/x.woff2")`` and JS
    ``import "./viewport.js"`` both point at files the browser will fetch, so a
    wrapper that serves the declared assets must serve their dependencies too.
    """

    ref = ref.lstrip("/")
    if ref in copied:
        return
    copied.add(ref)

    asset = get_static_asset(ref)
    dest = output_root.joinpath(*PurePosixPath(ref).parts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(asset.content)

    base = PurePosixPath(ref).parent
    for target in _referenced_paths(ref, asset.content):
        # Resolve "./" and "../" segments against the package asset root.
        normalized = _normalize_relative(base, target)
        if normalized is not None:
            _copy_asset(normalized, output_root, copied)


def _referenced_paths(ref: str, content: bytes) -> list[str]:
    """Same-bundle relative paths a CSS/JS file references (to copy alongside it).

    Returns CSS ``url(...)`` targets and JS ``import`` specifiers, skipping
    absolute, remote, and ``data:`` URLs. KaTeX's vendored bundle is classic
    (non-module) UMD whose deps come in via its own CSS ``url()`` refs, so its
    JS is not import-scanned.
    """

    text = content.decode("utf-8", errors="replace")
    if ref.endswith(".css"):
        raw_refs = _CSS_URL_RE.findall(text)
    elif ref.endswith(".js") and not ref.startswith("katex/"):
        raw_refs = _JS_IMPORT_RE.findall(text)
    else:
        return []

    out: list[str] = []
    for raw in raw_refs:
        target = raw.strip()
        if not target or target.startswith(("data:", "http://", "https://", "/", "#")):
            continue
        out.append(target)
    return out


def _normalize_relative(base: PurePosixPath, target: str) -> str | None:
    """Resolve ``target`` (a url() ref) relative to ``base`` into a clean ref."""

    parts: list[str] = list(base.parts)
    for segment in PurePosixPath(target).parts:
        if segment == "..":
            if parts:
                parts.pop()
            else:
                return None  # escapes the asset root; ignore
        elif segment == ".":
            continue
        else:
            parts.append(segment)
    return "/".join(parts) if parts else None


def _link_tags(css: list[str], js: list[str]) -> tuple[str, str]:
    """Build <link>/<script> tags the way KPress itself does."""

    style_tags = "\n  ".join(
        f'<link rel="stylesheet" href="{escape(ASSET_PREFIX + "/" + path)}">' for path in css
    )
    script_tags = "\n  ".join(_script_tag(path) for path in js)
    return style_tags, script_tags


def _script_tag(path: str) -> str:
    src = escape(ASSET_PREFIX + "/" + path)
    # Vendored KaTeX is classic UMD; KPress reader modules are native ESM.
    if path.startswith("katex/"):
        return f'<script defer src="{src}"></script>'
    return f'<script type="module" src="{src}"></script>'


def _nav_html(current: Page) -> str:
    items: list[str] = []
    for page in PAGES:
        current_attr = ' aria-current="page"' if page.url == current.url else ""
        items.append(f'<a href="{escape(page.url)}"{current_attr}>{escape(page.nav_title)}</a>')
    return "\n        ".join(items)


def _output_file(output_root: Path, url: str) -> Path:
    """Map a clean URL to its output file (``/`` and ``/docs/x/`` -> index.html)."""

    clean = url.strip("/")
    return output_root / "index.html" if not clean else output_root / clean / "index.html"


def build(output_dir: Path | None = None) -> dict[str, str]:
    """Build the wrapped site. Returns a map of URL -> output file (relative)."""

    output_root = (output_dir or (HERE / "public")).resolve()
    template = TEMPLATE.read_text(encoding="utf-8")
    fragments = _render_all()

    # Copy the union of every page's asset bundle once, into /assets/kpress.
    asset_root = output_root / "assets" / "kpress"
    copied: set[str] = set()
    for fragment in fragments:
        for ref in (*fragment.css, *fragment.js):
            _copy_asset(ref, asset_root, copied)

    routes: dict[str, str] = {}
    for fragment in fragments:
        styles, scripts = _link_tags(fragment.css, fragment.js)
        page_html = (
            template.replace("{{title}}", escape(fragment.page.nav_title))
            .replace("{{nav}}", _nav_html(fragment.page))
            .replace("{{kpress_styles}}", styles)
            .replace("{{kpress_scripts}}", scripts)
            # Content goes last: the fragment HTML is trusted KPress output and
            # must not be treated as a replacement template itself.
            .replace("{{kpress_content}}", fragment.html)
        )
        out_path = _output_file(output_root, fragment.page.url)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(page_html, encoding="utf-8")
        routes[fragment.page.url] = str(out_path.relative_to(output_root))
    return routes


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build the KPress wrapped-site example.")
    parser.add_argument("output_dir", nargs="?", help="Where to write the site (default ./public)")
    parser.add_argument("--serve", action="store_true", help="Serve the built site for browsing")
    parser.add_argument(
        "--zip", action="store_true", help="Package the built site as an uploadable .zip"
    )
    parser.add_argument("--port", type=int, default=8000, help="Port for --serve (default 8000)")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    routes = build(output_dir)
    destination = output_dir or (HERE / "public")
    print(f"Wrapped {len(routes)} KPress documents into {destination}")
    for url, output_path in sorted(routes.items()):
        print(f"  {url:<24} -> {output_path}")

    if args.zip:
        archive = package_zip(destination)
        print(f"\nPackaged uploadable archive: {archive}")
    if args.serve:
        serve(destination, port=args.port)
    elif not args.zip:
        print("\nServe it from the site root:  python build.py --serve")
        print(
            "Upload it with: python build.py --zip   (or copy", destination, "to any static host)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
