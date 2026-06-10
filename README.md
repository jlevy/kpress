# KPress

KPress renders Markdown into polished, readable HTML documents and publishes them as
static sites. It is a library and CLI, not a framework: it owns document rendering,
typography, and the static build pipeline, and stays out of site semantics so publishing
pipelines and embedding hosts can wrap it.

What you get out of the box:

- High-quality document typography: vendored PT Serif and Source Sans 3, a documented
  CSS token system, light/dark/system themes with a no-flash bootstrap, print CSS.
- Reader features as progressive enhancement: table of contents, footnote and link
  tooltips, code copy, tabs, video popovers, responsive tables, KaTeX math with a MathML
  no-JS fallback, diagram hooks.
  All JS is native ESM, source-first, zero-build.
- A full static build: route planning, sitemap/robots/redirects, content-hashed or fully
  offline (sealed) assets, an explicit optional minifier, gzip/Brotli precompression,
  and a deterministic build manifest.
- A dynamic host API proven by an embedding browser application
  (`kpress.runtime.render_view` / `get_static_asset`).
- Sanitization trust modes for raw HTML, including a strict public-static policy.

## Install

```bash
uv add kpress          # library
uvx kpress --help      # CLI
```

## Quickstart: a static site

```bash
mkdir mysite && cd mysite
uvx kpress init        # writes a starter kpress.yml
echo "# Hello" > index.md
uvx kpress build       # renders to public/
```

`kpress.yml` controls the site.
A fuller example:

```yaml
site:
  title: My Site
  base_url: https://example.com
  # Page chrome slots: opaque HTML owned by the site; kpress styles the
  # wrappers (.kpress-site-header / .kpress-site-footer) but never interprets
  # the content. Each slot also accepts a *_file variant read relative to
  # this config file.
  header_html_file: _includes/header.html
  footer_html: '<p>Published with <a href="https://github.com/jlevy/kpress">kpress</a></p>'
  head_extra_html: '<link rel="icon" href="/favicon.svg">'

sources:
  - path: content
    include: ["**/*.md"]
    # Verbatim-copy files (logos, favicons, images): copied to the output at
    # their source-relative paths, collision-checked against rendered pages.
    static: ["favicon.svg", "img/**/*.png"]

publish:
  output_dir: public
  asset_mode: hashed     # hosted | linked | hashed | sealed

optimizer:
  mode: none             # or "full" (requires Node; never a silent fallback)
```

`kpress clean` removes the output directory (only when it carries the kpress build
manifest) and the `.kpress/` work directory.

Asset modes: `hosted` points at a shared static server, `linked`/`hashed` emit an asset
directory beside the HTML (hashed names resolve through a standard import map; JS source
is never rewritten), and `sealed` produces a fully offline site.
A single-file `inline` export is not yet self-contained and is rejected with a clear
error; use `sealed` for offline artifacts.

## Quickstart: the Python API

```python
from pathlib import Path

from kpress.format import DocumentInput, RenderOptions, render_page

page = render_page(
    DocumentInput(
        title="Hello",
        source_text="# Hello\n\nSome prose.",
        body_markdown="# Hello\n\nSome prose.",
        source_path="hello.md",
    ),
    RenderOptions(asset_mode="linked"),
)
Path("hello.html").write_text(page.html)
```

`render_fragment(...)` returns the embeddable document fragment for hosts that own their
page shell; `kpress.publish.build_site("kpress.yml")` is the programmatic equivalent of
`kpress build`.

## Package boundary

- `kpress.format`: `render_fragment` / `render_page`, document model, sanitizer.
- `kpress.publish`: `build_site`, manifest, optimizer, precompression, capability probes
  (`kpress doctor`).
- `kpress.runtime`: dynamic-host rendering with caching and package asset serving.
  Importing it never pulls in publisher, optimizer, PDF, or Node-related modules.
- `kpress.workflow`: local `convert`, `format`, `paste`, `files`, `export` primitives.
- `kpress.contract`: the public names.
  Python API, CSS classes, CSS variables, template variables, data attributes, and
  manifest schema markers are all pinned there and enforced by tests; change them only
  with tests and goldens in the same patch, never via compatibility shims.

Embedding hosts should keep a thin adapter (runtime availability + error translation)
and consume only `kpress.runtime` / `kpress.models`.

## Development

```bash
uv sync --all-extras
uv run pytest tests --tb=short -q
uv run python devtools/lint.py --check
```

The lint gate runs Ruff, basedpyright, codespell, Biome 2, TypeScript `checkJs`, and
browserless DOM tests for the ESM helpers.
The pytest suite includes golden render and publish fixtures, a dynamic-vs-sealed
equivalence harness, contract tests, an optimized-build asset-resolution regression, and
a clean-room wheel gate that builds the wheel, installs it into a fresh venv, and builds
a site from the installed package.

Design and component docs live alongside the package: `kpress-design.md` (design system
and conscious departures), `kpress-icons.md` (icon sprite contract),
`kpress-reader-features.md`, and `docs/` runbooks.

## License

AGPL-3.0-or-later; see `LICENSE`. Third-party vendored components (Lucide icons, KaTeX,
PT Serif, Source Sans 3) are listed with their licenses in `NOTICE.md`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
