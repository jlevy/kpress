---
title: KPress Design
description: Package contract for KPress document rendering, document components, static publishing, asset handling, optimization, PDF generation, and acceptance testing.
author: Codex under Levy
---
# KPress Design

**Status:** Draft design contract

**Last Updated:** 2026-06-15

## Purpose

KPress is a standalone document viewing and publishing layer.
It provides a reusable format runtime for embedding host applications and a static
publisher for creating publishable HTML/CSS/JavaScript/PDF artifacts from Markdown,
source files, and document inputs.

KPress owns document presentation.
Host applications own browser chrome, navigation, workspace state, tabs, file trees,
authentication, deployment, and service-specific publishing.

## Core Principles

These govern what belongs in KPress and how it is built.

1. **Simple should be simple; complex should be possible.** Common
   customizations—changing a few colors, swapping a font—are trivial; arbitrary
   customization stays reachable.
   Convenience layers are optional and sit *on top of* the primitives, never in place of
   them.

2. **Adhere to and expose native browser abstractions.** Prefer the web platform—CSS
   custom properties, plain HTML/CSS/JS—over framework machinery, so output stays
   maintainable and customizable without bloat.
   The themeable design system *is* a documented set of CSS variables (the `--kpress-*`
   / `--kpress-host-*` contract); a host themes by setting those vars and, for anything
   beyond them, by injecting its own HTML/CSS/JS.

3. **Batteries included as optional building blocks.** The core knowledge-presentation
   features ship first-class and polished by default—tooltips and footnote previews, the
   mobile-friendly table of contents, tables, math and diagrams, code highlighting, the
   settings menu with light/dark mode, and responsive support—but each is a **component
   that can be turned off or customized**, down to its sub-settings (e.g. when the TOC
   appears or collapses).
   Complete by default; nothing forced.
   Built-in **palette themes** (named bundles of the CSS-var contract, e.g. `neutral`
   and `warm`) are convenience presets in this same spirit: selectable, overridable,
   never special-cased.
   Every setting maps to a **specific component or aspect**; KPress does not accumulate
   an arbitrary grab-bag of flags or named layouts.

4. **Own the document layer, not the app.** KPress focuses on the document model,
   rendering, and efficient packaging of web assets.
   It does **not** own app or publishing workflows: static-site building, navigation,
   deployment, and other service-specific concerns belong to the host.
   Site headers, nav pages, back-links, and similar chrome are authored by the client’s
   own workflow and injected through the chrome slots (`header_html` / `footer_html` /
   `head_extra_html`): KPress provides the slots, not the content or the workflow.
   Composing a site out of different feature sets is likewise a host concern, not a
   KPress setting.

5. **Customization is front-end code; Python orchestrates and injects it.** Anything
   interactive or per-reader—widget behavior and markup, choosers, hover handling,
   client state—is standard JavaScript/CSS over published data, never modeled in Python.
   Python decides *what ships* (which widgets, opaque config, slots, assets) and runs
   the build; the one Python exception is whole-artifact build-time processing (a proper
   build step: minification, tree/HTML transforms).
   Three placement rules keep every seam at this altitude (see
   [Extension and Injection Model](#extension-and-injection-model)):

   - **The no-JS rule:** server-render only what is meaningful without JavaScript (the
     document, TOC links, footnotes).
     Chrome that only functions with JS (a settings menu, a minimap) is client-rendered
     by a widget; a control that can do nothing without JS should not render without JS.
   - **The schema-with-the-code rule:** a widget’s config schema lives in the widget’s
     front-end code; Python/YAML transports opaque JSON and never knows what the widget
     *is*, only *that* it ships.
     No Python dataclasses for client concepts.
   - **The dogfood rule:** every built-in widget and behavior is implemented on the
     public layers exactly as a third-party one would be.
     If a host couldn’t build it outside KPress, the built-in may not use a private path
     either. This is the acceptance test that an abstraction is not too narrow.

6. **Plugin contracts are text and files, not an AST.** Content features extend KPress
   as *plugins*: a files-to-files Markdown→Markdown preprocessing step (syntax sugar
   that desugars to admitted custom tags) and/or front-end CSS/JS over those tags.
   The preprocessing boundary is plain Markdown text and file paths, never a KPress
   parse tree, token stream, or language-bound callback, so a plugin can be written in
   any language and does not break when KPress internals change.
   A tree-shaped surface is used only *inside* a preprocessor (for robust block
   boundaries) and as the in-process `transform_tree` build convenience, never as the
   cross-process contract.
   See [Plugins and the Document Dialect](#plugins-and-the-document-dialect).

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

## Feature Catalog

Everything KPress currently implements, by area.
The subsections after the table are the reader-feature behavior contract (what each
feature guarantees); the sections named in the table carry the architecture detail.

| Area | Current implementation | Detail |
| --- | --- | --- |
| Markdown rendering | GFM via `markdown-it-py` + plugins: stable duplicate-safe heading IDs, footnotes and backrefs, fence-safe parsing | Markdown, Sanitization, and Source Rendering |
| Sanitization and trust | nh3 single authority; `trusted` / `sanitized` trust modes, failing closed on unknown values; pass-through whitelist (`div`/`span` + host `extra_tags` on every path) and host-declared inert `extra_attributes` (e.g. `kind`, `term`), both validated against forbidden-name sets | Markdown, Sanitization, and Source Rendering |
| Code and source views | Pygments highlighting, code-copy controls, printable source profiles | Document Profiles; Document Components |
| Math | KaTeX with `off` / lazy `auto` modes; semantic MathML output; zero math assets when absent | Feature Catalog subsections below |
| Diagrams | Mermaid adapter behind explicit hooks; SVG passthrough | Feature Catalog subsections below |
| Tables | Responsive wrapping, numeric-cell hooks, print flattening | HTML Contract |
| TOC | Server-rendered desktop/mobile TOC with disclosure and active-link tracking | Document Components |
| Tooltips and footnotes | Footnote hover/touch previews and internal-link tooltips, keyboard accessible | Document Components |
| Media | Image/figure handling, YouTube popover interception | Document Components |
| Tabs | Tabbed content with keyboard access | Document Components |
| Theming | Light/dark/system with pre-paint bootstrap; `neutral`/`warm` palettes; container-query responsive layout | Design System; Theme and Fonts |
| Fonts | Vendored PT Serif / Source Sans 3 / mono with `custom`/`system` modes and per-role host overrides | Theme and Fonts |
| Widgets and extensions | Page-model block, widget registry (settings gear, choosers), tree/page transforms, head/header/footer slots | Extension and Injection Model |
| Document dialect | Open custom-tag admission for host plugins (preprocessors emit tags; hosts style them) | Plugins and the Document Dialect |
| Static publishing | Config, source discovery, routes, manifests, site files, `hosted`/`linked`/`hashed`/`inline` asset modes | Static Publishing; Asset Model |
| Optimization | Optional HTML/CSS/JS minification and gzip/Brotli precompression sidecars (`kpress[optimize]`) | Optimizer and Precompression |
| PDF | Deterministic print-profile PDF artifacts; browser-backed generation behind `kpress[pdf]` | Feature Catalog subsections below |
| Local workflows | CLI: `init` / `convert` / `format` / `render` / `paste` / `files` / `export` / `build` / `optimize` | Local Document Workflows |
| Dynamic hosting | `render_view` fragments with caching, `extra_tags` parity with publish, static asset serving, `postMessage` protocol | Host Integration |
| Quality gates | Golden/DOM/browserless suites, Biome + `tsc --checkJs`, doctor checks | Doctor; Browser Asset Quality Gate; Document Acceptance and Regression Harness |
| Accessibility | Landmarks, semantic tooltips, keyboard interactions, reduced-motion respect | Accessibility |

### Foundation

- **Host-neutral runtime.** A document renders as a fragment or a complete standalone
  page through a host-neutral API. KPress does not depend on any particular embedding
  host.
- **Standalone page shell.** Complete pages provide title, document landmarks, metadata,
  diagnostics surfacing, and the document’s own asset references.
- **Social and page metadata.** Open Graph, Twitter, and canonical metadata are emitted
  from document metadata with defined precedence.
- **Host embedding protocol.** An embedded document posts host-neutral
  `kpress:ready`/`kpress:resize`/`kpress:expand`/`kpress:close` messages with the
  document id and measured dimensions; expand/close controls and opt-in Escape-close are
  supported. The embedding host decides how to react.

### Markdown and document tree

- **GFM block and inline parsing.** Headings, paragraphs, nested lists, blockquotes,
  links and autolinks, strikethrough, task lists, hard/soft breaks, and code fences.
- **Stable heading anchors and TOC metadata.** Deterministic, de-duplicated heading ids
  with plain inline titles; broken-anchor diagnostics; a single leading H1 is excluded
  from the TOC.
- **Raw HTML trust modes.** `trusted` (no sanitization, for your own files) and
  `sanitized` (for anyone else’s content: embeds, publishing, exports) with a defined
  safe/unsafe policy and diagnostics; see
  [The Document Dialect and Trust Modes](#the-document-dialect-and-trust-modes).
  The sanitized mode admits a configurable pass-through tag allowlist (`<span>`/`<div>`
  always, plus `format.html.extra_tags`) carrying `class`/`data-*` plus any
  host-declared inert `format.html.extra_attributes` (semantic names like `kind` or
  `term`); `style`, `on*` handlers, and unsafe URLs are always stripped.
- **Footnotes.** Definitions, references, backrefs, tooltip-ready anchors, sequential
  superscript numbering (markers show `1, 2, 3 …` matching the footnotes section
  regardless of the authored label), missing-reference and unused-definition
  diagnostics, and simplified print rendering.
- **Code fences and syntax highlighting.** Language-classed code blocks with server-side
  token markup and a shipped light and dark highlight stylesheet.
- **Source profile.** Large source files are capped to a bounded preview with a visible
  truncation notice; a filename/extension language fallback applies.
- **Math.** Public modes are `off` and lazy `auto`. `off` leaves delimiters literal and
  loads nothing. `auto` detects math before doing any math work: a document with no math
  loads no math code or assets.
  When math is present KaTeX is the active renderer; it is applied progressively, after
  the rest of the document has rendered, so prose is never blocked on math.
  Until KaTeX takes over (and when scripting is unavailable) the equivalent MathML is
  shown; once KaTeX has rendered, that MathML remains as the semantic and accessibility
  output. Math font faces are fetched on demand, only when an expression actually needs
  them. (MathJax is out of scope unless real content proves KaTeX insufficient.)
- **Diagrams.** SVG fences render as sanitized inline SVG figures; Mermaid fences render
  as diagram figures with a readable source fallback and a progressive renderer when the
  host provides Mermaid.
- **External link policy.** Absolute HTTP(S) links open in a new tab with
  `rel="noopener noreferrer"`; anchors, relative links, and `mailto:` are unchanged.

### CSS and layout

- **Prose typography.** A full reading type scale: headings, spacing, lists, links, and
  long-form measure.
- **Lists.** Screen markers plus a print ordered-list grid and nested-list print resets,
  including long-list handling.
- **Links, selection, scrollbars.** Reader-grade selection and scrollbar styling.
- **Details, metadata, and frontmatter blocks.** Collapsible metadata with a defined
  print policy; a visible, accessible frontmatter parse-error affordance.
- **Named semantic blocks.** Authorable semantic containers and classes for highlights,
  citations, claims, summaries, concepts, annotations, captures, galleries,
  hero/subtitle/boxed/shaded/centered/justified content, styled consistently and scoped
  under the document root.

### Theme and fonts

- **Light, dark, and system modes** with localStorage persistence,
  `prefers-color-scheme` response, and a synchronous pre-paint no-flash bootstrap.
- **Standalone settings menu.** Full pages ship an accessible, no-print gear-icon
  popover with a `system`/`light`/`dark` icon chooser (ported from the original host
  app’s design); embedded hosts own the control instead.
- **Font model.** A global `font_mode` selects vendored reader faces (`custom`) or the
  platform stack (`system`); reader fonts, when used, are vendored and sealed offline
  (no CDN at publish).

### Interactions

- **Table of contents.** Desktop sticky rail with active-heading tracking and smooth
  scroll; mobile drawer with backdrop, body-scroll lock and restore, scrollbar-width
  compensation, outside-click and Escape close, and iOS overscroll handling.
- **Footnote tooltips.** Hover, focus, and touch previews with truncation, a navigation
  link, delayed hide, and a trigger-to-tooltip hover bridge; accidental footnote
  navigation is prevented.
- **Internal-link tooltips.** Previews for headings (with nearby text), figures, tables,
  code, and details, with viewport-aware placement, arrow positioning, touch fallback,
  and Escape close.
- **Tables.** Responsive wrapping, numeric-cell alignment hooks, small-caps headers,
  zebra rows, TOC-aware desktop breakout, mobile font reduction, and print flattening.
  Each cell also carries a `data-col="<header-slug>"` enrichment hook (and numeric cells
  a `data-kpress-numeric` hook) so downstream decorators can select columns by name
  without kpress depending on them.
- **Code copy.** A per-block copy control with success/error/idle states, accessibility
  labels, and print suppression.
- **Video popovers.** YouTube link and raw-embed interception into a no-network
  placeholder that opens a focus-trapped dialog with maximize/restore, mobile body lock,
  and TOC coexistence; sealed output makes no eager network calls.
- **Tabbed content.** Markdown-authored tab containers hydrate into ARIA tablists with
  keyboard support; print shows every panel with its title.

### Media and assets

- **Images and figures.** Standalone images emit semantic `<figure>/<figcaption>`; raw
  HTML figures receive the same hooks; a document thumbnail renders when provided.
- **Offline sealed assets.** Local assets, and approved external assets, are
  fetched/sealed into the output with manifest provenance; published output is
  verifiably free of unexpected network references.

### Print and PDF

- **Print CSS.** Page rules, paper palette, no-print/print-only, TOC and video
  suppression, heading/table break control, repeated table headers, footnote
  simplification, code wrapping, and orphans/widows.
- **Browser-backed PDF.** An optional browser backend renders the print profile to PDF;
  absence of the optional dependency produces a clear error, never a silent downgrade.

Implementation status, milestones, beads, and the reference-migration record live in
[`kpress-completion-plan.md`](kpress-completion-plan.md), with [`TODO.md`](../TODO.md)
as the fine-grained ledger.
This design doc is architecture and public contract only and carries no status ledger or
reference-system comparisons.

## Dependency Rules

The package must keep dynamic viewing lightweight.

- `kpress.format` must be importable without importing `kpress.publish`
- `kpress.format` must also avoid importing PDF, optimizer, subprocess, browser, or
  Node-related code at import time
- `kpress.runtime` may expose dynamic-host helpers and package asset serving
- static publishing dependencies must stay under `kpress.publish` or optional extras
- Node-backed tooling is allowed for author checks and optional production optimization,
  but dynamic rendering must not invoke Node
- KPress ships no Tailwind: no runtime, no generated CSS, no build step; all styling is
  KPress-owned CSS (asset-contract tests guard this)
- heavy import/export features belong behind optional extras with deterministic
  missing-extra errors
- An embedding host must depend only on the thin runtime surface for dynamic views and
  static asset serving; it must not import publisher, optimizer, or browser-PDF modules
  while serving normal document views

The optional extras that exist today: `kpress[pdf]` (browser-backed PDF generation) and
`kpress[optimize]` (Brotli precompression sidecars).
Future packaging tiers are tracked in
[`kpress-completion-plan.md`](kpress-completion-plan.md).

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
build_site(config: KPressConfig | Path | str = "kpress.yml") -> BuildReport
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

Extension-model surface (see
[Extension and Injection Model](#extension-and-injection-model)):

- `RenderOptions.widgets` / `format.widgets`: the uniform widget presence and opaque
  config map (Python’s entire involvement with chrome).
- `build_site(config, options=None, extensions=BuildExtensions(pipeline=…, transform_tree=…, transform_page_html=…))`
  (the build pipeline seam).
- The client runtime `window.kpress` (`static/js/runtime.js`), see
  [Host Integration](#host-integration).
- Name contracts in `kpress.contract`, mirroring `PUBLIC_CSS_VARIABLES` /
  `PUBLIC_CSS_CLASSES`: `PUBLIC_WIDGETS` (built-in widget ids), `PUBLIC_BEHAVIORS`
  (built-in behavior ids), `PUBLIC_JS_EXPORTS` (stability-pinned module exports),
  `PUBLIC_PIPELINE_STAGES` (built-in stage names), `PUBLIC_PAGE_MODEL_KEYS` (page-model
  block keys).

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

## Markdown, Sanitization, and Source Rendering

Markdown target capability:

- GFM tables
- footnotes
- task lists
- generated heading IDs
- raw HTML in trusted mode
- sanitizer diagnostics in sanitized mode
- postprocessing for footnote backrefs and component wrappers

### The Document Dialect and Trust Modes

Two independent axes govern what a rendered document can contain.
They are related but must not be conflated:

1. **The dialect (a feature axis): what input has *significance*.** The language going
   into kpress is Markdown blended with a known set of tags and syntaxes.
   Which tags/syntaxes carry meaning is *configuration*: the Markdown flavor itself
   (GFM), math, diagrams, widgets, and the pass-through tag whitelist (`<span>`/`<div>`
   always, plus host-activated `format.html.extra_tags`). Enabling a feature is a
   *behavioral* change, and a real content feature is a bundle that must be enabled at
   every layer at once: any Markdown-to-Markdown preprocessing that desugars a surface
   syntax into its tags (see
   [Plugins and the Document Dialect](#plugins-and-the-document-dialect)), admission of
   those tags through the sanitizer (`extra_tags`), and the CSS/JS that styles or
   activates them in the page.
   A tag that is not enabled has no significance anywhere: no preprocessing produces it,
   the sanitizer does not admit it, and no front-end code looks for it.
2. **The trust mode (a security axis): what happens to input *outside* the dialect.**
   Raw HTML the author typed that is not part of the enabled dialect is either passed
   through untouched (the author is trusted) or reduced to inert output (the author is
   not). This axis never adds behavior; it only decides the fate of unrecognized or
   dangerous input.

Every render carries a trust mode (`DocumentInput.trust_mode`), which answers one
question: **do we trust the person who wrote this Markdown?**

- **`trusted`** — *the author is the site/tool owner.* No sanitization; raw HTML
  (including `<script>` and `style`) passes through untouched.
  For rendering your own local files in your own tooling, where HTML in the document is
  a feature, not a threat.
  This is the `DocumentInput` default, used by the local format/preview workflows.
- **`sanitized`** — *the author may be anyone.* One nh3 profile applies: a broad,
  XSS-inert allow-set (standard formatting tags, tables, images, safe SVG/MathML) plus
  the pass-through whitelist.
  Everything else is stripped — the tag is removed, its text content is kept — and a
  `html_sanitized` diagnostic is emitted.
  This is what the dynamic render API (`kpress.runtime.render_view`, the entry point
  hosts call to render a document fragment into their own page at request time), static
  site builds (`build_site`, the `kpress.yml`-driven publisher), and single-document
  exports (`export_document`) all use.

This two-policy shape matches the rest of the ecosystem.
Static site builders rendering the site owner’s own content default to trust or a single
safe/unsafe toggle (Jekyll and Eleventy pass raw HTML through; Hugo’s
`markup.goldmark.renderer.unsafe = false` replaces raw HTML with a
`<!-- raw HTML omitted -->` comment; cmark is safe by default with `--unsafe` to opt
out). Platforms rendering *other people’s* content (GitHub’s Markdown pipeline,
Discourse) render HTML and then apply exactly one allowlist sanitizer that strips
everything else. No mainstream tool distinguishes “embedded” from “published” at the
sanitizer level, and kpress does not either: the same inert profile serves both
destinations.

**Why sanitization works on the whole document.** Rendering is a two-stage pipe:
markdown-it renders the Markdown source into one HTML string, then nh3 sanitizes that
string as the single authority on what survives.
The rendered string mixes two kinds of HTML — tags *generated from Markdown syntax*
(`# Title` → `<h1>`, `*em*` → `<em>`) and *raw HTML the author typed* into the document,
which markdown-it passes through.
By the time nh3 runs, the two are indistinguishable, so the trust mode is a policy over
the whole document, not just over the raw-HTML islands.
This is deliberate: one sanitizer over the final output is far harder to bypass than
pre-escaping heuristics applied to the source, and it means the sanitizer also covers
HTML produced by kpress’s own pipeline (math, diagrams, component wrappers).
It also constrains the `sanitized` allow-set from below: the profile must admit
everything the Markdown renderer itself emits, which is why the allow-set is broad and
the *dialect*, not the sanitizer, is the primary lever for shaping content.

**Threat model.** A hostile document author, absent sanitization, could use raw HTML to
attack the *reader* or the *host page* embedding the render: script execution
(`<script>`, `on*` event handlers, `javascript:` URLs — XSS and session theft), style
injection (`style` attributes for overlay/clickjacking or data exfiltration via CSS),
resource loading and navigation (`<iframe>`, `<embed>`, `<form>`, media elements
pointing at attacker servers), DOM clobbering (content-authored `id`s shadowing elements
the page’s scripts look up), and parser-context confusion (`<template>`, `<xmp>`,
`<base>`, `<meta>`). The `sanitized` mode strips all of these unconditionally —
including on whitelisted pass-through tags; tags admitted only via the whitelist carry
`class`/`data-*` plus any host-declared `extra_attributes` (validated inert names —
never `on*`, `style`, URL-bearing, or DOM-identity attributes) and nothing else.
Safe URL schemes are `http`/`https`/`mailto`/`tel`.

Choosing a mode is mechanical:

| Content author | Examples | Mode |
| --- | --- | --- |
| Yourself (local files, own repo) | Local preview, format workflows | `trusted` |
| Anyone else (users, third parties, LLMs) | Host-app embeds, published sites, exports | `sanitized` |

When in doubt, use `sanitized`: the profile is already inert, and a false-positive strip
is a rendering blemish, while a false-negative pass-through is an XSS.

Source rendering target capability:

- language metadata
- optional syntax highlighting
- copy controls on screen
- print wrapping
- large-file fallback/truncation warning when relevant

## HTML Contract

KPress emits semantic HTML and namespaced classes.
Host chrome must not appear in KPress fragments or pages.

The current public contract is encoded in `kpress.contract` and tested by
`tests/test_public_contract.py`. This is a new package and evolves by **hard cuts**:
keep the contract direct and current: no deprecation shims, no backward-compatibility
layers, no aliases kept around for old callers.
A breaking change is acceptable when an out-of-date caller fails loudly with a clear
error message; what is never acceptable is silent fallback or silently different
behavior. Changing public names means changing `kpress.contract`, docs, tests, and
accepted goldens in the same patch; the release/PR notes are the migration guide.

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

All KPress HTML is authored in the packaged Jinja templates under
`src/kpress/format/templates` and rendered through the single strict environment in
`format/templating.py` (`StrictUndefined` + autoescape; a missing variable is an
immediate hard failure, markup rides `| safe`). HTML is never assembled with Python
f-strings or string concatenation (see AGENTS.md → Conventions).
Each template’s public variables are listed in
`kpress.contract.PUBLIC_TEMPLATE_VARIABLES`; the tests assert both that each declared
variable exists in the template **and** that the template is actually rendered by the
code, so the templates and the renderer cannot diverge.

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
  downstream enrichment: `data-col` (the column slug derived from the header row) and
  `data-kpress-numeric`. This is the renderer-agnostic seam a downstream decorator (a
  host app’s table plugin, a future static-site builder) consumes to select a column by
  name or detect numeric columns.
  kpress emits them and never consumes them; it never imports a decorator and never
  knows any table plugin exists.
- `PUBLIC_PASS_THROUGH_TAGS` / `PUBLIC_PASS_THROUGH_ATTRIBUTES` /
  `PUBLIC_PASS_THROUGH_ATTRIBUTE_PREFIXES`: the whitelisted-HTML input contract.
  The language going into kpress is **Markdown blended with a known set of pass-through
  HTML tags.** `<span>`/`<div>` are always allowed (matching GitHub / CommonMark
  renderers); a host activates more through `format.html.extra_tags` (the
  `RenderOptions.extra_tags` equivalent), which is unioned with the defaults per render.
  Whitelisted tags reach the output untouched under the `sanitized` trust mode and
  trivially under `trusted`. Tags admitted *only* via the whitelist (custom
  `extra_tags`) carry `class`/`data-*` plus any host-declared
  `format.html.extra_attributes` (inert semantic names like `kind`/`term`, validated
  against a forbidden set — never `on*`, `style`, URL-bearing, or DOM-identity names)
  and nothing else; `<span>`/`<div>` are also part of the standard allow-set, so they
  additionally keep its standard global attributes (e.g. `id` for author anchors).
  Declared extra attributes ride only on whitelist-only tags; standard HTML keeps its
  fixed policy. `style`, `on*` handlers, and unsafe-URL attributes stay sanitized on
  every tag. This is a styleable pass-through, never “turn sanitization off”.
  A document with no whitelisted tags renders exactly as before.

There is no `BuildMode` type.
The former `publish.mode` / `BuildReport.mode` / manifest `"mode"` key have been
removed; the independent axes (`asset_mode`, `strict`, `optimizer`, `precompress`)
replaced them.

### Page model block and widget mounts

Two further pieces of the page HTML are contract (see
[Extension and Injection Model](#extension-and-injection-model)):

- **The page model block.** `render_page` emits
  `<script type="application/json" id="kpress-page-model">…</script>` alongside the
  existing `#kpress-diagnostics` block, with the same JSON-escaping discipline (`<`,
  `>`, `&` unicode-escaped so the payload cannot break out of the `<script>` element;
  keys sorted). Its keys are pinned by `contract.py::PUBLIC_PAGE_MODEL_KEYS`: `version`,
  `title`, `route`, `profile`, `headings`, `widgets` (the enabled widget map with each
  widget’s opaque config passed through verbatim).
  `headings` carries the **TOC entries, post-processing included**: a lone leading H1 is
  stripped and levels are renormalized to contiguous ranks, not raw document heading
  levels. This is the published data client widgets compute from: a minimap reads
  `headings`; the settings widget reads its own `widgets.settings` config.
  Keys are added as widgets need them; each addition is a contract change.
  The *fragment* path does not emit the block; embedding hosts get the same data in the
  `render_view` payload and may mount widgets anywhere.
- **Widget mounts.** For each enabled chrome widget the page emits only a positioned,
  empty mount element,
  `<div class="kpress-widget kpress-no-print" data-kpress-widget="<id>">`, inside the
  viewport (so document tokens resolve), pinned by the floating-UI rules
  (`position: fixed` against `.kpress-frame`). The widget client-renders into its mount
  (no-JS rule: interactive-only chrome does not render without JS). Mount position is
  CSS via the per-widget inset tokens (`--kpress-<widget>-inset-*`); the `settings`
  mount keeps the `kpress-settings` class/id so its existing styles and inset tokens
  apply unchanged.

## Design System

KPress is the lower, reusable design layer and the **single source of truth for its own
design system**. The guiding rule: design rules live **close to the code, in CSS
wherever possible**: each token and surface rule is documented as a comment next to its
declaration, so KPress’s design can be maintained on its own, cleanly, without chasing a
separate spec. This doc is the *map and rationale*; it does not duplicate the detailed
per-surface rules that live in the CSS.

Two sources of truth:

- **Tokens:** `format/static/css/style-tokens.css`. The `--kpress-*` token tree:
  typography (families/sizes/weights/caps), color and a shared `--kpress-doc-surface-bg`
  family, the corner-radius scale (`--kpress-radius-*`), spacing/measure, motion
  (`--kpress-ease` + `--kpress-transition-*`), and scrollbar colors.
  Each group carries its design rule inline as a CSS comment (e.g. “rounded-vs-square is
  a deliberate per-surface choice”; “one easing; fast for hovers, slow fade for
  overlays”). The public subset is pinned by `contract.py::PUBLIC_CSS_VARIABLES`. Core
  doc tokens read `var(--kpress-host-*, <default>)` so an embedding host app can theme
  them; the rest are overridable by static-site generators and standalone pages.
- **Icons:** `format/static/icons/icons.svg` (and the contract doc `kpress-icons.md`).
  The one place KPress SVGs live: a real SVG sprite, the Lucide v1.17.0 (ISC) set as
  `<symbol>` elements on the stroke grid (`currentColor`, size-from-CSS), the single
  source of truth for chrome glyphs.
  The server inlines the hidden sprite once per document and both the server chrome
  (`render.py::_icon`) and the client JS (`static/js/icons.js::icon`) draw a glyph with
  `<svg><use href="#kpress-icon-<name>"></svg>`, so no SVG geometry is authored in
  Python or JS. The contract is enforced by `tests/test_icons.py`.

**Relationship to the host app.** An embedding host app keeps the design that is
genuinely app-chrome-specific (e.g. a tree pane, tabs, shell, and its own app token
tree) but **leans on KPress for the shared, document-level design**, the same Lucide
icon family and the `--kpress-*` / `data-kpress-*` contract, rather than re-implementing
it. KPress owns and maintains the shared design layer; the three consumers (standalone
page, static-site build, host-app embed) inherit it.
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
  --kpress-doc-code-bg: oklch(97.93% 0.0029 84.6);
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

Widget and menu classes are part of this contract for a specific reason: they are the
**restyle-with-same-structure seam**. A host that wants the settings menu (or any
widget) to look different but keep its structure overrides `.kpress-widget`,
`.kpress-settings*`, `.kpress-menu`, `.kpress-menu-chooser`, `.kpress-menu-seg`, no JS
required. Positioning:

- The settings gear is positioned through the host-override pair
  `--kpress-host-settings-inset-block` / `--kpress-host-settings-inset-inline`, so
  moving it is a CSS override, never a markup change.
  (These consumed-not-declared host hooks are pinned in
  `contract.py::PUBLIC_HOST_CSS_VARIABLES`.)
- Custom widgets ship no KPress positioning: the server emits an in-flow mount with
  stable hooks (`#kpress-<id>`, `.kpress-<id>`, `.kpress-widget`), and the host’s own
  CSS positions it. Ship that CSS the same way as the widget’s JS (see Host Integration).

### Design tokens and shared primitives

Internal design tokens live once in `style-tokens.css` so shape and motion are tuned in
one place rather than per component.
Stylesheets reference these instead of hardcoding values (the lint floor and code review
enforce “always use CSS vars”).

- **Corner radius:** `--kpress-radius-none | -sm | -md | -lg | -pill`. One scale;
  rounded-vs-square is a deliberate per-surface choice.
  Code blocks and tables both use `--kpress-radius-none` so the two read as one family;
  the gear menu / popovers use `-sm`, footnote markers use `-pill`.
- **Motion:** `--kpress-ease` plus `--kpress-transition-fast | -med | -slow | -fade`.
  `-fast` is the default for hovers and size/shape changes; `-fade` is for overlay
  opacity/visibility. The `prefers-reduced-motion` block suppresses them.
- **Surface fill:** `--kpress-doc-surface-bg` is the single subtle fill shared by code
  blocks, table headers, and (where applicable) metadata/shaded surfaces.
  `--kpress-doc-surface-hover` and `--kpress-doc-surface-selected` extend the family for
  interaction highlights (TOC hover/active, hovered controls), deepening with
  interaction strength.
  All three are **host-overridable**: they read
  `var(--kpress-host-surface-*, <neutral default>)`, so a host (or a palette preset) can
  retarget the highlights, not just the code background.
  The neutral default is a subtle link tint, re-derived per light/dark theme.
  All first-party color literals are written as `oklch()` (exact, round-trip-verified
  conversions; see `devtools/css_to_oklch.py`).
- **Palette presets:** reasonable default sets for common cases, each a *named bundle of
  the `--kpress-host-*` contract* (not special-cased code), keyed on
  `.kpress[data-kpress-palette="<name>"]` and selected via `RenderOptions.palette` /
  `format.palette`. `neutral` is the default (no overrides); `warm` is *systematic with
  neutral*: every token keeps neutral’s lightness and near-identical chroma, and only a
  few are tastefully warm instead of neutral gray: ink/muted/border and the surface
  fills rotate to a warm greige/tan hue, the link keeps the warm preset’s own teal, and
  the hover/selected interaction tints are deliberately a step lighter than the plain
  rotation: gentle, quiet tan highlights.
  Everything else (page bg, success, selection strength) inherits neutral unchanged.
  A host can select a preset and still override any single var on top: *simple stays
  simple, complex stays possible.*
- **Content card:** the reading column rendered as a bordered sheet floating over the
  page, on `.kpress-long-text` (whose 48rem cap and `md` 4rem inline padding already are
  the card’s geometry; the card adds chrome only, no layout properties, so the coupled
  TOC/table width system is untouched).
  Chrome is `--kpress-card-border` + `--kpress-card-shadow` (dark themes deepen the
  shadow), appears only at md+ widths (narrow screens read full-bleed), and never
  prints. Shown or flat is a render-time setting: `RenderOptions.content_card` /
  `format.content_card`, stamped as `data-kpress-card="on|off"` on the document article,
  and **either default is supported**: the shipped default is **on** (for now; flip the
  option for the flat full-bleed page).
  Embedding hosts stamp the same attribute on the fragment wrapper themselves.

Two shared interaction primitives are documented so every component reuses them rather
than re-styling:

- **Disclosure toggle:** every `<details>`/summary uses the Lucide `chevron-right` glyph
  (drawn via a CSS mask so it inherits the summary color), rotated 90° when `[open]` on
  the motion token, with a single-color summary.
  No native disclosure triangle.
  Expansion animates via `interpolate-size: allow-keywords` + a `::details-content`
  transition where supported (older browsers open instantly).
- **Icon-only affordances:** action controls (code copy, video close) render an icon
  only, with the label in `aria-label`/`title`, and the copy control is revealed on
  hover/focus of the code block.
  Glyphs come from the shared Lucide set (see `kpress-icons.md`).

These primitives and tokens live in the KPress static layer deliberately: an embedding
host app consumes the same design (sharing the Lucide icon set) rather than
re-implementing it.

## Theme and Fonts

Theme mode values:

- `system`
- `light`
- `dark`

Standalone pages include a pre-paint bootstrap that resolves `system` using
`prefers-color-scheme`. Dynamic fragments let hosts resolve and set attributes.

**Theme engine vs. settings widget.** These are two layers, deliberately separate (see
[Extension and Injection Model](#extension-and-injection-model)):

- **The theme engine is a headless client primitive:** `kpress.theme` (today’s
  `setKpressTheme` / `initKpressTheme` in `theme.js`, promoted to a stable API): resolve
  `system` via `prefers-color-scheme`, set `data-kpress-theme` /
  `data-kpress-resolved-theme`, persist through `kpress.storage` (key `kpress.theme`),
  notify change listeners, and track OS theme changes.
  Engine *init* runs as the registered `theme` behavior at apply time: its first storage
  read goes through whatever adapter the host installed before `DOMContentLoaded`, and a
  host that owns theme resolution overrides the behavior rather than fighting it.
  The pre-paint bootstrap (`theme-bootstrap.js`, inlined render-blocking in `<head>`)
  applies persisted state attrs before first paint (theme, and the same pattern for the
  other persisted reader preferences (`kpress.proseFont` → `data-kpress-prose-font`,
  `kpress.fontSet` → `data-kpress-font-set`), so there is no flash regardless of which
  widget (if any) presents the controls.
- **The settings menu is a built-in chrome widget** (registry id `settings`): the
  default *presentation* over those engines: a gear button opening a menu
  (`.kpress-menu`) of segmented icon choosers (`.kpress-menu-seg`), client-rendered into
  its server-emitted mount (no-JS rule: the menu can do nothing without JS, so it does
  not render without JS). It composes the `kpress.menu` primitive (open/close,
  outside-click and Escape dismiss, `aria-checked` marking) and defines its chooser
  catalog *in its own JS* (schema-with-the-code): `theme` (system | light | dark),
  `reading-font` (serif | sans prose, via `data-kpress-prose-font` →
  `--kpress-font-prose: var(--kpress-host-font-prose-sans, var(--kpress-font-sans))`),
  and `font-set` (custom | system faces, via the existing `data-kpress-fonts` switch).
  Config selects and orders the choosers:
  `widgets: {settings: {choosers: [theme, reading-font]}}`, default `[theme]`; unknown
  chooser ids warn and are skipped.
  A host that wants a different presentation (a bare dark/light toggle, its own menu)
  turns the widget off and writes a few lines over `kpress.theme`. The engine is the
  contract, the gear only its default face.

The widget’s mount is emitted **inside** `.kpress-viewport` so it inherits the document
tokens (rather than living outside `.kpress` where tokens would not resolve); its
`position: fixed` pins to the enclosing non-scrolling `.kpress-frame`. The viewport
itself must never be a fixed containing block, or the gear (and all floating UI) would
scroll away with the content.

The gear’s two host seams stay orthogonal:

- **Whether:** presence via the widget map (`format.widgets: {settings: off}` /
  `RenderOptions(widgets=...)`). Off emits no mount at all.
  The gear is the only built-in theme control, so turning it off in a standalone page
  leaves the reader on the server-resolved theme with no switcher; pair it with your own
  control if you still want one.
- **Where:** position (CSS vars).
  The mount’s insets resolve through host hooks:
  `inset-block-start: var(--kpress-settings-inset-block)` and
  `inset-inline-end: var(--kpress-settings-inset-inline)`, each defaulting to
  `var(--kpress-host-settings-inset-<block|inline>, 0.75rem)`. Set
  `--kpress-host-settings-inset-block` / `--kpress-host-settings-inset-inline` on
  `:root` to move it (the `--kpress-host-*` hooks are not redeclared on the token scope,
  so a `:root` value flows through instead of being shadowed, the same pattern as the
  color hooks). The mount is a child of the `@container kpress-doc` viewport, so a host
  can also size the inset per layout band with a container query.
  Example: align the gear to the right edge of the header underline (the content column)
  instead of flush to the window:
  `--kpress-host-settings-inset-inline: max(3rem, calc(50vw - 24rem))` for the centered
  bands, where `24rem` is half the `--kpress-measure` reading width and `3rem` is the
  page + document gutter floor for narrow widths.
  (Use the literal half-measure rather than `var(--kpress-measure)` when setting this on
  `:root`: `--kpress-measure` lives on the document scope, not `:root`, so a `var()`
  reference there resolves to nothing and voids the inset.)

The standalone scroller `.kpress-page-main` carries the document `background`/`color`
and the document tokens, so the whole window is themed.

**Single scroll context.** `.kpress-page-main` is a `100dvh`, `overflow-y: auto` pane,
the one element the document scrolls inside.
So the page is not *also* scrolled by the window (which would show a second, nested
scrollbar), the page shell emits a standalone-only reset:
`html, body { margin: 0; height: 100%; overflow: hidden }`, making `.kpress-page-main`
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
not loaded in the host; see [Host Integration](#host-integration)). The
`system | light | dark` attribute contract is the shared seam; the gear chrome itself is
per-layer.

Font mode (`RenderOptions.font_mode`, type `FontMode = Literal["custom", "system"]`):

- `custom` (default): themed custom font stacks (PT Serif, Source Sans 3, mono,
  punctuation fallback) via CSS variables.
- `system`: `.kpress[data-kpress-fonts="system"]` overrides font variables to system-ui
  stacks with no custom font loading.

Font roles. Each role is a CSS variable that resolves through a host hook to a vendored
default, `var(--kpress-host-font-<role>, <vendored stack>)`, so an embedding host can
override any single role on its own, and otherwise the vendored reader faces apply:

| Variable | Default (vendored) | Used by | Host hook |
| --- | --- | --- | --- |
| `--kpress-font-prose` | serif: PT Serif (`LocalPunct` punctuation) | reading body (`.kpress-prose`), H1/H2 | `--kpress-host-font-prose` |
| `--kpress-font-sans` | sans: Source Sans 3 | UI chrome: TOC, captions, H3–H6, code-copy, **tooltips** | `--kpress-host-font-sans` |
| `--kpress-font-footnote` | sans (via `--kpress-font-sans`) | footnote previews and the bottom footnotes section | `--kpress-host-font-footnote` |
| `--kpress-font-table` | sans (via `--kpress-font-sans`) | data tables | `--kpress-host-font-table` |
| `--kpress-font-body` | sans: Source Sans 3 | `.kpress` wrapper base (a fallback; `.kpress-prose` overrides it for content) | `--kpress-host-font-body` |
| `--kpress-font-mono` | mono: system mono stack | code blocks | `--kpress-host-font-mono` |

The reading body is therefore serif by default and is settable serif↔sans per role: a
host flips it by setting `--kpress-host-font-prose` (a host app’s serif/sans
reading-font toggle does exactly this), and `font_mode="system"` swaps every vendored
face for the platform stack.
Footnotes and tables each carry their own stack (`--kpress-font-footnote`,
`--kpress-font-table`) so they can be retargeted independently; both default to the UI
**sans**. The bottom footnotes section uses the same `--kpress-font-footnote` as the
footnote preview tooltips, so the two always agree.

Static sealing must be able to copy or download font assets so output does not rely on a
CDN unless configured.

## Document Components

Interactive page parts come in three kinds (see
[Extension and Injection Model](#extension-and-injection-model)); naming the kind first
keeps each new feature on the right seam:

- **Document components:** server-rendered markup, meaningful without JS: prose, tables,
  tabs panels, footnotes, the TOC markup and links, code blocks.
  These are the components listed below.
- **Behaviors:** JS bindings over that markup, each a registered, overridable id: `toc`
  (scroll-spy / drawer / toggle), `tooltip`, `footnote-preview`, `code-copy`, `video`,
  `tables`, `tabs`, `diagrams`, and `theme` (engine init over the root element).
  The markup is the binding surface; a host can rebind an id over the same markup, or
  register a new behavior over its own injected HTML.
- **Chrome widgets:** client-rendered, JS-only chrome (`settings`; host-defined ids like
  a minimap), rendering into server-emitted mounts.

Presence is controlled per kind: `format.widgets: {<id>: on/off/auto}` governs chrome
widgets (which mounts the server emits); document components keep their own format
switches (`format.toc`, `format.math`, …), which control the markup itself; behaviors
have no Python presence map: they bind wherever their markup exists, and a host disables
or replaces one in JS (`behaviors.override(id, …)` before apply).
Built-in behaviors and widgets are **assembled from exported ES-module parts** (the TOC
behavior’s visibility policy and threshold, the tooltip placement and delay logic), so a
host can wrap or replace one aspect without owning the whole, and they are registered
through the same public registries a host uses (the dogfood rule).

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
2. **Init function shape + registration.** Each component exports a single
   `initKpress<Name>(root = document)` entry point.
   It is idempotent: re-running it on the same root must not double-bind handlers or
   duplicate injected controls (guard with a `data-kpress-*-ready` marker or an
   existing-node check).
   A component never runs DOM work at import time; at import it only **registers**:
   `kpress.behaviors.register(id, {bind: initKpress<Name>})` (or
   `kpress.widgets.register` for chrome widgets), and the runtime applies all registered
   binds once on `DOMContentLoaded`, then emits `kpress:ready`. Host overrides
   registered before apply replace the built-in; after apply, `rebind(id)` re-runs one
   binding. Long-lived side effects (MutationObservers, document-level listeners, OS
   media listeners) are installed inside `bind`, never at import, and `bind` returns a
   disposer that tears them down; the runtime disposes the old binding before
   `override`/`rebind` applies a new one, so replacing a behavior really retires it.
   (This registration step is what makes every built-in overridable; the older pattern
   of calling `initKpress<Name>()` directly at module bottom is retired by the runtime
   migration.)
3. **Exported parts.** The aspects of a component a host plausibly wants to change one
   at a time (an icon renderer, a visibility or placement policy, a threshold) are real
   ES-module `export`s (and/or config keys with callback values), not module-private
   closures. Exports pinned in `contract.py::PUBLIC_JS_EXPORTS` are stability contracts;
   start narrow and grow on demand.
4. **DOM and class conventions.** Behavior is wired through `data-kpress-*` attributes.
   Every component-owned class is namespaced `kpress-*`. Bare or legacy un-namespaced
   classes (for example `visible`, `open`, `toc-open`) are not allowed; shared state
   classes are `kpress-visible`, `kpress-overlay-open`, `kpress-mobile-visible`, and
   `kpress-toc-open`. New public classes are added to `contract.py::PUBLIC_CSS_CLASSES`
   and styled in `static/css/` in the same change.
5. **Shared overlay primitive.** Any component that positions a floating surface
   (tooltips, video popover, TOC drawer, future popovers) must use
   `static/js/overlay.js`: `computePosition` for viewport-aware placement,
   `dismissOnEscape` / `dismissOnResize` / `dismissOnOutsideClick` for teardown, and
   `toggleBackdrop` for backdrop plus `aria-hidden` state.
   Per-component positioning or dismiss logic must not be reintroduced.
   `overlay.js` records the explicit Floating-UI reconsider tripwire: adopt Floating UI
   only if the overlay system needs multi-axis collision detection with simultaneous
   flip and shift, or virtual-element anchoring for non-DOM triggers; until then a JS
   runtime dependency is not justified.
6. **Accessibility baseline.** Interactive components set correct ARIA roles, manage
   focus (trap and restore for modal surfaces), support keyboard operation and Escape
   close, and respect `prefers-reduced-motion`.
7. **Testing contract.** Each component ships a browserless happy-dom DOM test under
   `tests/js/`, is represented in an accepted golden, and passes the package gate (Biome
   2 including `style/useBlockStatements`, `tsc --checkJs`, Vitest).
   Real-browser visual and interaction acceptance is recorded through
   `docs/kpress-validation.runbook.md`, not asserted in CI.

## Extension and Injection Model

This is the single section to read to understand “how do I customize KPress.”
It defines the injection surfaces (five layers, each a simple entry point that can be
used, overridden, enhanced, and re-injected) plus the decision rules for where any
future customization lands.
The placement rules themselves (no-JS, schema-with-the-code, dogfood) are Core Principle
5\.

Guardrail: nothing here is a plugin framework, hook lifecycle, or DI container.
The whole model is three concrete shapes: **published data** (the page model, state
attrs, and tokens), a **registry** (a dict you add to: JS at runtime, or the widget
presence map in Python at build time), and an **ordered list of stages** (the build
pipeline). A proposed seam that is not one of those shapes does not belong.

### The JS / Python boundary

> Customization is front-end code; Python orchestrates and injects it; whole-artifact
> build-time processing is a Python plugin.

| Concern | Lives in | Why |
| --- | --- | --- |
| Widget behavior and markup, new interactive widgets, replacing TOC logic, rebinding tooltip/footnote hover, per-reader state, restyling | JavaScript / CSS (layers A–C) | Interactive, runs in the browser, per-reader; standard front-end code |
| Which widgets ship, opaque widget config, injecting host JS/CSS, assembling the page, driving the build | Python (layer D) | Build/host wiring; transports data and snippets; implements no widget logic |
| Minify/compress, document-tree transforms, HTML post-processing, asset packaging | Python plugin (layer E) | Needs the whole artifact, runs once at build, no browser: a proper build step |

Litmus: *needs a browser or runs per reader?* → front-end (Python only injects it).
*Transforms the whole artifact once at build?* → Python pipeline plugin.

### Layer A: page model and state contract (published data)

The server emits everything a widget needs to compute itself:

- **`#kpress-page-model`:** a JSON script block (same emission and escaping pattern as
  `#kpress-diagnostics`): `version`, `title`, `route`, `profile`, `headings`, and the
  enabled `widgets` with their (opaque) config.
  This replaces any temptation toward “Python callbacks computing chrome from a render
  context”: KPress publishes the context; JS computes whatever it wants.
- **State attrs:** the `data-kpress-*` family (`-theme`, `-resolved-theme`,
  `-prose-font`, `-font-set`, `-fonts`, …): the shared seam widgets write and CSS keys
  off. The pre-paint bootstrap applies persisted values before first paint.
- **Tokens:** the CSS-var contract (see [CSS Contract](#css-contract)), including
  per-widget position tokens (`--kpress-<widget>-inset-*`).

### Layer B: client primitives (built-in headless engines)

The genuinely complex machinery ships built-in, headless, and reusable, separate from
any presentation:

- `kpress.theme`: resolve system preference, set/persist mode, pre-paint, change
  listeners (today’s `setKpressTheme` / `initKpressTheme`, promoted to a stable API).
- `kpress.storage`: persistence with a pluggable adapter (`{get, set}`; localStorage
  default; an embedding host can supply cookies for cross-port sharing).
- `kpress.menu`: popover behavior: open/close, outside-click/Escape dismiss,
  `aria-checked` segment marking.

A host that wants a bare dark/light toggle writes a few lines over `kpress.theme`; the
gear menu is only the default presentation of that engine.

### Layer C: widget and behavior registries (named, optional, replaceable)

Two kinds of registrable things, one registry family, both plain DOM/JS over layers A+B,
no framework:

- **Widgets:** client-rendered *chrome* with a mount point (`settings`, a host’s
  `minimap`). For enabled widgets the server emits only a positioned mount element
  (`<div data-kpress-widget="<id>">`); the widget renders into it (no-JS rule).
  Position stays CSS (the inset tokens).
- **Behaviors:** JS bindings over *server-rendered document markup*: `toc`, `tooltip`,
  `footnote-preview`, `code-copy`, `video`, `tables`, `tabs`, `diagrams` (plus `theme`,
  which binds the theme engine’s init to the root element).
  The HTML contract is the binding surface; KPress’s defaults bind to it, a host can
  rebind the same markup, and HTML injected by the host (slots, markdown, build
  transforms) becomes interactive the same way.

```js
kpress.widgets.register("minimap", { mount(el, config, model) { /* … */ } });
kpress.widgets.configure("settings", { choosers: ["theme", "reading-font"] });
kpress.widgets.mount("settings", hostElement); // embeds: mount anywhere

kpress.behaviors.override("footnote-preview", myHoverBinding);
kpress.behaviors.register("glossary", { bind: bindGloss });
```

Built-ins go through the same registries (dogfood rule) and are **assembled from
exported ES-module parts**: KPress JS already ships as ES modules behind an import map,
so the sub-portions are real exports (the TOC behavior’s visibility policy, the tooltip
placement logic).
A host imports a part, wraps or replaces it, and re-registers, changing
one aspect without owning the whole thing.

Config travels on **two channels**: declarative JSON through YAML/Python
(transportable), and JS-level config, a superset that may include callbacks / policy
functions (`kpress.behaviors.configure("toc", { visible: () => true })`). Common aspects
may earn declarative spellings; the callback seam means KPress never has to
pre-enumerate every aspect as a binary setting.
Each widget/behavior defines and validates its config in its own JS
(schema-with-the-code rule).

### Layer D: Python orchestration (what ships; no widget semantics)

```yaml
format:
  widgets:            # chrome-widget presence + opaque config
    settings: { choosers: [theme, reading-font] }
    minimap: on       # unknown ids are allowed: hosts register their own
```

`RenderOptions(widgets={...})` mirrors the YAML. Python serializes this verbatim into
the page model and emits mount elements for enabled widgets.
That is its entire involvement with chrome.
The map governs **chrome widgets only**: behaviors bind wherever their markup exists
(disable or replace one in JS via `behaviors.override(id, …)` before apply), and
server-rendered document components keep their own format switches (`format.toc`,
`format.math`, …), which control the markup itself.

### Layer E: build pipeline plugins (Python; the build-step exception)

```python
build_site(config, extensions=BuildExtensions(
    pipeline=[my_js_preprocessor, "kpress:full"],   # pre-stage before the built-in compressor
    transform_tree=add_section_anchors,             # document-tree transform
    transform_page_html=stamp_build_info,           # final-HTML transform
))
```

Stages share the optimizer backend shape (`name` + `optimize(content, *, kind)`),
resolved by name (`kpress:none`, `kpress:full`) or passed as objects, and run in list
order. See [Optimizer and Precompression](#optimizer-and-precompression).

### The tiers (simple → complex, purpose-agnostic)

| You want to… | Mechanism | Layer |
| --- | --- | --- |
| Turn a chrome widget on/off | `widgets: {<id>: on/off/auto}` | D |
| Turn a document component on/off | its format switch (`format.toc`, `format.math`, …) | D |
| Configure a built-in widget | opaque config JSON | D→C |
| Restyle, same structure | CSS contract (classes + tokens) | A |
| Move the settings gear | `--kpress-host-settings-inset-*` tokens | A |
| Position a custom widget | host CSS on its mount (`#kpress-<id>` / `.kpress-<id>`) | A |
| Tweak one aspect of a built-in (TOC icon, appear-after-scroll policy) | wrap/replace an exported part, or pass a callback via JS config | C |
| Change tooltip/footnote hover handling | `behaviors.override("footnote-preview", …)` over the same markup | C |
| Replace a widget or behavior wholesale | `widgets`/`behaviors.register(<id>, …)` | C |
| Add a new widget (minimap) | register + read the page model | C+A |
| Inject new HTML and make it interactive | slot/markdown/transform HTML + `behaviors.register` | E/D→C |
| Put a different face on a built-in engine | primitives (`kpress.theme`, …) | B |
| Add a build stage / transform | pipeline list | E |

Every row requires no KPress edit; the chrome slots and `--kpress-host-*` vars (the
existing simplest tier) are unchanged underneath all of this.

Name contracts pin the model the way `PUBLIC_CSS_VARIABLES` pins the tokens:
`PUBLIC_WIDGETS`, `PUBLIC_BEHAVIORS`, `PUBLIC_JS_EXPORTS` (the stability-pinned module
exports), `PUBLIC_PIPELINE_STAGES`, and `PUBLIC_PAGE_MODEL_KEYS` in `contract.py`.

## Plugins and the Document Dialect

KPress is a configurable tag-admission and styling mechanism (the
[HTML Contract](#html-contract)) plus a front-end extension model (the
[Extension and Injection Model](#extension-and-injection-model)). Together these are the
substrate for **plugins**, how a host adds content features without editing KPress.
KPress assigns no meaning to a plugin’s tags; it admits, styles, and binds them.
It documents *conventions*, not a closed HTML dialect.

### What a plugin is

A plugin is one or both of:

- **A preprocessing step:** a files-to-files Markdown→Markdown rewrite that desugars a
  surface syntax (emoji glyphs, shortcodes, IDs) into custom tags KPress admits.
  It is *syntax sugar*: readable authoring maps to custom HTML. The host runs it before
  KPress assembly; KPress then renders the result with every built-in feature
  (footnotes, math, code highlighting, TOC, postprocess enrichment) intact, including
  inside the custom-tag blocks.
- **A front-end plugin:** CSS and/or JS over those tags, delivered through the injection
  seams (the `head_extra_html` slot, static passthrough, and the behavior/widget
  registries). CSS targets the admitted tags; JS registers as a behavior or widget
  exactly as a built-in does (the dogfood rule).

A plugin may be both halves or just one: a pure preprocessor whose tags need only CSS,
or a pure front-end decorator over markup KPress already emits.

### The document model

A KPress document is a body fragment: Markdown blended with an admitted set of custom
HTML/XML tags, one mixed vocabulary in which the standard tags Markdown compiles to and
a plugin’s custom hyphenated tags ride through under the same sanitizer policy.
A block-level custom tag surrounded by blank lines opens an HTML block whose inner
content re-parses as Markdown (standard CommonMark behavior), so links, math, and
footnotes render inside it; an inline custom tag wraps inline content.
Title and metadata travel as frontmatter, never guessed from the body.
A plugin’s two halves are intended to meet through sidecar artifacts: the preprocessor
emits JSON the front-end reads through a namespaced `data` key on the page model.
That `data` key is **planned, not yet shipped**: `PUBLIC_PAGE_MODEL_KEYS` does not
include it today, so a front-end plugin that needs sidecar data must carry it through
its own injected markup or a separate fetch until the key lands.

### The plugin boundary: text and files, not an AST

The preprocessing contract is plain Markdown text and file paths.
KPress exposes no parser hook, token API, or language-bound callback at the
preprocessing layer: a plugin reads Markdown files and writes Markdown files, so it can
be written in any language and never breaks when KPress internals change.
This is the consistent lesson of the build-system ecosystem: bundlers and Markdown
frameworks that kept their native parse tree internal and contracted on strings and
paths stayed stable, while making a tree the contract (a versioned AST schema) forces a
host/plugin compatibility matrix and serialization cost.
KPress goes one step further and has no tree schema to version at all: its dialect is
restricted HTML plus JSON sidecars, which change only when HTML itself does.
The files boundary is practical here because KPress documents are coarse-grained (a
handful of large documents, not thousands of modules), so per-file subprocess cost is
negligible. That granularity is a caveat to record, not a universal claim.

A tree-shaped surface is appropriate only *inside* a preprocessor, using a
document-model library to find exact block boundaries, then splicing custom tags back
into the source at those offsets so the output is byte-identical except at the rewritten
blocks, and as the in-process `transform_tree` build convenience over the `DocumentTree`
dataclass. Both use a tree internally; neither is a cross-process or cross-language
contract, and `transform_tree`’s schema evolves with KPress releases.

### Conventions, not a closed dialect

KPress documents the conventions; the tag vocabularies are the plugins’ business.

- **Prefixes.** A plugin claims a short tag prefix (such as `x-…`) and declares its tags
  in the admission config; data payloads follow a matching `data-…` convention.
  The `k-*` tag prefix and the `kpress-*` class/data/id prefix are reserved for KPress’s
  own use by convention, so plugins do not squat them.
  This is a governance signal, not a hard-coded list.
- **Attributes.** Plugin tags carry clean inert attributes.
  A plugin declares its semantic attribute names (`kind`, `term`, …) through
  `format.html.extra_attributes` and they survive `sanitized` on whitelisted tags, so
  `<k-block kind="epigram">` is the idiomatic form; `class` stays available and `data-*`
  remains the open-ended escape hatch for arbitrary payload (no declaration needed).
  `id` and ARIA survive only under `trusted`; `on*`, `style`, and unsafe-URL attributes
  are always stripped.
- **No pinned vocabulary.** KPress does not freeze a closed dialect.
  Codifying one is deliberately deferred: pinning today’s tags would lock current shape
  into a contract before the design has settled.
  The conventions are the contract.

### Graduated complexity

Content extension follows the same simple-to-complex ladder as the
[Extension and Injection Model](#extension-and-injection-model), and like it requires no
KPress edit at any rung:

- **Nothing declared:** KPress is Markdown→HTML; the `div`/`span` floor is the only
  pass-through.
- **Declare tags:** one config line (`format.html.extra_tags`) admits custom tags, so an
  author can hand-write `<x-callout kind="warning">…</x-callout>` and style it with host
  CSS. No preprocessor needed.
- **Add a preprocessor:** a files-to-files step desugars a surface syntax into those
  tags; companion CSS/JS styles or binds them.
  Adding or renaming a feature is a ruleset and CSS edit.
- **Add behavior:** register a front-end behavior or widget over the tags through the
  client registries, exactly as a built-in does.

### Examples

Each illustrates the model: a surface syntax, the tags it desugars to, and the styling
or behavior over them:

- **Structural devices** (preprocessing and CSS). A leading glyph on a Markdown block
  gives it a meaning or format; a data ruleset maps glyph→kind.
  The preprocessor walks base blocks (paragraphs, list items, whole blockquotes), wraps
  a matched block in `<x-device kind="…">` (the tag and `kind` declared via
  `extra_tags`/`extra_attributes`), and splices it back at the block’s source span; host
  CSS styles each kind (callout, definition, alignment, hidden).
  Adding a device is a config edit, zero KPress changes.
- **Inline badges** (preprocessing and CSS). A shortcode such as `:new:` rewrites to an
  inline `<x-badge>`, the degenerate case of the same engine, CSS only.
- **Definitions and glossaries** (preprocessing and CSS, optional front-end).
  A glyph marks a definition block; the preprocessor wraps it and emits a term sidecar.
  Basic CSS styles the block; an optional behavior reads the sidecar (via the planned
  page-model `data` key, or its own injected markup until then) to add term tooltips
  elsewhere.
- **Table decorators** (front-end only).
  KPress emits neutral enrichment attributes on table cells; a client decorator consumes
  them to sort or chart, with no preprocessing and no KPress-specific code.
  KPress emits the hooks and never consumes them.

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
| **Static build dev** | `kpress build` | `linked` | n/a | `none` | none | `kpress build` | Stable; readable multi-file tree. Document-local and external asset URLs pass through verbatim; the deploy layer owns them. |
| **Static build prod** | `kpress build` | `hashed` | n/a | `full` | `gzip` (`br` with `kpress[optimize]`) | `kpress build` | Stable; content-hashed package assets, immutable cache, minified. Document-local and external asset URLs pass through verbatim. |
| **Static build sealed** | `kpress build` | `sealed` + `strict=true` | yes | `full` (typical) | optional | `kpress build` | **Deferred to v2.** See “Asset Model and Sealing: deferred for v1” below. |
| **Self-contained single file** | `kpress format` / `render` | `inline` + classic (non-module) reader JS + inline fonts + inline KaTeX | n/a | `full` (typical) | n/a | `kpress format`/`render` with `--asset-mode inline` (lever gap) | **Deferred.** See “Self-contained single file: deferred” below. |

For a “share one HTML file by link” workflow, prefer **Static build prod** deployed to a
CDN (or **Dynamic multifile (production embed)** with a CDN-hosted reader bundle) rather
than self-contained inline.
The artifact-size math (see deferred notes) makes inline a poor default for most
documents.

For air-gapped or offline-verified static publish, sealing is on the v2 roadmap; see
“Asset Model and Sealing: deferred for v1” below.
The deploy layer (CDN, S3, GitHub Pages, etc.)
is the right place to handle external-asset integrity, fetching, and hashing in v1.

Dynamic and static differ in *layer*, not in shaping intent.
Dynamic emits one HTML fragment and a JSON asset manifest per request; static emits a
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

- Reader fonts alone (PT Serif and Source Sans, 6 woff2) add ~250 KB after base64
  inflation.
- KaTeX as inline (when math is present) adds another ~700 KB (UMD JS, 20 woff2 fonts,
  and CSS).
- Document images push artifact size into MB territory quickly (1 MB photo → ~1.3 MB
  after base64; email clients clip at ~100 KB; multi-MB HTML noticeably slows browser
  parse).

For “share a rendered doc by link”, point at a CDN-hosted asset bundle instead and
publish via **Static build prod**. The current package-asset URL builder already accepts
an arbitrary prefix (`format/assets.py::package_asset_url`), so a host or build step can
point at a CDN with no new code.

To revisit if a real `file://`-only consumer appears, the work is small and
self-contained:

- **Tier 1 (~1 day):** bundle reader JS to classic.
  Reader modules are 11 files, ~1,930 LOC, with a shallow single-root import graph (3
  modules import from `overlay.js`; nothing else has imports).
  A topological concat and strip of `import`/`export` statements is ~30 lines of Python
  or one `npx esbuild` call (same pattern as `html-minifier-next`). Then plumb
  `--asset-mode` through `format`/`render` and switch inline JS emission from
  `<script type="module">` to classic `<script>`. This alone unblocks `file://` for
  documents with system-font fallback acceptable.
- **Tier 2 (~half day):** inline reader fonts.
  Rewrite `url(../fonts/foo.woff2)` in `style-tokens.css` to
  `url(data:font/woff2;base64,...)` (~20 lines).
- **Tier 3 (~half day):** inline KaTeX when math is detected.
  Same data-URI rewrite for the 20 KaTeX woff2 fonts plus literal-inline the KaTeX UMD
  JS (already classic).
- **Tier 4 (deferred-within-deferred):** document images.
  The asset-sealing infrastructure in `publish/seal.py` already handles size caps,
  integrity, MIME validation, and HTML/CSS rewriting.
  Extending it to base64-inline local images is ~50 lines plus a
  `--max-inline-image-bytes` policy.
  External-image fetching would reuse the existing sealed-asset path.
  Skip video; emit poster and link.

Surface as one composable lever (`reader_js=module|classic`, kept independent of
`asset_mode`) plus a `--single-file` convenience flag that maps to
`asset_mode=inline, reader_js=classic, font_inline=true`. Don’t introduce a 6th opaque
`asset_mode` value, as that breaks the no-coarse-modes stance.

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
  Revisit if/when one does; the work would be ~1-2 days of build and manifest changes if
  accepted.

In the meantime, embedding hosts should treat the served `/kpress-static/<v>/...` tree
as a stable source they can optimize at their own deployment layer.

## Asset Model

KPress sees four kinds of assets:

- **Package assets:** CSS/JS/fonts vendored inside the wheel (`format/static/`). Copied
  into the publish output tree (or served dynamically) by KPress itself.
- **Document-local assets:** files the document references via relative paths
  (`./image.png`, `./styles.css`). In v1, KPress does **not** copy or rewrite these: the
  URL is left in the rendered HTML verbatim and the deploy layer is responsible for
  placing the file alongside the HTML (or rejecting the build).
- **External URL assets:** anything the document references with `http(s)://` or
  `//host/...`. In v1, these pass through verbatim; the rendered HTML still references
  the original CDN URL.
- **Generated assets:** KPress-generated content (KaTeX bundle when math is present,
  etc.). Treated like package assets.

Package asset modes (`asset_mode` in `publish` config):

- `hosted`: the embedding host serves package assets at a configured URL prefix (default
  `/kpress-static/`). Used by the dynamic host-app path; emits no copies.
- `linked`: package assets copied to `_kpress/assets/...` with stable (unhashed) paths.
  Readable, dev-friendly.
- `hashed`: package assets copied with `<name>.<sha>.<ext>` names so the CDN can mark
  them `cache-control: immutable`.
- `inline`: package CSS/JS embedded in the rendered page.
  Fonts stay on disk; KaTeX (when present) stays linked because its stylesheet uses
  relative font URLs.

The `sealed` mode (external assets fetched + integrity-pinned + offline- verified) is
**deferred to v2**; see the section below.

### Static asset caching

Every package asset response carries a strong `ETag` (the SHA-256 of the bytes,
`"kp-<digest>"`) and the route honors `If-None-Match` with a `304`. Cache lifetime then
depends on whether the URL fingerprints the asset by **content** or only by **version**:

- **`hashed` (static build).** The filename embeds the content hash
  (`<name>.<sha>.<ext>`), so the URL changes whenever the bytes change.
  This is a true content fingerprint, so these are served
  `cache-control: public, max-age=31536000, immutable`, so the browser never
  revalidates, and a changed asset is a new URL.
- **`hosted` (dynamic serve from an embedding host app).** The URL is version-addressed
  (`/kpress-static/v<version>/...`), not content-addressed.
  An upgrade bumps `<version>` and yields a fresh URL, so released upgrades never
  collide with a cached older build.
  Within a single version the assets are served
  `cache-control: public, max-age=31536000` **without `immutable`**: the version is only
  a coarse fingerprint, so the same-bytes-per-URL guarantee can break for a
  source/editable checkout, or if a release ever ships changed assets without bumping
  the version. Omitting `immutable` keeps the in-session cache (zero requests across a
  multi-page browse) while letting a normal reload revalidate against the ETag, a cheap
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

The v2 sealing roadmap is tracked in
[`kpress-completion-plan.md`](kpress-completion-plan.md).

## Optimizer and Precompression

Optimization and precompression are publish steps, never render steps.
Dynamic host rendering must not invoke Node, a minifier, or a compressor.

Development checking and publish optimization are separate concerns.
Biome and `tsc --checkJs` reject bad source but never rewrite published output.
The publish optimizer rewrites deployable artifacts and does not replace those checks.

### Optimizer modes and build pipeline plugins

The built-in optimizer contract has exactly two modes, and the optimizer is the
canonical instance of the **build pipeline**: an ordered list of named stage plugins
(see [Extension and Injection Model](#extension-and-injection-model), layer E). There is
no built-in regex pseudo-minifier and no silent fallback.

- `none` (default; stage name `kpress:none`): published HTML/CSS/JS is byte-for-byte the
  rendered output. No Node toolchain is required.
  This is a fully supported output; a static build with `none` is correct, readable, and
  deployable.
- `full` (stage name `kpress:full`): opt in to Node-backed minification/optimization.
  KPress runs `html-minifier-next@6.2.3` through `npx --package`, so callers keep no
  project `package.json` and npm manages the fetch and cache.
  This mode requires Node.js with `npx` on `PATH`.

Selection is explicit: `optimizer.mode` in `kpress.yml`, `--optimizer`, or
`BuildOptions.optimizer`. If `full` is selected and `npx` is unavailable, optimization
raises `KPressMissingOptionalDependencyError` with an actionable message.
It never downgrades to `none` silently, and an unknown mode is an error.
If optimization is not requested, `npx` is not required.

**Pipeline plugins.** A host generalizes the single mode into an ordered stage list via
`build_site(config, extensions=BuildExtensions(...))`:

- `pipeline`: a sequence of stages run in list order over each deployable text artifact.
  A stage is the existing optimizer-backend shape—`name: str` plus
  `optimize(content, *, kind) -> OptimizerResult` (`kind` ∈ html/css/js/other)—given
  either as a built-in stage name (`"kpress:none"`, `"kpress:full"`, pinned by
  `contract.py::PUBLIC_PIPELINE_STAGES`) or as a stage object.
  An unknown stage name is an error (never a silent skip).
  `pipeline=None` derives the list from `optimizer.mode`, providing full back-compat.
  Example: `[my_js_preprocessor, "kpress:full"]` runs a host preprocessing layer before
  the built-in compressor.
- `transform_tree`: an optional `DocumentTree -> DocumentTree` callable applied after
  parsing and before TOC/rendering, for document-level build transforms (e.g. injecting
  section anchors) that should be reflected in the TOC and page model.
- `transform_page_html`: an optional `(html, route) -> html` callable applied to each
  rendered page before the pipeline stages, for whole-page stamps and rewrites.

These are callables and stage objects, not config-file values: the pipeline is the
Python-side extension seam (the build-step exception to the front-end-first rule), and
it stays an explicit ordered list: no priorities, no hook lifecycle.
The manifest records the joined stage names per file (see below).

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

- The build manifest records the resolved stage list per optimized file
  (`optimizer_backend` is the joined stage names, e.g. `full` or `my-preprocessor+full`;
  absent for `none`/no-op), `original_size` when a file was rewritten, and the
  compression method and sizes for each sidecar.
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

The reader-feature accessibility contract adds: heading landmarks and skip-friendly
structure, `aria` state on tabs, TOC, and copy controls, focus-visible interactive
elements, and semantic tooltip markup (`<aside role="tooltip">`).

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

An embedding host app keeps KPress’s vendored PT Serif / Source Sans reader faces by
default, so an embed keeps the KPress reading look rather than the host’s UI fonts.
A host overrides a font per role through the `--kpress-host-font-*` hooks (see the
font-role table under [Theme and Fonts](#theme-and-fonts)); a host app can use this for
a serif/sans reading-font toggle, which sets `--kpress-host-font-prose`. Color tokens
bridge the same way through the other `--kpress-host-*` variables.

### Client runtime (`window.kpress`)

The client runtime (`static/js/runtime.js`, loaded first in the default JS assets) is
the host-facing JS surface, the same one KPress’s own built-ins use (dogfood rule).
It assembles the `kpress` global from per-module namespaces:

- `kpress.model()`: the parsed `#kpress-page-model` page model (empty in fragments;
  embedding hosts get the same data in the `render_view` payload).
- `kpress.on` / `kpress.off` / `kpress.emit`: events (`kpress:ready` after the runtime
  applies registrations; `widget:change` from widgets).
- `kpress.storage`: `{get, set, use(adapter)}`; localStorage default.
  An embedding host swaps persistence with one call (e.g. a cookie adapter for
  cross-port sharing) and every primitive and widget follows.
- `kpress.theme`: the theme engine (see [Theme and Fonts](#theme-and-fonts)).
- `kpress.menu`: the popover-behavior primitive.
- `kpress.widgets`:
  `{register(id, {mount}), configure(id, config), mount(id, el, config?)}`; mounting is
  explicit in embeds (host picks the element), automatic in the standalone page
  (server-emitted mounts).
- `kpress.behaviors`:
  `{register(id, {bind}), override(id, binding), configure(id, config), rebind(id)}`
  over the server-rendered markup.
  A `bind(root)` may return a **disposer**; the runtime calls it before re-binding on
  `override`/`rebind`, so replacement is real: the old binding’s observers and listeners
  are gone, not shadowed.

Lifecycle: modules register at import (no DOM work, no storage I/O); the runtime applies
all registrations on `DOMContentLoaded` and emits `kpress:ready`. Application is
fault-isolated: a throwing mount, bind, or event listener is logged (`console.error`)
and skipped; it never blocks other registrations or `kpress:ready`. Host scripts
injected via `head_extra_html` run before apply, so a host
`register`/`override`/`configure` (and `storage.use`) replaces a built-in cleanly; later
scripts use `rebind`/`mount`. The exported ES-module parts of built-ins (TOC visibility
policy, tooltip placement, …) are importable through the same import map the assets
already publish, and the stability-pinned subset is `contract.py::PUBLIC_JS_EXPORTS`.

Asset shipping is deliberately simple: the default JS/CSS set is a **fixed reader
bundle**: `widgets: {settings: off}` removes the mount (so nothing renders or runs), not
the asset; there is no per-widget asset selection.
A host widget’s own JS and CSS ship through host channels: a `head_extra_html`
`<script type="module">`/`<link>` plus `sources[].static` passthrough for the files.
That is the supported delivery contract (the static-site example’s `demo/extensions.js`
is the reference).

Standalone-vs-embedded for the settings control: an embedding host that previously
forked the gear menu instead mounts the same built-in:
`kpress.widgets.mount("settings", el, {choosers: [...]})` plus
`kpress.storage.use(cookieAdapter)`, and keeps only its font-stack choices via the
`--kpress-host-font-*` vars.
Theme init itself is the registered `theme` behavior (it reads persisted state through
the current storage adapter at apply time and binds the OS listener): an embedding host
that owns theme resolution disables it before apply:
`kpress.behaviors.override("theme", () => {})`, and the engine API (`kpress.theme.set`,
…) stays callable.

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
| `theme_mode` | no | `"system"` (default), `"light"`, or `"dark"`: the user’s theme preference |
| `resolved_theme` | no | `"light"` or `"dark"`: the host’s resolution of `system` for SSR/no-flash bootstrap |
| `host` | no | Free-form host identifier for diagnostics; KPress never special-cases this value |
| `asset_url_prefix` | no | URL prefix the host uses to serve `/kpress-static/...`; defaults to `/kpress-static/` |
| `widgets` | no | Widget presence + opaque config map (same shape as `format.widgets`); echoed in the response payload so host-mounted widgets read the same config the standalone page model carries |

Render response shape:

```jsonc
{
  "type": "kpress-rendered-document",
  "html": "<!-- HTML fragment to inject into the document body -->",
  "profile": "document" | "source" | "table" | "tree" | "plain",
  "printable": true,
  "assets": { "css": ["<asset_url_prefix>v0.0.1/css/document.css", ...],
               "js":  ["<asset_url_prefix>v0.0.1/js/theme.js", ...] },
  "widgets": { "settings": { "choosers": ["theme"] } },  // normalized presence + opaque config
  "model": { "version": 1, "title": "...", "route": "", "profile": "document",
             "headings": [...], "widgets": { ... } },    // same keys as #kpress-page-model
  "diagnostics": []
}
```

The `model` field carries exactly the static page model
(`contract.py::PUBLIC_PAGE_MODEL_KEYS`; `route` is empty, as fragments have no site
route), so a widget reading `kpress.model()`-shaped data works identically when the host
feeds it the payload’s `model`.

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
  so the host can revalidate against the ETag rather than being locked to stale bytes;
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
for the initial server render.
KPress uses it to stamp `data-kpress-resolved-theme` on `<html>` for a no-flash first
paint.

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
via its own `@media print` rules.
KPress does not reach outside its `.kpress` container.

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

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
