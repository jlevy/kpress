---
title: KPress Design
description: Package contract for KPress document rendering, document components, static publishing, asset handling, optimization, PDF generation, and acceptance testing.
author: Codex under Levy
---
# KPress Design

**Status:** Draft design contract

**Last Updated:** 2026-05-18

## Purpose

KPress is a standalone document viewing and publishing layer.
It provides a reusable format runtime for embedding host applications and a static
publisher for creating publishable HTML/CSS/JavaScript/PDF artifacts from Markdown,
source files, and document inputs.

KPress owns document presentation.
Host applications own browser chrome, navigation, workspace state, tabs, file trees,
authentication, deployment, and service-specific publishing.

## Current Implementation Status

The current package slice is the first end-to-end implementation of the package
boundary. It proves dynamic rendering, static build, workflow, asset, quality-gate, PDF,
and golden-test paths, but it is not yet the full source-port of the TextPress/Kash
document client. The package-local implementation ledger is [`TODO.md`](TODO.md).

Implemented now:

- the standalone package layout and `pyproject.toml`
- importable `kpress`, `kpress.format`, and `kpress.runtime`
- public dynamic-host models in `src/kpress/models.py`
- runtime normalization, render caching, print profile normalization, static asset
  lookup, and export delegation in `src/kpress/runtime.py`
- format models, Markdown normalization, `nh3` sanitizer, render fragment/page, package
  template resources, theme/font hooks, asset helpers, and deterministic PDF artifact
  generation under `src/kpress/format/`, with an explicit missing-extra error for the
  not-yet-implemented browser backend
- package CSS and native ESM JavaScript assets for document layout, theme, TOC,
  tooltips, tables, code-copy, video popovers, tabs, and print controls
- `markdown-it-py` plus `mdit-py-plugins` based GFM normalization, stable duplicate
  heading IDs, footnotes/backrefs, fence-safe footnote/math parsing, trust-mode
  sanitizer coverage, Pygments code highlighting, math/diagram marker modes, and
  reader-parity structural tests
- package review cleanup for multi-source routes, trailing-slash output routes,
  single-read export behavior, `build_html()` manifest ownership, pre-paint theme
  bootstrap, stricter `basedpyright`, and exact optional dependency declarations
- browserless DOM tests for TOC disclosure/active links, footnote/internal-link
  tooltips, numeric table hooks, code-copy success/error/reset, video popovers, tab
  click/keyboard access, and theme initialization
- publisher config loading, source discovery, routes, output manifests, site files,
  cache helpers, static build, content-hashed package assets, `full`-optimizer
  HTML/CSS/JS minification, and optimizer primitives under `src/kpress/publish/`
- package CSS/JS asset modes (`hosted`/`linked`/`hashed`/`inline`) wired into both the
  dynamic runtime and `build_site()`; KaTeX bundle copied unhashed when math is present
- local workflow APIs and CLI commands for `init`, `convert`, `format`, `render`,
  `paste`, `files`, `export`, `build`, and `optimize`
- package-owned Biome and `tsc --checkJs` wrappers
- package-owned golden helper, accepted render fixtures, accepted static-site output
  tree, runtime, render, asset contract, cache, sealing, optimizer, static build,
  workflow, CLI, PDF, and golden tests
- TextPress/Kash Tailwind utility inventory with semantic KPress selector mappings and
  tests proving KPress output/assets do not reference the Tailwind runtime or active
  utility classes

Not implemented yet:

- remaining Markdown/GFM edge parity, image/figure/local media support, and full
  syntax-highlighting/source-profile visual acceptance
- broad accepted KPress document component fixture corpus
- Playwright-assisted manual browser acceptance playbook
- full source-port of TextPress/Kash document CSS and JavaScript behavior
- TextPress/Kash semantic content component parity
- sealed font asset parity and manual browser font confirmation
- manual browser visual proof for the Tailwind migration against accepted reference
  fixtures
- manual visual acceptance of `full`-optimizer output parity with `none`
- asset sealing — document-local asset copying, external URL fetching and
  integrity-pinning, HTML/CSS/JS URL rewriting, and offline tree verification — is
  deferred to v2 (see “Asset Model” below); v1 leaves document-local and external refs
  in the rendered HTML verbatim and lets the deploy layer own delivery
- browser-backed PDF generation

Parity closure rule: KPress reader/doc-format parity is not complete until every row in
the format feature ledger has accepted KPress fixtures, automated checks for stable
structure/package behavior, and explicit manual confirmation for
visual/mobile/dark/print/PDF quality where listed.

## Reader Feature Catalog and Parity Tracking

The durable catalog of document-reader features and their intended behavior is
`kpress-reader-features.md` (feature contract only: no status, beads, or source-port
detail).

Implementation status and the remaining reader-parity work are tracked in
[`TODO.md`](TODO.md) and
[`docs/kpress-completion-plan.md`](docs/kpress-completion-plan.md).
This design doc is architecture and public contract only and does not carry a status
ledger or reference-system comparisons.

## Product Boundaries

KPress has two public products.

**KPress format runtime:** Host-neutral document rendering.
It accepts normalized document inputs and returns fragments or full pages plus explicit
asset references. An embedding host uses this layer for document views and printable
source views.

**KPress publisher:** Static output generation.
It discovers source files, resolves routes, renders pages, copies and seals assets,
writes manifests, optionally optimizes HTML/CSS/JS, optionally precompresses assets, and
can generate browser-print PDFs.

KPress does not provide hosted publishing, accounts, login, comments, analytics, search
service, CMS behavior, or deployment automation.
A future `kpress-publish` adapter may provide service login, upload, and stable hosted
URLs.

## Dependency Rules

The package must keep dynamic viewing lightweight.

- `kpress.format` must be importable without importing `kpress.publish`
- `kpress.format` must also avoid importing PDF, optimizer, subprocess, browser, or
  Node-related code at import time
- `kpress.runtime` may expose dynamic-host helpers and package asset serving
- static publishing dependencies must stay under `kpress.publish` or optional extras
- Node-backed tooling is allowed for author checks and optional production optimization,
  but dynamic rendering must not invoke Node
- Tailwind is not part of KPress core.
  Active Tailwind-backed behavior from reference systems must be migrated into
  KPress-owned CSS
- heavy import/export features belong behind optional extras with deterministic
  missing-extra errors
- An embedding host must depend only on the thin runtime surface for dynamic views and
  static asset serving; it must not import publisher, optimizer, or browser-PDF modules
  while serving normal document views

Planned dependency tiers:

| Tier | Scope |
| --- | --- |
| `kpress` | Markdown/simple HTML rendering, package assets, dynamic fragments, static build basics, HTML export |
| `kpress[import]` | DOCX/PDF/URL/rich HTML import adapters |
| `kpress[clipboard]` | clipboard paste workflow |
| `kpress[pdf]` | browser-backed PDF generation |
| `kpress[office]` | DOCX export |
| `kpress[optimize]` | Brotli (`br`) precompression sidecars |
| `kpress-publish` | hosted login, upload, and public service URLs |

## Package Layout

Target layout:

```text
kpress/
  kpress-design.md
  pyproject.toml
  biome.json
  tsconfig.json
  devtools/
    biome.py
    tsc_check.py
    lint.py
  src/kpress/
    __init__.py
    py.typed
    cli.py
    errors.py
    models.py
    runtime.py
    format/
      __init__.py
      model.py
      render.py
      markdown.py
      sanitize.py
      validate.py
      theme.py
      assets.py
      pdf.py
      templates/
        fragment.html.jinja
        page.html.jinja
        components/
      static/
        css/
        js/
    publish/
      __init__.py
      config.py
      discover.py
      routes.py
      build.py
      cache.py
      seal.py
      optimize.py
      manifest.py
      site_files.py
    workflow/
      __init__.py
      convert.py
      format.py
      export.py
      paste.py
      workspace.py
    themes/
      default/
        kpress-theme.yml
  tests/
    fixtures/
    golden/
    browser/
```

The current implementation now uses the target `format/`, `publish/`, and `workflow/`
subpackage boundaries.
Later implementation beads should deepen those modules without breaking the public
import surface.

## Public API

Initial target API:

```python
from kpress.format import (
    DocumentInput,
    PdfOptions,
    RenderOptions,
    render_fragment,
    render_page,
    render_pdf,
)
from kpress.publish import BuildOptions, build_html, build_site
from kpress.workflow import convert_document, export_document, format_document

render_fragment(input: DocumentInput, options: RenderOptions) -> RenderedDocument
render_page(input: DocumentInput, options: RenderOptions) -> RenderedPage
render_pdf(page: RenderedPage | Path, options: PdfOptions) -> PdfReport
build_site(config_path: Path | str = "kpress.yml") -> BuildReport
build_html(src_html: str, dest_html: Path, options: BuildOptions) -> BuildReport
```

Current public API:

- `kpress.runtime.render_view(request: KPressRenderRequest) -> dict[str, Any]`
- `kpress.runtime.get_static_asset(rel_path: str) -> KPressAsset`
- `kpress.runtime.export_document(request: KPressExportRequest) -> Any`
- `kpress.format.render_fragment(document, options) -> RenderResult`

The current `export_document` path delegates to `kpress.publish.export_document`, which
renders HTML through the static page path and can emit the deterministic PDF artifact
used by the first test slice.

## Data Model Lifecycle

KPress should normalize inputs through these stages:

1. **Input:** Markdown, source text, trusted HTML, imported document Markdown, or static
   source tree entry.
2. **DocumentInput:** typed payload with source path, logical path, metadata, profile,
   trust mode, theme, TOC, math, diagram, and asset options.
3. **DocumentTree:** normalized document structure with stable IDs, headings, tables,
   footnotes, code blocks, images, diagrams, math, details, metadata, and diagnostics.
4. **RenderedDocument:** embeddable fragment plus required CSS/JS asset IDs, print
   profile, TOC metadata, diagnostics, and asset references.
5. **RenderedPage:** complete HTML page with metadata tags, theme bootstrap, document
   assets, social metadata, and static/publish metadata.
6. **BuildReport:** route graph, output files, asset manifest, optimization report,
   diagnostics, and cache information.

## Document Profiles

Document profiles describe the main printable surface:

| Profile | Purpose |
| --- | --- |
| `document` | rendered Markdown or rich document prose |
| `source` | source code, plaintext, logs, scripts, and config files |
| `table` | tabular documents and data previews |
| `tree` | directory or structured tree views where printable |
| `plain` | simple text fallback |

Profiles affect markup, CSS assets, print CSS, and behavior.
Host view names may map to profiles, but KPress should emit normalized profile names.

## HTML Contract

KPress emits semantic HTML and namespaced classes.
Host chrome must not appear in KPress fragments or pages.

The current public contract is encoded in `kpress.contract` and tested by
`tests/test_public_contract.py`. This is a new package, so keep the contract direct and
current rather than adding a compatibility shim layer.
Changing public names means changing `kpress.contract`, docs, tests, and accepted
goldens in the same patch.

Current public classes (from `contract.py::PUBLIC_CSS_CLASSES`):

```text
annotated-para
boxed-text
centered-headers
citation
claim
concepts
debug
description
frame-capture
full-text
hero
hidden
highlight
justify
key-claims
kpress
kpress-code
kpress-code-copy
kpress-code-scroll
kpress-content-with-toc
kpress-diagram
kpress-diagram-rendered
kpress-diagram-source
kpress-doc
kpress-doc-header
kpress-doc-layout
kpress-footnotes
kpress-frontmatter
kpress-frontmatter-error
kpress-header-actions
kpress-header-grow
kpress-header-row
kpress-long-list
kpress-long-text
kpress-math
kpress-math-display
kpress-math-inline
kpress-menu
kpress-menu-chooser
kpress-menu-seg
kpress-mermaid
kpress-metadata
kpress-no-print
kpress-page-main
kpress-page-spacer
kpress-print-only
kpress-print-surface
kpress-prose
kpress-settings
kpress-settings-btn
kpress-settings-menu
kpress-source
kpress-source-header
kpress-source-meta
kpress-source-truncation-warning
kpress-svg-diagram
kpress-tab-button
kpress-tab-list
kpress-tab-panel
kpress-tabs
kpress-table
kpress-table-wrap
kpress-task
kpress-toc
kpress-toc-backdrop
kpress-toc-title
kpress-toc-toggle
kpress-tooltip
kpress-video-backdrop
kpress-video-popover
para
para-caption
shaded-text
subtitle
summary
tab-button-active
tab-button-inactive
thumbnail
video-gallery
video-item
```

Current template variables are public where they are listed in
`kpress.contract.PUBLIC_TEMPLATE_VARIABLES`. They cover the packaged Jinja files under
`src/kpress/format/templates`. The tests assert that each declared variable exists in
the corresponding packaged template.

The contract module also declares:

- `PUBLIC_PACKAGE_API`: top-level importable names from `kpress`
- `PUBLIC_FORMAT_API`: names from `kpress.format`, including `AssetMode`, `MathMode`,
  `RenderOptions`, `FontSpec`, `TocMode`, `TrustMode`, and `DiagramMode`
- `PUBLIC_PUBLISH_API`: names from `kpress.publish`, including `BuildOptions`,
  `BuildReport`, `OptimizerOptions`, `PublishConfig`, `get_optimizer`, and
  `optimize_text`
- `BUILD_MANIFEST_REQUIRED_KEYS`: `schema_version`, `output_dir`, `files`, `assets`,
  `routes`, `diagnostics`
- `OptimizerMode = Literal["none", "full"]` (defined in `format.model`, used by publish)
- `full_optimizer_available()` in `publish.optimize`
- `PUBLIC_DATA_ATTRIBUTES`: the stable per-cell table `data-*` hooks kpress emits for
  downstream enrichment — `data-col` (the column slug derived from the header row) and
  `data-kpress-numeric`. This is the renderer-agnostic seam a downstream decorator (a
  host app’s table plugin, a future static-site builder) consumes to select a column by
  name or detect numeric columns.
  kpress emits them and never consumes them; it never imports a decorator and never
  knows any table plugin exists.

There is no `BuildMode` type.
The former `publish.mode` / `BuildReport.mode` / manifest `"mode"` key have been
removed; the independent axes (`asset_mode`, `strict`, `optimizer`, `precompress`)
replaced them.

## Design System

KPress is the lower, reusable design layer and the **single source of truth for its own
design system**. The guiding rule: design rules live **close to the code, in CSS
wherever possible** — each token and surface rule is documented as a comment next to its
declaration — so KPress’s design can be maintained on its own, cleanly, without chasing
a separate spec. This doc is the *map and rationale*; it does not duplicate the detailed
per-surface rules that live in the CSS.

Two sources of truth:

- **Tokens — `format/static/css/style-tokens.css`.** The `--kpress-*` token tree:
  typography (families/sizes/weights/caps), color and a shared `--kpress-doc-surface-bg`
  family, the corner-radius scale (`--kpress-radius-*`), spacing/measure, motion
  (`--kpress-ease` + `--kpress-transition-*`), and scrollbar colors.
  Each group carries its design rule inline as a CSS comment (e.g. “rounded-vs-square is
  a deliberate per-surface choice”; “one easing; fast for hovers, slow fade for
  overlays”). The public subset is pinned by `contract.py::PUBLIC_CSS_VARIABLES`. Core
  doc tokens read `var(--kpress-host-*, <default>)` so an embedding host app can theme
  them; the rest are overridable by static-site generators and standalone pages.
- **Icons — `format/static/icons/icons.svg`** (+ the contract doc `kpress-icons.md`).
  The one place KPress SVGs live: a real SVG sprite — the Lucide v1.17.0 (ISC) set as
  `<symbol>` elements on the stroke grid (`currentColor`, size-from-CSS), the single
  source of truth for chrome glyphs.
  The server inlines the hidden sprite once per document and both the server chrome
  (`render.py::_icon`) and the client JS (`static/js/icons.js::icon`) draw a glyph with
  `<svg><use href="#kpress-icon-<name>"></svg>` — no SVG geometry is authored in Python
  or JS. The contract is enforced by `tests/test_icons.py`.

**Relationship to the host app.** An embedding host app keeps the design that is
genuinely app-chrome-specific (e.g. a tree pane, tabs, shell, and its own app token
tree) but **leans on KPress for the shared, document-level design** — the same Lucide
icon family and the `--kpress-*` / `data-kpress-*` contract — rather than
re-implementing it. KPress owns and maintains the shared design layer; the three
consumers (standalone page, static-site build, host-app embed) inherit it.
See `kpress-icons.md` for the KPress↔host glyph map.

## CSS Contract

It must not reference host-shell selectors such as `.tree-pane`, `.preview-pane`,
`.file-header`, or `.tab-bar`.

Current public variables (from `contract.py::PUBLIC_CSS_VARIABLES`):

```css
.kpress {
  --kpress-caps-heading-size-multiplier: ...;
  --kpress-caps-spacing: ...;
  --kpress-caps-transform: ...;
  --kpress-doc-accent: #0f766e;
  --kpress-doc-bg: white;
  --kpress-doc-border: #ddd;
  --kpress-doc-code-bg: #f6f8fb;
  --kpress-doc-link: #0645ad;
  --kpress-doc-muted: #666;
  --kpress-doc-text: black;
  --kpress-font-body: system-ui;
  --kpress-font-features-sans: normal;
  --kpress-font-footnote: var(--kpress-font-sans);
  --kpress-font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;
  --kpress-font-prose: ui-serif, Georgia, serif;
  --kpress-font-punctuation: LocalPunct;
  --kpress-font-sans: system-ui;
  --kpress-font-table: var(--kpress-font-sans);
  --kpress-font-size-mono: ...;
  --kpress-font-size-normal: ...;
  --kpress-font-size-small: ...;
  --kpress-font-weight-sans-bold: 650;
  --kpress-font-weight-sans-medium: 550;
  --kpress-measure: 76ch;
  --kpress-print-font-size: 11pt;
  --kpress-print-footer: ...;
  --kpress-print-page-margin: 0.7in;
}
```

Body-level overlays.
Tooltips and footnote previews are appended to `<body>` (outside the `.kpress` subtree)
so their `position: fixed` resolves against the non-scrolling `.kpress-frame` (the
standalone shell marks `<body>` itself as the frame) rather than scrolling away inside
the `.kpress-viewport` scroller.
The document tokens above are scoped to `.kpress`, so those overlay selectors
(`.kpress-tooltip`) must be listed alongside `.kpress` in the token-defining rules
(`style-tokens.css`, `theme-light.css`, `theme-dark.css`); otherwise they resolve no
background/color/font and render transparent with a fallback face.

CSS must cover light, dark, mobile, and print modes.
Print CSS should force a light paper palette, hide screen-only controls, preserve
footnote readability, avoid clipped tables and source lines, and make generated PDFs
readable without host chrome.

### Design tokens and shared primitives

Internal design tokens live once in `style-tokens.css` so shape and motion are tuned in
one place rather than per component.
Stylesheets reference these instead of hardcoding values (the lint floor and code review
enforce “always use CSS vars”).

- **Corner radius** — `--kpress-radius-none | -sm | -md | -lg | -pill`. One scale;
  rounded-vs-square is a deliberate per-surface choice.
  Code blocks and tables both use `--kpress-radius-none` so the two read as one family;
  the gear menu / popovers use `-sm`, footnote markers use `-pill`.
- **Motion** — `--kpress-ease` plus `--kpress-transition-fast | -med | -slow | -fade`.
  `-fast` is the default for hovers and size/shape changes; `-fade` is for overlay
  opacity/visibility. The `prefers-reduced-motion` block suppresses them.
- **Surface fill** — `--kpress-doc-surface-bg` is the single subtle fill shared by code
  blocks, table headers, and (where applicable) metadata/shaded surfaces.

Two shared interaction primitives are documented so every component reuses them rather
than re-styling:

- **Disclosure toggle** — every `<details>`/summary uses the Lucide `chevron-right`
  glyph (drawn via a CSS mask so it inherits the summary color), rotated 90° when
  `[open]` on the motion token, with a single-color summary.
  No native disclosure triangle.
  Expansion animates via `interpolate-size: allow-keywords` + a `::details-content`
  transition where supported (older browsers open instantly).
- **Icon-only affordances** — action controls (code copy, video close) render an icon
  only, with the label in `aria-label`/`title`, and the copy control is revealed on
  hover/focus of the code block.
  Glyphs come from the shared Lucide set (see `kpress-icons.md`).

These primitives and tokens live in the KPress static layer deliberately: an embedding
host app consumes the same design (sharing the Lucide icon set) rather than
re-implementing it.

### Tailwind Migration Matrix

KPress core does not ship Tailwind runtime, generated Tailwind CSS, or a Tailwind build
step. The active Tailwind-backed behavior observed in the KPress/TextPress reference
templates is inventoried in `tests/fixtures/textpress_kash/tailwind-migration.json` and
covered by `tests/test_tailwind_migration.py`.

| Reference utility | KPress-owned replacement | Behavior preserved |
| --- | --- | --- |
| `container`, `max-w-3xl`, `mx-auto` | `.kpress-long-text` | centered readable document width |
| `bg-white` | `.kpress-long-text` | paper background for the document content surface |
| `py-4`, `px-6`, `md:px-16` | `.kpress-long-text` | mobile and tablet document padding |
| `flex`, `items-center` | `.kpress-header-row`, `.kpress-header-actions` | centered horizontal header/action layout |
| `flex-grow`, `ml-2` | `.kpress-header-grow` | expanding header/nav region with small inline gap |
| `ml-auto` | `.kpress-header-actions` | action cluster pushed to the inline edge |
| `mt-6` | `.kpress-page-spacer` | top spacing before main page content |

## Theme and Fonts

Theme mode values:

- `system`
- `light`
- `dark`

Standalone pages include a pre-paint bootstrap that resolves `system` using
`prefers-color-scheme`. Dynamic fragments let hosts resolve and set attributes.

Settings menu. The standalone page shell renders a gear-icon settings popover
(`.kpress-settings`) in the top-right of the viewport: a button that opens a menu
(`.kpress-menu`) of segmented icon choosers (`.kpress-menu-seg`), today a single
`system | light | dark` theme chooser.
It is ported from the original host app’s settings control and re-tokenized onto the
document tokens, so standalone KPress and the embedded host share one design and the
same theme contract; more choosers (e.g. a font chooser) can be added as further
`.kpress-menu-chooser` groups.
The menu is server-rendered **inside** `.kpress-viewport` so it inherits the document
tokens (rather than living outside `.kpress` where tokens would not resolve); its
`position: fixed` pins to the enclosing non-scrolling `.kpress-frame` — the viewport
itself must never be a fixed containing block, or the gear (and all floating UI) would
scroll away with the content.
`theme.js` (`bindSettingsMenu`) wires open/close — gear click, outside-click and Escape
dismiss — and marks the active segment with `aria-checked`. Selection persists in
`localStorage` (`kpress.theme`) and the pre-paint bootstrap reads it back.
There is no text theme chooser; the icon menu is the only theme control.

The standalone scroller `.kpress-page-main` carries the document `background`/`color`
and the document tokens, so the whole window is themed.

**Single scroll context.** `.kpress-page-main` is a `100dvh`, `overflow-y: auto` pane —
the one element the document scrolls inside.
So the page is not *also* scrolled by the window (which would show a second, nested
scrollbar), the page shell emits a standalone-only reset —
`html, body { margin: 0; height: 100%; overflow: hidden }` — making `.kpress-page-main`
the sole scroller. Its source lives in `static/css/page-reset.css` (front-end code in a
front-end file); `render_page` reads and inlines it render-blocking, the same way the
theme bootstrap is read from `static/js/theme-bootstrap.js`. No CSS or JS is authored as
a Python string (pinned by `test_no_css_or_js_source_is_authored_in_render_py`). This
reset is emitted only by the page shell, never by the embeddable fragment, so a host’s
own `html`/`body` stay untouched (Conscious Departures #14/#15: the fragment imposes no
global styles on a host).

It is standalone-only: an embedding host renders the KPress *fragment* (the `.kpress`
article), not the page shell, so neither the settings menu nor `.kpress-page-main`
appears in the host.
The host owns its own pane background and drives the embedded document’s theme by
setting `data-kpress-theme` / `data-kpress-resolved-theme` (KPress’s own `theme.js` is
not loaded in the host — see [Host Integration](#host-integration)). The
`system | light | dark` attribute contract is the shared seam; the gear chrome itself is
per-layer.

Font mode (`RenderOptions.font_mode`, type `FontMode = Literal["custom", "system"]`):

- `custom` (default): themed custom font stacks (PT Serif, Source Sans 3, mono,
  punctuation fallback) via CSS variables.
- `system`: `.kpress[data-kpress-fonts="system"]` overrides font variables to system-ui
  stacks with no custom font loading.

Font roles. Each role is a CSS variable that resolves through a host hook to a vendored
default — `var(--kpress-host-font-<role>, <vendored stack>)` — so an embedding host can
override any single role on its own, and otherwise the vendored reader faces apply:

| Variable | Default (vendored) | Used by | Host hook |
| --- | --- | --- | --- |
| `--kpress-font-prose` | serif — PT Serif (`LocalPunct` punctuation) | reading body (`.kpress-prose`), H1/H2 | `--kpress-host-font-prose` |
| `--kpress-font-sans` | sans — Source Sans 3 | UI chrome: TOC, captions, H3–H6, code-copy, **tooltips** | `--kpress-host-font-sans` |
| `--kpress-font-footnote` | sans (via `--kpress-font-sans`) | footnote previews and the bottom footnotes section | `--kpress-host-font-footnote` |
| `--kpress-font-table` | sans (via `--kpress-font-sans`) | data tables | `--kpress-host-font-table` |
| `--kpress-font-body` | sans — Source Sans 3 | `.kpress` wrapper base (a fallback; `.kpress-prose` overrides it for content) | `--kpress-host-font-body` |
| `--kpress-font-mono` | mono — system mono stack | code blocks | `--kpress-host-font-mono` |

The reading body is therefore serif by default and is settable serif↔sans per role: a
host flips it by setting `--kpress-host-font-prose` (a host app’s serif/sans
reading-font toggle does exactly this), and `font_mode="system"` swaps every vendored
face for the platform stack.
Footnotes and tables each carry their own stack (`--kpress-font-footnote`,
`--kpress-font-table`) so they can be retargeted independently; both default to the UI
**sans**, matching kash/textpress footnote and table typography.
The bottom footnotes section uses the same `--kpress-font-footnote` as the footnote
preview tooltips, so the two always agree.

Static sealing must be able to copy or download font assets so output does not rely on a
CDN unless configured.

## Document Components

Required document components:

- prose typography and headings
- frontmatter and metadata blocks
- TOC with desktop sticky rail, mobile affordance, active-heading state, and threshold
- footnotes with backrefs, hover/touch previews, and print simplification
- internal-link tooltips
- responsive tables, numeric-cell hooks, desktop breakout, mobile scroll, and print
  flattening
- code blocks with copy controls on screen and wrapped print output
- source profile with large-file/truncation messaging when needed
- images and local asset rewriting
- math support should expose only the modes users need: `off` and lazy `auto`. `auto`
  scans the document; documents without math do not parse math, load math JavaScript,
  fetch CDN assets, or include math dependencies in static output.
  Documents with math use KaTeX as the only active renderer, rendered **client-side**.
  The server emits, per expression, a hidden TeX source node and a semantic MathML node;
  a vendored, sealed KaTeX bundle (pinned `katex.min.js` + `auto-render` + a small init
  shim, loaded as deferred classic scripts) replaces the TeX node in place on
  `DOMContentLoaded`, after the rest of the document has painted.
  This is deliberate progressive enhancement: prose is never blocked on math, and math
  is filled in once document layout is stable.
  Build-time prerendering is explicitly **not** adopted: it would require a Node/JS or
  python-katex toolchain at publish time, which conflicts with KPress’s toolchain-free,
  self-contained sealing story.
  The cost is accepted: ~290K of KaTeX CSS+JS for documents that contain math (zero for
  documents that do not).
  The KaTeX font faces are not subsetted or bundled eagerly.
  KaTeX lays out using its precomputed metrics (baked into `katex.min.js`), so layout
  does not wait on fonts; the woff2 faces are declared via `@font-face` and fetched **on
  demand by the browser**, per face, only when a glyph that needs them is painted.
  A trivial `$x^2$` pulls only the Main/Math faces;
  Fraktur/Script/Caligraphic/SansSerif/Typewriter are never fetched unless used.
  All twenty faces are vendored (sealed bundle size, not client transfer); codepoint
  subsetting is intentionally avoided because needed glyphs are content- and not
  vendor-time-determined, and the per-face native lazy load already bounds client bytes.
  KaTeX’s `@font-face` rules carry `font-display: swap` so the late face arrival is a
  clean glyph repaint, not a reflow or an invisible-text gap.
  Native MathML remains valuable as the semantic/accessibility output generated by the
  renderer and as the no-JS fallback (it stays visible until KaTeX swaps, then is moved
  to the accessibility tree), but it should not grow into a parallel public provider
  matrix. MathJax is deferred unless concrete content shows KaTeX cannot cover the needed
  TeX.
- `inline` asset mode does not inline the KaTeX bundle: KaTeX’s stylesheet references
  font faces by relative `fonts/` URL, so the `katex/` subtree is always emitted with
  stable, unhashed names and linked externally even in inline mode.
  An inline-mode build of a math document is therefore not a single self-contained file
  with respect to KaTeX; this is a documented limitation, not a defect.
- diagram provider hooks for image/SVG passthrough and optional Mermaid
- details/summary styling
- video popovers where documents use them
- tabbed document content where documents use it
- highlight/citation/claim/summary/annotation styles when still useful from the
  reference renderer

Every component needs an accepted fixture, structural assertions, browser-state checks
when interactive, and visual acceptance before the component phase closes.
The end-to-end validation flow is maintained in `docs/kpress-validation.runbook.md`.

### Component Authoring Contract

These conventions are binding for every interactive document component.
They keep the reader hand-rolled, zero-build, and sealable, which is the reviewed and
accepted architecture (no component kit, no platform-only widgets, no positioning
library yet).

1. **No JavaScript runtime dependency.** Components are native ESM modules under
   `src/kpress/format/static/js/`. No bundler, no framework, no CDN import.
   They must run from sealed static output with no network access and must progressively
   enhance server-rendered HTML (the document is readable with JavaScript disabled).
2. **Init function shape.** Each component exports a single
   `initKpress<Name>(root = document)` entry point.
   It is idempotent: re-running it on the same root must not double-bind handlers or
   duplicate injected controls (guard with a `data-kpress-*-ready` marker or an
   existing-node check).
   A component never runs work at import time.
3. **DOM and class conventions.** Behavior is wired through `data-kpress-*` attributes.
   Every component-owned class is namespaced `kpress-*`. Bare or legacy un-namespaced
   classes (for example `visible`, `open`, `toc-open`) are not allowed; shared state
   classes are `kpress-visible`, `kpress-overlay-open`, `kpress-mobile-visible`, and
   `kpress-toc-open`. New public classes are added to `contract.py::PUBLIC_CSS_CLASSES`
   and styled in `static/css/` in the same change.
4. **Shared overlay primitive.** Any component that positions a floating surface
   (tooltips, video popover, TOC drawer, future popovers) must use
   `static/js/overlay.js`: `computePosition` for viewport-aware placement,
   `dismissOnEscape` / `dismissOnResize` / `dismissOnOutsideClick` for teardown, and
   `toggleBackdrop` for backdrop plus `aria-hidden` state.
   Per-component positioning or dismiss logic must not be reintroduced.
   `overlay.js` records the explicit Floating-UI reconsider tripwire: adopt Floating UI
   only if the overlay system needs multi-axis collision detection with simultaneous
   flip and shift, or virtual-element anchoring for non-DOM triggers; until then a JS
   runtime dependency is not justified.
5. **Accessibility baseline.** Interactive components set correct ARIA roles, manage
   focus (trap and restore for modal surfaces), support keyboard operation and Escape
   close, and respect `prefers-reduced-motion`.
6. **Testing contract.** Each component ships a browserless happy-dom DOM test under
   `tests/js/`, is represented in an accepted golden, and passes the package gate (Biome
   2 including `style/useBlockStatements`, `tsc --checkJs`, Vitest).
   Real-browser visual and interaction acceptance is recorded through
   `docs/kpress-validation.runbook.md`, not asserted in CI.

## Reference Source Areas

KPress reader parity is adapted from prior Kash/TextPress reader surfaces.
This public package contract records the behavior categories without machine-local
source paths; internal migration evidence belongs in monorepo evidence docs.

| Reference area | Behavior carried forward |
| --- | --- |
| Prior page shell templates | page shell, theme setup, font baseline, social metadata, Tailwind CDN inventory |
| Prior base reader styles | reader typography tokens, PT Serif/Source Sans usage, responsive sizing |
| Prior content styles | prose, semantic blocks, tables, code, media, annotations |
| Prior standalone document templates | standalone document layout |
| Prior TOC styles and scripts | desktop/mobile TOC layout, disclosure, and active-link behavior |
| Prior tooltip styles and scripts | tooltip visual treatment and footnote/internal-link interactions |
| Prior video popover styles and scripts | YouTube link interception and iframe popover behavior |
| Prior tabbed-page template | tabbed page behavior and utility-class inventory |
| Prior webpage renderer | render assembly and API shape |
| Prior TextPress workflows | local format workflow expectations, document rendering entry point, and page UX |

## Reference-to-KPress Component Matrix

The source systems are implementation references, not long-term compatibility targets.
Each row below must end with accepted KPress fixtures and tests before the component
phase closes.

| Capability | Reference behavior | KPress-owned surface | Required fixtures and tests | Bead |
| --- | --- | --- | --- | --- |
| Markdown/GFM document tree | TextPress/Kash Markdown-to-HTML path and item frontmatter/sidematter handling | `markdown.py`, `model.py`, `sanitize.py`, document component templates | GFM/nested-list/raw-HTML/image/code/math/diagram golden fixtures, duplicate-ID and anchor assertions | `orig-8is3` |
| Standalone page shell and metadata | Kash base page and TextPress page template | `page.html.jinja`, metadata/social model fields, static page render path | standalone page golden, social metadata assertions, landmark checks | `orig-selz`, `orig-0xa1` |
| Prose typography and headings | Kash base/content CSS and TextPress page template | `document.css`, `style-tokens.css`, `fragment.html.jinja`, `page.html.jinja` | prose page golden, heading-ID structural assertions, desktop/mobile/print manual style review | `orig-131h`, `orig-pyhv` |
| Light, dark, and system theme | TextPress/Kash theme setup and toggle behavior | `theme-light.css`, `theme-dark.css`, `theme.js`, theme data attributes | theme DOM state, pre-paint bootstrap smoke, light/dark manual screenshot review | `orig-131h`, `orig-q72a` |
| Print-ready document surface | TextPress/Kash print CSS | `print.css`, `.kpress-print-surface`, print profile metadata | print-media HTML/CSS probes, browser PDF artifact checks, no host chrome assertions | `orig-131h`, `orig-n7ok`, `orig-q72a` |
| Mobile document layout | Kash responsive layout and TOC affordances | responsive document CSS, TOC mobile controls | narrow viewport manual screenshot review, max-width/margin observations, mobile TOC state | `orig-131h`, `orig-d6g2`, `orig-q72a` |
| TOC | Kash TOC scripts/styles | `toc.html.jinja`, `toc.js`, `components.css` | TOC threshold tests, generated IDs, active-heading browser state, print suppression | `orig-d6g2` |
| Footnotes | Marko/Kash footnote output and tooltip behavior | footnote postprocessing, `footnotes.html.jinja`, `tooltips.js` | footnote/backref structural golden, hover/touch preview browser state, print simplification | `orig-xmov`, `orig-d6g2` |
| Internal-link tooltips | Kash tooltip scripts/styles | `tooltips.js`, `.kpress-tooltip`, preview markup | heading/figure/table/code/details preview fixtures, Escape close and expansion states | `orig-d6g2` |
| Tables | Kash table wrapping and content CSS | `table.html.jinja`, `tables.js`, table CSS | wide table/mobile scroll/print flattening fixtures, numeric-cell hooks | `orig-xmov`, `orig-d6g2` |
| Code blocks and source views | Kash code-copy and source rendering behavior | `source.html.jinja`, `code-block.html.jinja`, `code-copy.js`, source profile CSS | source-file golden, copy-control browser state, long-line print wrapping | `orig-xmov`, `orig-d6g2` |
| Frontmatter and metadata | TextPress/Kash metadata components and sidematter copying | `frontmatter.html.jinja`, `metadata.html.jinja`, metadata model fields | frontmatter/sidematter precedence tests, print policy fixture | `orig-xmov`, `orig-ngq8` |
| Images and local assets | TextPress image URL rewriting and sidematter assets | asset model, URL rewriter, static seal/copy pipeline | local image fixture, rewritten URL assertions, sealed asset manifest | `orig-xmov`, `orig-lghl` |
| Math | net-new KPress behavior | `off`/lazy-`auto` math modes, KaTeX renderer, semantic MathML accessibility output | no-math fixture proving zero math assets, inline/block math fixtures, `off` mode, `auto` lazy detection, sealed static output, browser/PDF review | `orig-xmov`, `orig-q72a` |
| Diagrams | explicit KPress image/SVG/Mermaid hooks | diagram adapter, Mermaid optional asset path | SVG passthrough fixture, Mermaid fixture, offline/sealed mode checks | `orig-xmov`, `orig-lghl`, `orig-q72a` |
| Video popovers | Kash YouTube popover scripts/styles | `video-popover.js`, video component CSS/templates | open/close browser-state fixture, no unexpected network in sealed mode, raw iframe placeholder fixture | `orig-d6g2`, `orig-lghl` |
| Tabbed content | Kash tabbed page template | `tabs.js`, tab component templates/CSS | tab switching browser state and accessibility checks | `orig-d6g2`, `orig-0xa1` |
| Semantic content components | Kash content styles for citations, claims, summaries, concepts, annotations, frame captures, and video galleries | `document.css`, `components.css`, semantic content fixtures | selector coverage, manual style observations, desktop/mobile/print visual review | `orig-selz`, `orig-q72a` |
| Custom fonts | TextPress/Kash PT Serif, Source Sans 3, mono, punctuation fallback | theme/font model, `FontMode` (`custom`/`system`), CSS variables, `data-kpress-fonts` attribute, sealed font assets | font variable tests, `font_mode` switching, manual font-family review, sealed font manifest | `orig-131h`, `orig-lghl` |
| Sealed reader assets | Kash CDN font/assets and TextPress sidematter assets | `assets.py`, `seal.py`, `build.py`, package manifests | linked/hashed/inline output goldens, offline tree checks, font/image manifest assertions | `orig-5dmd`, `orig-lghl` |
| Tailwind-backed layout behavior | active utility classes in Kash/TextPress templates | semantic KPress classes and CSS replacements | Tailwind migration matrix, class coverage tests, accepted layout snapshots | `orig-8kp9`, `orig-131h` |
| Browser asset quality | planned native ESM JS/CSS package source | `biome.json`, `tsconfig.json`, `devtools/*`, JS assets | Biome CI, `tsc --checkJs`, browserless DOM tests, manual browser console/network review | `orig-bht8`, `orig-q72a` |
| Static publishing | earlier KPress static builder conventions | `publish/*`, `workflow/*`, `kpress.yml` | static output tree goldens, route/manifest/cache tests | `orig-ngq8`, `orig-lghl`, `orig-jm5n` |
| Local document workflows | TextPress convert/format/paste/files/export ergonomics | `workflow/*`, CLI commands, workspace/cache report model | CLI golden tests for outputs, reports, missing extras, `--rerun`, `--refetch` | `orig-2l9z` |

## Conscious Departures from kash/textpress

KPress mirrors the kash/textpress design system for TOC, tooltips, footnotes, and serif
typography (the visual-parity reconciliation spec
`plan-2026-06-01-kpress-visual-polish.md`, with the full divergence matrix in its
evidence file, lives in the originating monorepo’s spec archive).
Parity is pinned by
`tests/test_asset_contract.py::test_visual_parity_css_contract_pins_kash_reconciliation`
and the golden/DOM suites.
The following divergences are **intentional and approved** — do not “fix” them toward
kash; they are the recorded exceptions:

1. **Container queries, not media queries.** All responsive layout uses
   `@container kpress-doc` + `cqw` instead of `@media`/`vw`, so the document adapts to
   its embedding host’s pane width, not the browser window.
   (Standalone breakpoints are tuned to reproduce kash’s ~1200px viewport crossover at
   the equivalent container width, 75rem.)
2. **Server-rendered TOC.** TOC HTML is built in Python at render time, not client-side,
   so there is no layout shift.
3. **Ordered list for the TOC** (`<ol>` vs kash `<ul>`); visually identical
   (`list-style: none`).
4. **Single-tooltip architecture** — one tooltip created on demand and removed on hide,
   vs kash’s persistent pre-created map.
   More memory-efficient.
5. **`<aside role="tooltip">`** instead of a `<div>` (semantic upgrade).
6. **Focus/blur tooltip triggers** for keyboard accessibility (kash lacks this).
7. **Escape and resize dismiss** for tooltips.
8. **`<section class="kpress-footnotes">`** wrapper instead of
   `<div class="footnotes">`.
9. **Footnotes-section container styling** (border-top, muted, 0.9em) — kash has none.
10. **Dual active-state signal** on TOC links (`data-active` attribute + `.active`
    class) so embedding hosts get an attribute hook.
11. **Cool-blue palette**, not kash’s warm teal — `#0756a5`-based primary, fully-opaque
    tokens. This is the KPress brand palette; the kash `--color-*` token *names* are
    provided but mapped to blue values.
12. **Blue-based dark palette** (same hue choice in dark mode).
13. **Sans on the `.kpress` wrapper, serif only inside `.kpress-prose`** — UI chrome is
    sans, body prose is serif.
14. **No global scrollbar styling** (KPress is an embeddable fragment, not a page).
15. **No `html { overflow-x: hidden }}`** (KPress is a fragment, not a full page).
16. **Modernized font fallback chains** (`system-ui`/`Georgia` named fallbacks).
17. **No Hack Nerd Font** (a desktop icon font, inappropriate for the web).
18. **Responsive image constraints** (`height: auto; max-width: 100%`).
19. **TOC levels 5–6** styled (kash stops at 4) for deep heading hierarchies.
20. **Viewport `overflow: hidden` scroll lock** for the open drawer, instead of kash’s
    `body { position: fixed }` — correct for container-scoped scrolling.
21. **Proactive top-right tooltip flip** decided at selection time rather than a
    deferred bounds check.
22. **`print.css` dual-class selectors** (both `kpress-`-namespaced and legacy kash
    class names) for defensive compatibility.
23. **Tooltip sizing hardcoded** rather than exposed as CSS custom properties (simpler;
    hosts cannot override tooltip dimensions — accepted trade-off).
24. **`kpress-footnote-nav` / `kpress-footnote-nav-link` classes** instead of reusing
    kash’s `.footnote` class (avoids kash’s `display: none` override hack).

In addition, an embedding host app keeps KPress’s vendored PT Serif / Source Sans reader
faces by default, so an embed reads with the kash look rather than the host’s UI fonts.
A host overrides a font per role through the `--kpress-host-font-*` hooks (see the
font-role table under [Theme and Fonts](#theme-and-fonts)); a host app can use this for
a serif/sans reading-font toggle, which sets `--kpress-host-font-prose`. Color tokens
bridge the same way through the other `--kpress-host-*` variables.

## Tailwind Migration

KPress must preserve active Tailwind-backed behavior without depending on Tailwind.

Known source usage includes the `@tailwindcss/browser` CDN in the Kash base page and
utility classes such as `container`, `max-w-3xl`, `mx-auto`, `bg-white`, spacing
utilities, `hidden`, `flex`, and text sizing classes in simple, tabbed, and TextPress
page templates.

Migration rules:

- inventory all active utility classes before porting a template
- replace utilities with semantic KPress classes and CSS variables
- preserve spacing, max-width, display toggles, hidden tab panes, flex header layout,
  centered headings, responsive behavior, dark overrides, and print behavior
- do not expose Tailwind class names as public KPress API unless a legacy adapter needs
  them
- do not include Tailwind runtime, generated Tailwind CSS, or a Tailwind compile step in
  normal KPress output

A compatibility adapter may exist for legacy artifacts, but it must not be part of
KPress core.

## Markdown, Sanitization, and Source Rendering

Markdown target capability:

- GFM tables
- footnotes
- task lists
- generated heading IDs
- raw HTML in trusted local mode
- sanitizer or rejection diagnostics in public static mode
- postprocessing for footnote backrefs and component wrappers

Trust modes:

- `trusted-local`: local document viewing, useful raw HTML allowed
- `public-static`: sanitize or reject unsafe HTML, scripts, iframes, SVG, unsafe links,
  and unsealed remote URLs according to config

Source rendering target capability:

- language metadata
- optional syntax highlighting
- copy controls on screen
- print wrapping
- large-file fallback/truncation warning when relevant

## Static Publishing

Static publishing reads `kpress.yml`, discovers source files, merges metadata, resolves
routes, renders pages, copies assets, seals external dependencies, optionally optimizes,
and writes manifests.

Source conventions:

- Markdown files are renderable sources
- YAML frontmatter is part of the document
- sidematter files may provide additional metadata
- colocated `.assets/` directories are copied and URL-rewritten
- `public_path`, `public_slug`, page IDs, redirects, sitemap, and robots are supported

Frontmatter and sidematter are read through the `frontmatter-format` library
(`kpress.publish.frontmatter`), not a KPress-specific parser.
A source may carry in-document `---` YAML frontmatter and an optional sibling sidematter
file `<stem>.meta.yml` (or `.meta.yaml`). The merged metadata is the single input to
routing, rendering, and the manifest.
Precedence is fixed: **in-document frontmatter wins over sidematter**; sidematter
supplies defaults an author can override inline.
The body passed to the renderer always has the frontmatter fence removed.

Route overrides come from the merged metadata:

- `public_path`: an explicit, site-absolute route that replaces the path-derived route.
  Case-normalized like every route; a trailing `/` is a directory route
  (`…/index.html`).
- `public_slug`: replaces only the leaf segment of the path-derived route, keeping
  parent directories and the index/trailing-slash shape.
  Ignored when it contains a `/`.

`public_path` takes precedence over `public_slug`. Overridden routes keep the same
case-insensitive collision and reserved-path (`sitemap.xml`, `robots.txt`, `_redirects`,
`_kpress/`) guarantees as path-derived routes.

Static output shape:

```text
public/
  index.html
  _kpress/
    assets/
    kpress-manifest.json
  sitemap.xml
  robots.txt
  _redirects
```

## Static Build Output

KPress is a framework for building highly readable, production-ready documents that can
be statically built or dynamically served, depending on the application.
There is no `dev`/`production` build mode: that conflated deployment intent with asset
shaping. The build exposes independent, explicit axes, each with a readable default, so
the application chooses what it needs.

| Axis | Config / option | Default | Choices |
| --- | --- | --- | --- |
| Asset shaping | `publish.asset_mode` / `--asset-mode` | `linked` (readable) | `linked`, `hashed`, `inline`, `sealed`, `hosted` |
| Offline strictness | `publish.strict` / `--strict` | `false` | `true` rejects any unexpected remote reference |
| Optimizer | `optimizer.mode` / `--optimizer` | `none` | `none`, `full` |
| Precompression | `optimizer.precompress` / `--precompress` | none | `gzip`, `br` |

Every axis is independent.
Readable linked output, content-hashed sealed output, and inline single-file output are
all valid; a local embedded file browser and a public CDN deployment differ only in
which axes they set, not in a coarse mode.
Selecting `full` without the Node toolchain, `br` without `kpress[optimize]`, or
`strict` with an unexpected remote reference is a clear error, never a silent downgrade.

### Named output modes

The independent axes (`asset_mode`, `strict`, `optimizer`, `precompress`) cover both
dynamic per-request rendering and static publishing.
The following named modes are the canonical combinations consumers ask for; they are
conveniences over the underlying axes, not coarse build modes that hide them.

| Mode | Layer | `asset_mode` | `strict` | `optimizer` | `precompress` | Entry point | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Dynamic multifile dev** | Runtime | host-served package assets, unmodified | n/a | n/a | n/a | `runtime.render_view` + `/kpress-static/...` | Stable; current host-app default |
| **Dynamic multifile (production embed)** | Runtime | host-served, optionally hashed/optimized package variants | n/a | host-side, if any | host-side (CDN/edge) | `runtime.render_view` from an embedding host | Same code path as dev; no pre-optimized package variants ship today |
| **Static build dev** | `kpress build` | `linked` | n/a | `none` | none | `kpress build` | Stable; readable multi-file tree. Document-local and external asset URLs pass through verbatim — the deploy layer owns them. |
| **Static build prod** | `kpress build` | `hashed` | n/a | `full` | `gzip` (`br` with `kpress[optimize]`) | `kpress build` | Stable; content-hashed package assets, immutable cache, minified. Document-local and external asset URLs pass through verbatim. |
| **Static build sealed** | `kpress build` | `sealed` + `strict=true` | yes | `full` (typical) | optional | `kpress build` | **Deferred to v2.** See “Asset Model and Sealing: deferred for v1” below. |
| **Self-contained single file** | `kpress format` / `render` | `inline` + classic (non-module) reader JS + inline fonts + inline KaTeX | n/a | `full` (typical) | n/a | `kpress format`/`render` with `--asset-mode inline` (lever gap) | **Deferred.** See “Self-contained single file: deferred” below. |

For a “share one HTML file by link” workflow, prefer **Static build prod** deployed to a
CDN (or **Dynamic multifile (production embed)** with a CDN-hosted reader bundle) rather
than self-contained inline.
The artifact-size math (see deferred notes) makes inline a poor default for most
documents.

For air-gapped or offline-verified static publish, sealing is on the v2 roadmap — see
“Asset Model and Sealing: deferred for v1” below.
The deploy layer (CDN, S3, GitHub Pages, etc.)
is the right place to handle external-asset integrity, fetching, and hashing in v1.

Dynamic and static differ in *layer*, not in shaping intent.
Dynamic emits one HTML fragment + a JSON asset manifest per request; static emits a
directory tree the deploying host serves verbatim.

#### Open lever gaps

One small gap applies to the “Dynamic multifile (production embed)” mode: no
pre-optimized variant of the package assets ships in the wheel today, so an embedding
host that wants minified/hashed reader assets at runtime must apply its own
optimization/hashing on top of the served package files.
Tractable when a real production embed asks for it.

#### Self-contained single file: deferred

Truly self-contained single-file output (one HTML that opens over `file://` with no
sibling assets) is **deferred**. The artifact size dynamics, not the implementation
mechanics, are the reason:

- Reader fonts alone (PT Serif + Source Sans, 6 woff2) add ~250 KB after base64
  inflation.
- KaTeX as inline (when math is present) adds another ~700 KB (UMD JS + 20 woff2 fonts
  + CSS).
- Document images push artifact size into MB territory quickly (1 MB photo → ~1.3 MB
  after base64; email clients clip at ~100 KB; multi-MB HTML noticeably slows browser
  parse).

For “share a rendered doc by link”, point at a CDN-hosted asset bundle instead and
publish via **Static build prod**. The current package-asset URL builder already accepts
an arbitrary prefix (`format/assets.py::package_asset_url`), so a host or build step can
point at a CDN with no new code.

To revisit if a real `file://`-only consumer appears, the work is small and
self-contained:

- **Tier 1 (~1 day) — bundle reader JS to classic.** Reader modules are 11 files, ~1,930
  LOC, with a shallow single-root import graph (3 modules import from `overlay.js`;
  nothing else has imports).
  A topological concat + strip of `import`/`export` statements is ~30 lines of Python or
  one `npx esbuild` call (same pattern as `html-minifier-next`). Then plumb
  `--asset-mode` through `format`/`render` and switch inline JS emission from
  `<script type="module">` to classic `<script>`. This alone unblocks `file://` for
  documents with system-font fallback acceptable.
- **Tier 2 (~half day) — inline reader fonts.** Rewrite `url(../fonts/foo.woff2)` in
  `style-tokens.css` to `url(data:font/woff2;base64,...)` (~20 lines).
- **Tier 3 (~half day) — inline KaTeX when math is detected.** Same data-URI rewrite for
  the 20 KaTeX woff2 fonts plus literal-inline the KaTeX UMD JS (already classic).
- **Tier 4 (deferred-within-deferred) — document images.** The asset-sealing
  infrastructure in `publish/seal.py` already handles size caps, integrity, MIME
  validation, and HTML/CSS rewriting.
  Extending it to base64-inline local images is ~50 lines plus a
  `--max-inline-image-bytes` policy.
  External-image fetching would reuse the existing sealed-asset path.
  Skip video; emit poster + link.

Surface as one composable lever (`reader_js=module|classic`, kept independent of
`asset_mode`) plus a `--single-file` convenience flag that maps to
`asset_mode=inline, reader_js=classic, font_inline=true`. Don’t introduce a 6th opaque
`asset_mode` value — that breaks the no-coarse-modes stance.

Tracking: `orig-547y` (classic-JS reader output lever).

#### Dynamic multifile (production embed): host-owned optimization

Decision: KPress does **not** ship pre-optimized variants of package CSS/JS in the
wheel.
Embedding hosts that want minified/hashed reader assets at runtime are expected to
apply their own optimization on top of the served package files (e.g., a CDN edge that
minifies + hashes, or a Vite/esbuild/webpack passthrough that consumes the package
resources). Rationale:

- KPress’s optimizer story is built around `kpress build`’s `full` mode and a locked
  `html-minifier-next` cache.
  Duplicating that into a build step that bakes minified variants into the wheel doubles
  the install surface (more files, larger wheel, duplicate provenance in two places) and
  re-introduces a `dev`/`production` axis at the package level, which the
  no-coarse-modes stance rejects.
- The `package_asset_url(path, prefix=...)` builder already accepts any URL prefix, so a
  host that pre-optimizes can serve from `/static/kpress/<v>/...` (or any CDN) without
  any KPress code change.
- No real embedding consumer is asking for baked variants today.
  Revisit if/when one does; the work would be ~1-2 days of build + manifest changes if
  accepted.

In the meantime, embedding hosts should treat the served `/kpress-static/<v>/...` tree
as a stable source they can optimize at their own deployment layer.

## Asset Model

KPress sees four kinds of assets:

- **Package assets** — CSS/JS/fonts vendored inside the wheel (`format/static/`). Copied
  into the publish output tree (or served dynamically) by KPress itself.
- **Document-local assets** — files the document references via relative paths
  (`./image.png`, `./styles.css`). In v1, KPress does **not** copy or rewrite these —
  the URL is left in the rendered HTML verbatim and the deploy layer is responsible for
  placing the file alongside the HTML (or rejecting the build).
- **External URL assets** — anything the document references with `http(s)://` or
  `//host/...`. In v1, these pass through verbatim; the rendered HTML still references
  the original CDN URL.
- **Generated assets** — KPress-generated content (KaTeX bundle when math is present,
  etc.). Treated like package assets.

Package asset modes (`asset_mode` in `publish` config):

- `hosted` — the embedding host serves package assets at a configured URL prefix
  (default `/kpress-static/`). Used by the dynamic host-app path; emits no copies.
- `linked` — package assets copied to `_kpress/assets/...` with stable (unhashed) paths.
  Readable, dev-friendly.
- `hashed` — package assets copied with `<name>.<sha>.<ext>` names so the CDN can mark
  them `cache-control: immutable`.
- `inline` — package CSS/JS embedded in the rendered page.
  Fonts stay on disk; KaTeX (when present) stays linked because its stylesheet uses
  relative font URLs.

The `sealed` mode (external assets fetched + integrity-pinned + offline- verified) is
**deferred to v2** — see the section below.

### Static asset caching

Every package asset response carries a strong `ETag` (the SHA-256 of the bytes,
`"kp-<digest>"`) and the route honors `If-None-Match` with a `304`. Cache lifetime then
depends on whether the URL fingerprints the asset by **content** or only by **version**:

- **`hashed` (static build).** The filename embeds the content hash
  (`<name>.<sha>.<ext>`), so the URL changes whenever the bytes change.
  This is a true content fingerprint, so these are served
  `cache-control: public, max-age=31536000, immutable` — the browser never revalidates,
  and a changed asset is a new URL.
- **`hosted` (dynamic serve from an embedding host app).** The URL is version-addressed
  (`/kpress-static/v<version>/...`), not content-addressed.
  An upgrade bumps `<version>` and yields a fresh URL, so released upgrades never
  collide with a cached older build.
  Within a single version the assets are served
  `cache-control: public, max-age=31536000` **without `immutable`**: the version is only
  a coarse fingerprint, so the same-bytes-per-URL guarantee can break for a
  source/editable checkout, or if a release ever ships changed assets without bumping
  the version. Omitting `immutable` keeps the in-session cache (zero requests across a
  multi-page browse) while letting a normal reload revalidate against the ETag — a cheap
  `304` when unchanged, fresh bytes when not.
  `immutable` is deliberately avoided here because it suppresses revalidation even on an
  explicit reload, which would strand readers on stale CSS/JS until a hard reload.

Restoring `immutable` on the hosted path would require content-addressed (not merely
version-addressed) URLs, mirroring the `hashed` build mode.
That is the natural future step if the per-reload revalidation cost ever matters; until
then, freshness on reload is worth more than saving one conditional request.

The build manifest records source files, routes, output files, hashes, optimizer
settings, diagnostics, and warnings.
Build and asset manifests include explicit current schema markers:

- `kpress-build-manifest-v1`
- `kpress-asset-manifest-v1`

### Asset sealing: deferred for v1

Sealing the document-local and external-URL asset graph (downloading remote refs,
content-hashing every file, rewriting every URL in HTML + CSS + JS to its sealed local
path, then verifying the tree is free of remote refs) is **on the v2 roadmap**, not in
v1.

Why deferred:

- **Wrong abstraction.** A regex-driven Python rewriter over arbitrary HTML/CSS/JS has
  the wrong fundamentals: every quote variant, every bare specifier, every
  attribute-value edge case is a new bug class.
  The JS ecosystem has converged on real asset-graph bundlers (Vite, Parcel, esbuild,
  Bun, Rollup) for good reason.
- **Deploy layer owns this.** A CDN (CloudFront, Fastly, Cloudflare), static-host
  platform (Netlify, Vercel, GitHub Pages, S3), or reverse-proxy already handles asset
  fetching, hashing, integrity pins, and serving.
  v1 KPress emits HTML + package assets; the deploy layer handles delivery.
- **No current consumer requires it.** Both the dynamic host-app path and the typical
  “publish a doc site behind a CDN” workflow work without sealing.
  Document-local images stay local; CDN script refs stay on the CDN.

What v1 does instead:

- Package assets (KPress’s own CSS/JS/fonts) are copied into the output tree with the
  chosen `asset_mode` shape (linked / hashed / inline).
  This is the only asset graph KPress owns and rewrites.
- KaTeX bundle is copied (unhashed, vendored) when math is present.
- Document-local refs (`./image.png`, `./decor.css`) are emitted into the rendered HTML
  verbatim. The deploy layer places these files, links to a CDN, or accepts a broken
  link.
- External refs (`https://...`) are emitted verbatim.
  The browser fetches at view time, same as any normal site.

What v2 sealing should look like (when it returns):

- Drive the asset graph through a **real parser** (selectolax/lxml + tinycss2 for the
  Python-side option, or — preferred — delegate to a JS bundler at the publish step).
  Stop reinventing HTML/CSS parsing in regex.
- Keep sealing strictly opt-in (`asset_mode=sealed` plus an explicit fetcher config).
  Default `asset_mode` stays `linked` / `hashed`, which require zero network access at
  build time.
- Make the bundler step a clean optional extra (e.g. `kpress[bundle]`) so users who
  don’t need sealing never install Node tooling.

Tracking: see the v2 sealing roadmap entry under `## Implementation Beads` below.

## Optimizer and Precompression

Optimization and precompression are publish steps, never render steps.
Dynamic host rendering must not invoke Node, a minifier, or a compressor.

Development checking and publish optimization are separate concerns.
Biome and `tsc --checkJs` reject bad source but never rewrite published output.
The publish optimizer rewrites deployable artifacts and does not replace those checks.

### Optimizer modes

The optimizer contract has exactly two modes.
There is no built-in regex pseudo-minifier and no silent fallback.

- `none` (default): published HTML/CSS/JS is byte-for-byte the rendered output.
  No Node toolchain is required.
  This is a fully supported output; a static build with `none` is correct, readable, and
  deployable.
- `full`: opt in to Node-backed minification/optimization.
  KPress runs `html-minifier-next@6.2.3` through `npx --package`, so callers keep no
  project `package.json` and npm manages the fetch and cache.
  This mode requires Node.js with `npx` on `PATH`.

Selection is explicit: `optimizer.mode` in `kpress.yml`, `--optimizer`, or
`BuildOptions.optimizer`. If `full` is selected and `npx` is unavailable, optimization
raises `KPressMissingOptionalDependencyError` with an actionable message.
It never downgrades to `none` silently, and an unknown mode is an error.
If optimization is not requested, `npx` is not required.

The current public contract is deliberately simpler than a full JavaScript package
setup: if callers ask for optimization, they need `npx`; if they do not ask for
optimization, they do not need it.
The `npx --package` implementation pins the top-level minifier package while letting npm
own package installation and cache layout.
That is acceptable for the current KPress publishing slice.

A future hardening layer can improve dependency reproducibility without changing that
public contract.
The cleaner long-term shape is modeled on the useful parts of `tminify`:
Python API, tiny JavaScript wrapper, committed lockfile, `npm ci`, file-locked
user-cache installation, and structured subprocess errors.

`full` should be preflighted at the start of a publish operation, before writing or
copying outputs. If `npx` or the optimizer package is unavailable, the publish command
should fail conspicuously with no partial success status and no fallback to `none`.

### Precompression

Precompression is orthogonal to the optimizer and needs no Node.
It writes `.gz` / `.br` sidecars next to deployable text files for origins that perform
static precompressed negotiation (nginx `gzip_static`, Caddy `precompressed`, Apache
MultiViews, or an explicit CloudFront/Lambda@Edge rule).

It is off by default regardless of other axis settings.
Pure CDN and managed hosts (CloudFront auto-compression, Cloudflare, Netlify, Vercel,
GitHub Pages) compress at their own edge and ignore committed sidecars, so emitting them
there is dead weight and manifest noise.
Enable it only when the deploy origin actually serves sidecars:
`optimizer.precompress: [gzip]`, `[br]`, `[gzip, br]`, or `--precompress`.

- `gzip` uses the Python standard library and is always available.
- `br` requires the `kpress[optimize]` extra (the `brotli` library).
  Requesting `br` without it raises `KPressMissingOptionalDependencyError`, the same
  explicit-error philosophy as the `full` optimizer.
  There is no fallback.

### Manifest and equivalence

- The build manifest records the resolved optimizer mode per optimized file
  (`optimizer_backend` is `full`, or absent for `none`), `original_size` when a file was
  rewritten, and the compression method and sizes for each sidecar.
- `none` plus optional precompression preserves the rendered document surface exactly.
  `full` must preserve functional equivalence with `none`: the only accepted differences
  are minification, hashing, URL shape, and compression.
- Tests prove dynamic rendering never imports the optimizer.

## Local Document Workflows

KPress should preserve useful local document workflows without hosted service coupling.

Commands:

```bash
kpress init
kpress convert INPUT --output OUTPUT.md
kpress format INPUT --output-dir DIR --show
kpress render INPUT.md --output OUTPUT.html --show
kpress paste --title TITLE --plaintext --show
kpress files --all
kpress export INPUT.md --html OUT.html --pdf OUT.pdf --docx OUT.docx
kpress build --config kpress.yml
kpress build --config kpress.yml --asset-mode hashed --optimizer full --precompress gzip
kpress check --config kpress.yml
kpress seal --config kpress.yml
kpress optimize public/
kpress pdf INPUT.md --output OUT.pdf
```

Global workflow flags:

- `--work-root`
- `--rerun`
- `--refetch`
- `--show`
- `--strict`
- `--asset-mode`

The workflow layer owns workspace paths, cache semantics, output names, local reports,
paired Markdown/HTML output, sidematter copying, and image URL rewriting.
Hosted login, upload, accounts, and public service URLs stay outside KPress core.

## Doctor

`kpress doctor` is a runtime-capability readiness probe, not a development quality gate
(it never runs Biome, `tsc --checkJs`, Vitest, Ruff, basedpyright, package-policy, or
formatting; those stay in `devtools/lint.py`). It answers whether the installed package
can render, publish, optimize, precompress, or export PDF on this machine with the
dependencies currently present.

`kpress.publish.probe_capability`/`probe_all` and the dataclass `ProbeResult` (status
one of `ok`/`unavailable`/`skipped`/`fail`, optional snake_case `reason`) are the single
source of truth, shared with the `optimizer=full` preflight in
`build_site()`/`build_html()`.

- Default `kpress doctor`: lightweight, no network, discovery only; never fails the
  process.
- `--profile {render,publish,optimize,pdf}`: probe one capability; a requested profile
  that is not `ok` exits non-zero.
- `--config kpress.yml`: config-aware aggregate.
  There is no `dev`/`production` mode; doctor reads the resolved explicit axes and fails
  only when a capability the config actually requires (optimizer `full`, `br`
  precompression, or PDF enabled) is unavailable.
- `--allow-network`: only gate for the optimizer cold-cache smoke; the `npx` presence
  check is always no-network.
- `--json`: stable `{kpress_version, platform, capabilities}` with the closed status
  set.

Capability semantics mirror the runtime contract: `optimizer=none` with no `npx` is OK;
`optimizer=full` without the toolchain, `br` without `brotli`, or PDF without Playwright
are failures only when that path is requested, otherwise reported
`unavailable`/`skipped`.

## Browser Asset Quality Gate

KPress browser JavaScript and CSS are first-class package source.

Required tooling:

- repository package supply-chain policy for exact npm/PyPI tool pins and the two-week
  new-release cooldown
- Biome 2 for JS/CSS/JSON formatting and linting, run through the package-owned
  exact-version wrapper
- `tsc --checkJs` for native JavaScript type checking with JSDoc
- Vitest with `happy-dom` for browserless DOM behavior tests
- Ruff and basedpyright for Python
- codespell for docs/source
- CI job `lint-kpress`
- lefthook staged-file formatting and validation for KPress Python, JS, CSS, and JSON

Runtime JavaScript should be native ESM and should not require a build step for dynamic
hosts. If TypeScript source is introduced later, it must include a stale-build check and
generated output policy.

## Document Acceptance and Regression Harness

The long-term contract is accepted KPress output, not TextPress/Kash compatibility.
Reference implementations may seed the first fixture corpus, but once a scenario is
accepted, current KPress output is compared to accepted KPress baselines.

Required layers:

- canonical source fixture corpus
- optional reference artifacts from TextPress/Kash for implementation review only
- accepted KPress golden artifacts under `tests/golden/accepted/`
- normalized DOM structural diffs
- HTML validity checks: duplicate IDs, broken anchors, ARIA references, landmarks,
  sanitizer expectations
- CSS selector coverage and validity checks
- JavaScript checks: Biome, `tsc --checkJs`, browserless Vitest/`happy-dom` behavior
  tests
- manual Playwright-assisted checks for browser-load errors, unhandled promises, missing
  modules, unexpected globals, interactions, console/network state, mobile, dark mode,
  print media, screenshots as review evidence, and PDF probes

The component phase cannot close until every required component has accepted KPress
baselines, visual approval, structural checks, browser review notes, and print checks.

## Accessibility

KPress output should support:

- sensible landmark structure
- ordered headings
- accessible theme controls
- accessible TOC controls
- keyboard usable details, tabs, and popovers
- live-region feedback for transient copy status
- reduced-motion behavior for animated reader controls
- tooltip triggers that degrade cleanly on touch/mobile
- readable color contrast in light, dark, and print modes
- print output that excludes screen-only controls

Accessibility checks should be automated where practical and backed by fixture review.

## Host Integration

The embedding host should call KPress through the dynamic runtime and serve KPress
assets. It should not copy component CSS or JavaScript into host-specific selectors.

Host responsibilities:

- read files and frontmatter
- choose active view and printability
- map host view names to KPress profiles
- serve KPress package assets
- hide host chrome during print
- handle KPress unavailable mode gracefully
- keep navigation and shell controls outside KPress fragments

KPress responsibilities:

- render document fragments/pages
- own document CSS and JS
- own document print profile
- declare required assets
- provide diagnostics
- generate static outputs and PDFs when called through publisher APIs

### Dynamic render contract

The host calls `kpress.runtime.render_view(KPressRenderRequest)` and receives a
JSON-ready dict. Fields and semantics:

| `KPressRenderRequest` field | Required | Meaning |
| --- | --- | --- |
| `source_text` | yes | Raw document bytes the host has already read from disk |
| `source_path` | yes | Relative path inside the host’s worktree; used for diagnostics, link resolution, and the source-profile header |
| `kind` | yes | Host-side file kind (`markdown`, `text`, `structured`, etc.); KPress dispatches on this |
| `view` | yes | Host-side view name (`rendered`, `source`, `tree`, …); normalized via `normalize_print_profile` into a KPress profile |
| `ext` | yes | Lowercase file extension including the dot; used for syntax-profile selection on source views |
| `mtime_hash` | yes | Host-supplied content fingerprint; drives the in-process render cache and ETag |
| `size` | yes | Byte size of the source; used for large-file truncation guards on source views |
| `frontmatter` | no | Parsed YAML metadata the host already extracted; KPress treats this as authoritative |
| `frontmatter_error` | no | Host-side YAML parse error string; surfaced as a visible reader banner |
| `profile` | no | Optional explicit KPress profile override; bypasses the view-name mapping |
| `theme_mode` | no | `"system"` (default), `"light"`, or `"dark"` — the user’s theme preference |
| `resolved_theme` | no | `"light"` or `"dark"` — the host’s resolution of `system` for SSR/no-flash bootstrap |
| `host` | no | Free-form host identifier for diagnostics; KPress never special-cases this value |
| `asset_url_prefix` | no | URL prefix the host uses to serve `/kpress-static/...`; defaults to `/kpress-static/` |

Render response shape:

```jsonc
{
  "type": "kpress-rendered-document",
  "html": "<!-- HTML fragment to inject into the document body -->",
  "profile": "document" | "source" | "table" | "tree" | "plain",
  "printable": true,
  "assets": { "css": ["<asset_url_prefix>v0.0.1/css/document.css", ...],
               "js":  ["<asset_url_prefix>v0.0.1/js/theme.js", ...] },
  "diagnostics": []
}
```

The response is JSON-round-trippable.
The host injects `html` into a container, links the listed CSS, and loads the listed JS
as `type="module"`. There is no per-request mutation of global state.

### Asset serving

KPress package assets live at `/kpress-static/<v>/<rel_path>` where `<v>` is the package
version segment (`v0.0.1`). The host mounts a route that calls
`kpress.runtime.get_static_asset(rel_path)` and returns the resulting `KPressAsset`
(`content`, `media_type`, `etag`, `cache_control`). The runtime guarantees:

- Path traversal is rejected (paths with `..` or absolute prefixes raise
  `KPressAssetNotFoundError`).
- Versioned URLs (`/kpress-static/v0.0.1/...`) return
  `cache-control: public, max-age=31536000` (long-lived, but **not** `immutable`);
  unversioned URLs return `no-cache`. The version segment is only a coarse fingerprint,
  so the host can revalidate against the ETag rather than being locked to stale bytes —
  see “Static asset caching” above for the rationale.
- `etag` is content-stable; the host can honor `If-None-Match` (the route answers a
  matching conditional request with `304`).

A host that wants to point at a CDN-hosted KPress bundle passes a different
`asset_url_prefix` in `KPressRenderRequest`; KPress URL-builds against that prefix
without any code change.

### `postMessage` protocol (embedded reader → host)

When the reader runs inside an iframe (or any sandboxed host), `js/host.js` posts the
following messages to the parent window so the host can resize, expand, or close the
embedded surface:

| Message type | Payload | When |
| --- | --- | --- |
| `kpress:ready` | `{ id?, height }` | First paint settled; the host can size the iframe |
| `kpress:resize` | `{ id?, height }` | Reader content size changed (DOM mutation, font swap, viewport change) |
| `kpress:expand` | `{ id?, expanded: bool }` | User toggled the standalone expand control |
| `kpress:close` | `{ id?, reason: “control” | “escape” }` |

The host opts into Escape-to-close behavior; KPress does not assume it.
All messages include the document id when one was provided.

### Theme mode plumbing

`theme_mode` is one of `"system" | "light" | "dark"` and represents the user’s
preference. `resolved_theme` (`"light" | "dark"`) is the host’s resolution of `system`
for the initial server render — KPress uses it to stamp `data-kpress-resolved-theme` on
`<html>` for a no-flash first paint.

After load, `theme.js` listens for the system color-scheme media query and updates the
resolved attribute live; it also persists explicit `theme_mode` choices to
`localStorage` under `kpress-theme-mode`. The standalone full-page render ships an
accessible System/Light/Dark toggle bound to the same machinery; embedded hosts that
have their own theme control should set `theme_mode` per request and let KPress derive
the resolved theme.

### Print profile mapping

The host’s `view` (or explicit `profile`) maps to a KPress print profile via
`normalize_print_profile`. The accepted KPress profiles are
`{document, source, table, tree, plain}`. Host aliases that already work:

| Host view | KPress profile |
| --- | --- |
| `rendered`, `doc`, `markdown` | `document` |
| `text`, `code` | `source` |
| any unrecognized name | rejected with `KPressInvalidRequestError` |

The print profile drives `print.css` rules: `document` strips chrome and prepares for
A4/Letter pagination; `source` keeps line numbers and switches to mono; `table` / `tree`
reuse the source profile with structural overrides.
The host hides its own chrome (`.app-header`, `.tab-bar`, `.tree-pane`, `.file-header`)
via its own `@media print` rules — KPress does not reach outside its `.kpress`
container.

### Static export seam

For “render this document into a publishable artifact” use cases, the host calls
`kpress.runtime.export_document(KPressExportRequest)` rather than `render_view`. The
request carries the same `path`/`kind`/`view`/`theme_mode` as a render request plus
publisher-side levers:

| `KPressExportRequest` field | Choices | Meaning |
| --- | --- | --- |
| `print_profile` | `document`/`source`/`table`/`tree`/`plain` | Same as the render contract |
| `export_mode` | `page` (default), `single-file`, `static-hosted`, `sealed-static-hosted`, `pdf` | Which output shape to produce. `single-file` is deferred per “Self-contained single file: deferred”. |
| `asset_mode` | `linked` (default), `inline`, `sealed` | Underlying asset-shaping axis from the build levers |
| `optimize` | bool | Maps to `optimizer=full` when true |
| `destination` | path | Where to write the artifact; KPress derives a default from `path` if omitted |

This is a thin wrapper around `kpress.workflow.export_document` and
`kpress.publish.build_site`; the host translates the user’s “export this file” gesture
into a request, then surfaces the returned build report (or `KPressRenderError` /
`KPressMissingOptionalDependencyError`) to the user.

### Failure modes the host must handle

| Exception | Origin | Host response |
| --- | --- | --- |
| `KPressInvalidRequestError` | Malformed request (e.g. unknown print profile) | 400 with the underlying message |
| `KPressRenderError` | Render pipeline raised | 502 with diagnostics |
| `KPressAssetNotFoundError` | Asset path rejected as unsafe or missing | 404 |
| `KPressUnavailableError` | KPress package not importable | 503; degrade to a host-side fallback if any |
| `KPressMissingOptionalDependencyError` | Static-export with `optimizer=full` and no npx, or `pdf` with no Playwright | 503 (or surface to the user as a setup error) |

`KPressInvalidRequestError` is a `ValueError` subclass for ergonomic catching, but hosts
should catch it specifically rather than catching all `ValueError`s.

### Reference adapter

The original host app’s `kpress_adapter.py` is the canonical embedding reference:
optional import (`try: from kpress import runtime`), translated exceptions (every KPress
exception type is re-wrapped into a host-side type so callers never need to import
kpress), and an explicit `kpress_available()` probe for graceful degradation.
Other embedding hosts (Electron viewers, hosted web deployments, custom web apps) should
follow the same pattern.

## Implementation Beads

The active bead map is the implementation authority.
Key beads:

| Bead | Scope | Status |
| --- | --- | --- |
| `orig-wkzp` | KPress package and static publisher epic | open |
| `orig-xgzj` | granular KPress reader feature parity epic | open; child beads now own every missing reader feature |
| `orig-bht8` | package skeleton, workspace wiring, import boundary | implemented in PR #111 |
| `orig-h2xx` | write this public design contract | implemented in PR #111 |
| `orig-kfwn` | full typed models, validation, theme, resources | implemented in PR #111 |
| `orig-skuk` | golden testing harness and accepted fixtures | implemented in PR #111 |
| `orig-pyhv` | render fragment/page runtime | implemented in PR #111 |
| `orig-xmov` | Markdown, sanitizer, source rendering | initial implementation in PR #111 |
| `orig-8is3` | Markdown/GFM and document-tree reader parity | open; full parity required |
| `orig-131h` | document CSS, theme assets, print CSS, JS helpers | source-adapted typography/theme/print first pass implemented; visual acceptance open |
| `orig-d6g2` | TOC, footnotes, tooltips, tables, code components | initial source-adapted components and DOM tests implemented; deeper browser behavior open |
| `orig-selz` | semantic content and document-format component parity | source-adapted semantic CSS/page metadata first pass implemented; fixtures and visual acceptance open |
| `orig-5dmd` | font and packaged asset sealing reader parity | packaged PT Serif/Source Sans assets implemented; broader reader asset sealing open |
| `orig-q72a` | document acceptance browser/PDF fixture suite | structural/PDF checks implemented; browser visual suite open |
| `orig-8kp9` | Tailwind behavior migration into KPress CSS | implemented in PR #111; visual parity hardening remains future work |
| `orig-ngq8` | publisher config, discovery, metadata, routes | implemented in PR #111 |
| `orig-lghl` | asset manifest, cache, sealing, offline verification | implemented in PR #111 |
| `orig-jm5n` | static build pipeline, site files, CLI | implemented in PR #111 |
| `orig-u1mo` | optional dependency boundary hardening | implemented in PR #111 |
| `orig-25bk` | package-owned JS quality gate and browserless DOM tests | implemented in PR #111 |
| `orig-v4an` | repository-wide package release cooldown and exact tool pins | implemented in PR #111 |
| `orig-2l9z` | TextPress-compatible local workflows | initial workflows implemented in PR #111 |
| `orig-p5q6` | optional optimizer and precompression | current implementation includes rendered HTML optimization, CSS/JS asset optimization, hashed assets, manifests, gzip precompression, and Brotli optional-extra precompression; locked Node package and optimizer metadata remain future hardening |
| `orig-n7ok` | browser-print PDF generation | deterministic PDF artifact implemented; optional Playwright browser backend is code-side implemented; fixture PDFs and manual inspection remain open |
| `orig-0xa1` | public contract hardening and host readiness | current API/CSS/template/manifest contract implemented; accessibility and host-readiness review remain open |
| `orig-obq5` | PR #111 review cleanup | implemented in review follow-up: sanitizer, sanitized-local, fence-safe Markdown, offline sealing, theme bootstrap, interactions, strict typing, publishing API cleanup, optional extras, and status docs |
| `orig-t3ud` | remove asset sealing for v1; defer to v2 roadmap | open; epic — strips regex-driven HTML/CSS/JS rewriter from v1, keeps package-asset copying, parks sealing on the v2 roadmap (real parser or JS bundler). See `docs/project/specs/active/plan-2026-05-21-kpress-remove-sealing-for-v1.md` |
| `orig-mfvi` | v2 sealing: real parser or JS bundler over the asset graph | open; v2 roadmap — drives HTML/CSS/JS through a real parser or delegates to Vite/Parcel/esbuild/Bun at publish; restores `verify_offline_tree` and air-gapped `Static build sealed` mode |

Reader parity child beads under `orig-xgzj`:

| Bead | Reader feature |
| --- | --- |
| `orig-97c1` | GFM Markdown block and inline document tree |
| `orig-1rc7` | raw HTML trust and sanitizer matrix |
| `orig-oxs3` | images, figures, captions, and local media assets |
| `orig-c5xy` | code fences, source profiles, and syntax highlighting |
| `orig-g0ra` | `off`/lazy-`auto` KaTeX math design |
| `orig-lir6` | diagram rendering providers |
| `orig-vdbu` | typography, document CSS, and themes |
| `orig-boxw` | print CSS and print profiles |
| `orig-i4rj` | desktop TOC behavior |
| `orig-o59o` | mobile TOC drawer behavior |
| `orig-1u4r` | footnote hover and touch tooltips |
| `orig-2z84` | internal-link preview tooltips |
| `orig-09i3` | responsive tables and numeric-cell hooks |
| `orig-vy98` | code-copy controls |
| `orig-m83y` | video popovers and embedded media policy |
| `orig-wv4m` | tabbed content components |
| `orig-3l2o` | semantic content components |
| `orig-mzp0` | fonts and packaged reader assets |
| `orig-4mdl` | canonical fixture corpus and accepted goldens |
| `orig-azna` | manual browser acceptance playbook |
| `orig-zwc2` | browser-backed PDF generation and fixtures |
| `orig-t2rf` | accessibility and host-readiness checks |
| `orig-08y5` | final reader parity audit and closure gate |

Matrix-specific closure beads created from
`docs/project/reviews/review-2026-05-17-kpress-feature-parity-matrix.md`:

| Bead | Matrix issue |
| --- | --- |
| `orig-dz9t` | ship Pygments syntax-highlight themes for light and dark mode |
| `orig-blqw` | harden Markdown/GFM edge parity |
| `orig-4iuf` | add a visible frontmatter parse-error affordance |
| `orig-o2vp` | add source large-file and truncation handling |
| `orig-mgct` | implement image URL rewriting, sidecar assets, figures, and captions |
| `orig-mne3` | define and implement external link target/rel policy |
| `orig-hne1` | complete TOC behavior fidelity |
| `orig-m84t` | port the full footnote/internal-link tooltip system |
| `orig-viq1` | style code-copy controls and states |
| `orig-jhxx` | specify and implement math rendering as net-new work |
| `orig-32r0` | specify and implement diagram rendering |
| `orig-2vx3` | decide and implement standalone theme toggle behavior |
| `orig-1fwg` | finish table responsive and print polish |
| `orig-ntct` | finish video popover maximize/coexistence/network behavior |
| `orig-vy1h` | generate Kash/TextPress semantic document components |
| `orig-iape` | finish tab authoring surface, styling, and print policy |
| `orig-f3e8` | complete print CSS parity |
| `orig-14v1` | implement browser-backed PDF generation |
| `orig-9h7y` | define host embedding resize/expand/close protocol |
| `orig-2h7t` | complete accessibility and reduced-motion parity |

The final audit bead `orig-08y5` depends on every matrix-specific bead above.
That dependency is intentional: parity cannot be declared complete while any matrix gap
remains open.

## Acceptance Milestones

1. **Design complete:** this document exists, plan spec is clear, the reader parity
   ledger maps every feature to beads, manual confirmation gates are explicit, and
   current implementation status is explicit.
2. **Runtime foundation:** full models, render fragment/page, Markdown/source rendering,
   and minimal accepted baselines.
3. **Document components accepted:** KPress-owned CSS/JS/components, Tailwind migration,
   visual approval, browser checks, print checks, PDF checks where relevant, manual
   confirmation records, and accepted baselines.
4. **Publisher complete:** config, discovery, routes, assets, sealing, cache, manifests,
   asset/optimizer/precompression axes, and static output goldens.
5. **Workflow complete:** local convert/format/render/paste/files/export CLI and golden
   command tests.
6. **Production artifacts complete:** optimizer, precompression, PDF generation, and
   offline verification.
7. **Host readiness:** accessibility, current public contract, host integration
   contract, and package docs are stable.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
