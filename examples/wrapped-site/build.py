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
2. Merge the complete per-render asset manifests and copy that package closure
   with :func:`kpress.format.materialize_package_assets`.
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
import sys
from dataclasses import dataclass
from html import escape
from pathlib import Path

from kpress.format import (
    AssetManifest,
    DocumentInput,
    RenderOptions,
    materialize_package_assets,
    render_fragment,
)

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


@dataclass
class RenderedFragment:
    page: Page
    html: str
    assets: AssetManifest


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
            # Sanitize even though these documents are authored by the site
            # owner: published pages should carry no raw scripts or handlers,
            # matching what kpress's own static publisher does.
            trust_mode="sanitized",
        )
        fragment = render_fragment(
            document,
            RenderOptions(
                asset_mode="linked",
                asset_url_prefix=ASSET_PREFIX + "/",
            ),
        )
        rendered.append(
            RenderedFragment(
                page=page,
                html=fragment.html,
                assets=fragment.assets,
            )
        )
    return rendered


def _link_tags(manifest: AssetManifest) -> tuple[str, str]:
    """Build <link>/<script> tags the way KPress itself does."""

    style_tags = "\n  ".join(
        f'<link rel="stylesheet" href="{escape(asset.url)}">'
        for asset in manifest.browser_entry_points()
        if asset.loading == "stylesheet"
    )
    script_tags = "\n  ".join(
        _script_tag(asset.url, loading=asset.loading)
        for asset in manifest.browser_entry_points()
        if asset.loading in {"module", "classic"}
    )
    return style_tags, script_tags


def _script_tag(url: str, *, loading: str) -> str:
    src = escape(url)
    if loading == "classic":
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
    site_assets = AssetManifest()
    for fragment in fragments:
        site_assets = site_assets.merged(fragment.assets)
    materialize_package_assets(site_assets, asset_root)

    routes: dict[str, str] = {}
    for fragment in fragments:
        styles, scripts = _link_tags(fragment.assets)
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
