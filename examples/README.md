# KPress Examples

Three runnable examples cover full static generation, host-wrapped fragments, and a
typed programmatic build.
The two site examples take a folder of Markdown documents to a built site you can browse
or upload. Each site example’s `build.py` builds the site, can serve it locally, and can
package it as an uploadable `.zip`:

```bash
python build.py            # build ./public
python build.py --serve    # build, then serve it (open the printed URL)
python build.py --zip      # build, then package an uploadable .zip
```

The built `public/` directory, or the `.zip`, is what you upload to any static host:
object storage, a Netlify drop, GitHub Pages, or a plain web server.

| Example | KPress’s Role | Who Owns the Page Shell? |
| --- | --- | --- |
| `static-site/` | Full static generator | **KPress:** the whole page, theme, and nav |
| `wrapped-site/` | Inner rendering library | **Your** outer template, CMS, or SSG |
| `single-doc/` | Typed Python library | **KPress:** one standalone document page |

All three are tested builds; see `../tests/test_examples.py`.

## 1. `static-site/`: KPress as the Generator

The simple case. Point KPress at a `content/` tree and call one function:

```python
from kpress.publish import build_site

build_site("kpress.yml")          # writes ./public
```

```bash
cd static-site
python build.py --serve           # build and browse (or: kpress build)
```

KPress discovers every `*.md`, derives clean URLs from the directory layout (with
optional `public_path:` frontmatter overrides), and emits a complete site: styled HTML,
fingerprinted CSS and JS, and web fonts.
Use this when KPress can own the whole page.

## 2. `wrapped-site/`: KPress as an Inner Library

Sometimes you already have a site shell: your navigation, your branding, your framework
(a CMS, an Astro, Eleventy, or Hugo-style builder, or a bespoke generator).
You want KPress to render only the *document body*. That is the wrapper pattern.

```bash
cd wrapped-site
python build.py --serve           # build and browse
```

The outer builder (`build.py`, standing in for your framework) does four things, all
through KPress’s **public API**:

1. **Render to a fragment:** call `kpress.format.render_fragment(...)`. The result is a
   document `<article>` plus a manifest of the CSS and JavaScript it needs, with no page
   chrome.
2. **Self-host the assets:** merge the complete typed manifests and pass the result to
   `kpress.format.materialize_package_assets(...)`. The manifest distinguishes browser
   entry points from dependency-only files and already includes stylesheet fonts,
   transitive modules, and conditional math assets, so the wrapper never parses CSS or
   JavaScript to discover the closure.
3. **Embed:** place each fragment in its own `templates/layout.html` shell and wire up
   the `<link>` and `<script>` tags the same way KPress itself would.
4. **Route:** map each page to a URL from its own site map (`sitemap.py`).

The result: every page carries both the outer site’s sidebar and top bar *and* a
KPress-rendered document inside it.
KPress never sees the surrounding chrome, and the wrapper never reaches inside the
rendered document.

### The Seam That Makes This Work

The wrapper depends only on KPress’s public surface:

- `kpress.format.render_fragment` and `render_page` render a document.
- `kpress.get_static_asset` obtains packaged assets.
- `kpress.publish.build_site` and `build_html` run full-site and single-page builds.

Everything else (the Markdown pipeline, theming internals, asset hashing) stays private.
Because the contract is this fragment-plus-assets seam, an outer tool can wrap KPress
without forking it. The asset manifest is fully resolved from `RenderOptions.asset_mode`
and `asset_url_prefix`. A wrapper emits HTML tags for ordered browser entry points and
materializes every manifest file at its declared output path.

## End-to-End Deployment Boundary

These examples go all the way to a navigable site you can browse (`--serve`) and an
uploadable artifact (`--zip`); see `_runner.py` for those two helpers.
The test suite (`../tests/test_examples.py`) serves each built site over HTTP and crawls
every internal link and asset to prove it is navigable.

What they leave to *you* is the hosting decision.
A production wrapper around this same seam would add content sourcing (pulling Markdown
from a repo or CMS), an incremental build cache, and the actual deploy step (upload to
object storage or a host, then invalidate the CDN). None of that changes how KPress is
called. It wraps the same `render_fragment` and `get_static_asset` core shown here; only
the final “copy `public/` somewhere” step becomes a real upload.

## The Library-Call Path (`single-doc/`)

`single-doc/` is the exemplary *programmatic* integration: one Markdown document
published by constructing a typed `KPressConfig` in Python and calling
`build_site(config)`—no `kpress.yml`, no YAML strings, chrome slots as plain strings,
widget selection as a dict.
A Python host calling a Python library writes Python; the YAML file is the veneer for
file-based setups, not the API. (Production site builders follow this same pattern.)

## Extension-Model Tour (`static-site/`)

`static-site/content/extensions.md` and `static-site/content/demo/extensions.js` are a
working tour of the
[Extension and Injection Model](../docs/kpress-design.md#extension-and-injection-model):
a **minimap widget** built from the page model, a **bare theme toggle** over the
built-in theme engine, a **TOC toggle tweak** (custom icon + always-visible policy via
callback config), a **footnote-handling override** over unchanged markup, and a
**glossary behavior** binding the page’s own injected HTML. Every one is site code
injected through `head_extra_html`—zero KPress edits—and the widget selection is plain
config (`format.widgets`).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
