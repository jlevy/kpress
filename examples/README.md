# KPress Examples

Two runnable examples take a folder of Markdown documents from source to a built site
you can browse or upload, showing the two ways to consume KPress.
Each example’s `build.py` builds the site, can serve it locally so you can click through
it, and can package it as an uploadable `.zip`:

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

Both are real, tested builds; see `../tests/test_examples.py`.

## 1. `static-site/`: KPress as the Generator

The simple case. Point KPress at a `content/` tree and call one function:

```python
from kpress.publish import build_site

build_site("kpress.yml")          # writes ./public
```

```bash
cd static-site
python build.py --serve           # build and browse (or: kpress build kpress.yml)
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
   fully styled, self-contained `<article>` plus a manifest of the CSS and JS it needs,
   with no page chrome.
2. **Self-host the assets:** copy them out of the package with
   `kpress.get_static_asset(...)`. The manifest lists the *declared* top-level CSS and
   JS, but those files have dependencies the browser also fetches: CSS `url(...)`
   references (fonts and KaTeX) and JS `import` statements.
   The reader’s entry-point modules import transitive modules such as `overlay.js` and
   `viewport.js` that are deliberately not in the inject list, so the wrapper walks both
   reference graphs and copies the full closure.
   Copy only the declared list and the served site returns 404 on those imports.
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
- `kpress.get_static_asset` and `static_asset_url` obtain packaged assets.
- `kpress.publish.build_site` and `build_html` run full-site and single-file builds.

Everything else (the Markdown pipeline, theming internals, asset hashing) stays private.
Because the contract is this fragment-plus-assets seam, an outer tool can wrap KPress
without forking it.
One sharp edge to respect: the asset manifest names what to *inject*,
not the complete set of files to *serve*. A wrapper must serve the transitive closure
(the CSS `url()` and JS `import` graphs), which the example resolves with
`get_static_asset` in `build.py`.

## End to End, and What a Real Deploy Wrapper Would Add

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

## The library-call path (single-doc)

`single-doc/` is the exemplary *programmatic* integration: one Markdown document
published by constructing a typed `KPressConfig` in Python and calling
`build_site(config)`—no `kpress.yml`, no YAML strings, chrome slots as plain
strings, widget selection as a dict. A Python host calling a Python library
writes Python; the YAML file is the veneer for file-based setups, not the API.
(Production site builders follow this same pattern.)

## Extension-model tour (static-site)

`static-site/content/extensions.md` + `static-site/content/demo/extensions.js` are the
living tour of the extension model (kpress-design.md → *Extension and Injection Model*):
a **minimap widget** built from the page model, a **bare theme toggle** over the built-in
theme engine, a **TOC toggle tweak** (custom icon + always-visible policy via callback
config), a **footnote-handling override** over unchanged markup, and a **glossary
behavior** binding the page's own injected HTML.
Every one is site code injected through `head_extra_html`—zero KPress edits—and the
widget selection is plain config (`format.widgets`).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
