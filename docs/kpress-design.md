---
title: KPress Design
description: Package contract for KPress document rendering, document components, static publishing, asset handling, optimization, PDF generation, and acceptance testing.
---
# KPress Design

**Status:** Current architecture and public-contract reference

**Last Verified:** 2026-07-13

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
   The themeable design system *is* a documented set of CSS variables.
   A host sets the public `--kpress-*` document tokens, uses the narrower
   `--kpress-host-*` font and settings-position hooks, and injects its own HTML/CSS/JS
   for anything beyond them.

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
It discovers source files, resolves routes, renders pages, copies KPress-owned and
explicitly declared static assets, writes manifests, optionally optimizes HTML/CSS/JS,
optionally precompresses assets, and can generate browser-print PDFs.

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
| Static publishing | Config, source discovery, routes, manifests, site files, and `hosted`/`linked`/`hashed` site asset modes | Static Publishing; Asset Model |
| Optimization | Optional HTML/CSS/JS minification and gzip/Brotli precompression sidecars (`kpress[optimize]`) | Optimizer and Precompression |
| PDF | Deterministic print-profile PDF artifacts; browser-backed generation behind `kpress[pdf]` | Feature Catalog subsections below |
| Local workflows | CLI: `init` / `convert` / `format` / `render` / `paste` / `files` / `export` / `clean` / `build` / `optimize` / `doctor` | Local Document Workflows |
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

### Markdown and Document Tree

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

### CSS and Layout

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

### Theme and Fonts

- **Light, dark, and system modes** with localStorage persistence,
  `prefers-color-scheme` response, and a synchronous pre-paint no-flash bootstrap.
- **Standalone settings menu.** Full pages ship an accessible, no-print gear-icon
  popover with a `system`/`light`/`dark` icon chooser; embedded hosts own the control
  instead.
- **Font model.** A global `font_mode` selects vendored reader faces (`custom`) or the
  platform stack (`system`); reader fonts are vendored package assets rather than CDN
  dependencies.

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
  and TOC coexistence.
  Remote video is loaded only after the reader activates it.
- **Tabbed content.** Markdown-authored tab containers hydrate into ARIA tablists with
  keyboard support; print shows every panel with its title.

### Media and Assets

- **Images and figures.** Standalone images emit semantic `<figure>/<figcaption>`; raw
  HTML figures receive the same hooks; a document thumbnail renders when provided.
- **Explicit asset ownership.** KPress copies and fingerprints its packaged reader
  assets, copies eligible project-local media while preserving authored URLs, and copies
  additional site files declared through `sources[].static`. External URLs and any
  remaining site files stay the consuming project’s responsibility.

### Print and PDF

- **Print CSS.** Page rules, paper palette, no-print/print-only, TOC and video
  suppression, heading/table break control, repeated table headers, footnote
  simplification, code wrapping, and orphans/widows.
- **Browser-backed PDF.** An optional browser backend renders the print profile to PDF;
  absence of the optional dependency produces a clear error, never a silent downgrade.

This document describes the current alpha architecture and public contract.
Open implementation work and current capability status are indexed in
[`TODO.md`](../TODO.md).

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
Any new packaging tier requires a public design update and issue before implementation.

## Package Layout

Ownership map:

```text
src/kpress/
  cli.py                    command-line parsing and dispatch
  contract.py               versioned public names and schema markers
  models.py                 dynamic-runtime request and response models
  runtime.py                host rendering and package-asset serving
  format/                   document parsing, sanitization, rendering, PDF, and assets
    templates/              live standalone page shell
    static/                 source-first CSS, JavaScript, fonts, icons, and KaTeX
  publish/                  config, discovery, routing, build, manifests, and optimization
  workflow/                 local convert, format, paste, and export workflows
devtools/                   repository quality-gate entry points
tests/                      contracts, fixtures, goldens, and browserless behavior tests
```

Keep new behavior with its current owner.
Moving rendered markup into templates, for example, requires switching the live renderer
and contract tests in the same change; an unused template is not an architectural
improvement.

## Public API

`kpress.contract` is the exhaustive source of truth for top-level, format, and publish
exports. The principal entry points are:

- `kpress.runtime.render_view(request: KPressRenderRequest) -> dict[str, Any]`
- `kpress.runtime.get_static_asset(rel_path: str) -> KPressAsset`
- `kpress.runtime.export_document(request: KPressExportRequest) -> Any`
- `kpress.format.render_fragment(document, options) -> RenderResult`
- `kpress.format.render_page(document, options) -> RenderedPage`
- `kpress.publish.build_site(config, options=None, extensions=None) -> BuildReport`
- `kpress.publish.build_html(src_html, dest_html, options=None) -> BuildReport`

PDF generation is an optional backend under `kpress.format.pdf` and the local
`kpress export --pdf` workflow.
It is not part of `PUBLIC_FORMAT_API`.

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

KPress normalizes inputs through these stages:

1. **Input:** Markdown or source text from a file, host request, or static source tree.
2. **DocumentInput:** typed payload with source and body text, paths, metadata, profile,
   and trust mode. `RenderOptions` carries theme, TOC, math, diagram, widget, and asset
   choices.
3. **DocumentTree:** normalized HTML with headings, TOC entries, footnotes, diagnostics,
   and a math-presence marker.
4. **RenderedDocument:** embeddable fragment with its profile, TOC, asset references,
   diagnostics, and math-presence marker.
5. **RenderedPage:** complete HTML page with title, profile, asset references,
   diagnostics, and math-presence marker.
6. **BuildReport:** route graph, output files, asset manifest, pipeline and compression
   records, and diagnostics.

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
Host view names may map to profiles; KPress emits normalized profile names.

## Markdown, Sanitization, and Source Rendering

Markdown capability:

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

Source rendering capability:

- language metadata
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

`PUBLIC_CSS_CLASSES` is the exhaustive class list.
Keep that tuple and its contract tests authoritative rather than copying a second list
into this document. Classes fall into three groups: namespaced KPress structure and
behavior hooks, print and visibility utilities, and the documented author-facing
semantic classes retained from the document dialect.

`page.html.jinja` is the one live packaged template.
It owns the standalone page shell and renders through `format/templating.py`
(`StrictUndefined` + autoescape).
Fragment and component markup remains in `format/render.py` and `format/markdown.py`.
The separate template migration is tracked by `kpr-hh97`.
`kpress.contract.PUBLIC_TEMPLATE_VARIABLES` therefore pins only the live page template.

The contract module also declares:

- `PUBLIC_PACKAGE_API`: top-level importable names from `kpress`
- `PUBLIC_FORMAT_API`: names from `kpress.format`, including `AssetMode`, `MathMode`,
  `RenderOptions`, `FontSpec`, `TocMode`, `TrustMode`, and `DiagramMode`
- `PUBLIC_PUBLISH_API`: names from `kpress.publish`, including `BuildOptions`,
  `BuildReport`, `OptimizerOptions`, `PublishConfig`, `get_optimizer`, and
  `optimize_text`
- `BUILD_MANIFEST_REQUIRED_KEYS` and `ASSET_MANIFEST_REQUIRED_KEYS`
- `OptimizerMode = Literal["none", "full"]` in `format.model`
- `PUBLIC_DATA_ATTRIBUTES`: the stable per-cell table `data-*` hooks kpress emits for
  downstream enrichment: `data-col` (the column slug derived from the header row) and
  `data-kpress-numeric`. This is the renderer-agnostic seam a downstream decorator
  consumes to select a column by name or detect numeric columns.
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

Publishing exposes the independent `asset_mode`, `optimizer`, and `precompress` axes.
There is no `BuildMode` type or `strict` publishing axis.

### Page Model Block and Widget Mounts

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

KPress is the reusable document-design layer.
Design rules live close to their implementation: CSS owns token values and surface
rules, while this document explains their boundaries and rationale without copying every
declaration.

Two sources of truth:

- **Tokens:** `format/static/css/style-tokens.css`. The `--kpress-*` token tree:
  typography (families/sizes/weights/caps), color and a shared `--kpress-doc-surface-bg`
  family, the corner-radius scale (`--kpress-radius-*`), spacing/measure, motion
  (`--kpress-ease` + `--kpress-transition-*`), and scrollbar colors.
  Each group carries its design rule in a nearby CSS comment.
  The public subset is pinned by `contract.py::PUBLIC_CSS_VARIABLES`. Embedding hosts
  override public document tokens directly; `PUBLIC_HOST_CSS_VARIABLES` separately pins
  the consumed font and settings-inset hooks.
- **Icons:** `format/static/icons/icons.svg`. The SVG sprite is the only source of glyph
  geometry. It contains the required Lucide v1.17.0 symbols and the two KPress reading-
  font symbols on one 24×24 stroke grid.
  The server inlines the hidden sprite once per document and both the server chrome
  (`render.py::_icon`) and the client JS (`static/js/icons.js::icon`) draw a glyph with
  `<svg><use href="#kpress-icon-<name>"></svg>`, so no SVG geometry is authored in
  Python or JS. The contract is enforced by `tests/test_icons.py`.

**Relationship to the host app.** An embedding host keeps app-specific chrome such as
its shell, navigation, and tabs.
It consumes KPress’s document-level CSS, icons, and `--kpress-*` / `data-kpress-*`
contracts instead of copying their implementation.
The standalone page, static publisher, and host embed therefore share one document
layer.

## Icon System

KPress chrome uses [Lucide](https://lucide.dev) v1.17.0 under the ISC license.
Lucide uses a consistent 24×24 stroke grid, so new glyphs match the existing controls
without per-icon visual tuning.
The two reading-font symbols are KPress originals drawn on the same grid.

### Icon Source and Rendering

[`src/kpress/format/static/icons/icons.svg`](../src/kpress/format/static/icons/icons.svg)
is the only file that owns KPress SVG geometry.
It is a hidden sprite containing one `<symbol id="kpress-icon-<name>">` per glyph.

- **Server rendering:** `format/render.py` inlines the sprite once per document through
  the cached `_icon_sprite()` helper.
  `_icon(name, *, css_class, attrs)` emits an
  `<svg><use href="#kpress-icon-<name>"></use></svg>` reference.
- **Client rendering:** [`static/js/icons.js`](../src/kpress/format/static/js/icons.js)
  exports `icon(name, className)`, which emits the same reference.
  The settings and code-copy modules use this helper.

No glyph geometry is authored in Python or JavaScript.
`tests/test_icons.py` pins the required symbols and rejects inline SVG geometry in the
server and code-copy helpers.

KPress inlines the hidden sprite because external `<use href="file.svg#id">` references
are unreliable in headless Chromium and some sandbox or content-security-policy
configurations. One in-document sprite also lets server and client controls resolve the
same symbols without another request.

### SVG Contract

Every glyph uses these wrapper attributes:

- `viewBox="0 0 24 24"`
- `fill="none"`
- `stroke="currentColor"`
- `stroke-width="2"`
- `stroke-linecap="round"`
- `stroke-linejoin="round"`

CSS sets the referencing `<svg>` width and height.
The referencing SVG is decorative and carries `aria-hidden="true"`; the interactive
control owns its visible label, `aria-label`, and `title`.

A replacement glyph must preserve this contract or update every symbol and its consumers
together. Mixing a filled family or a different view box into the sprite would produce
inconsistent weight and sizing.

### Required Glyphs

`tests/test_icons.py::_REQUIRED_ICONS` pins the guaranteed symbol set.
A reserved glyph may remain in the set even when the current interface does not render
it.

| Sprite Name | Lucide ID | Current Role |
| --- | --- | --- |
| `settings` | `settings` | Settings-menu trigger |
| `serif` | KPress original | Serif reading-font choice |
| `sans` | KPress original | Sans-serif reading-font choice |
| `monitor` | `monitor` | System-theme choice |
| `sun` | `sun` | Light-theme choice |
| `moon` | `moon` | Dark-theme choice |
| `x` | `x` | Video and overlay close control |
| `copy` | `copy` | Code-copy idle state |
| `check` | `check` | Code-copy success state |
| `triangle-alert` | `triangle-alert` | Code-copy error state |
| `list` | `list` | Collapsed table-of-contents toggle |
| `maximize` | `maximize` | Reserved media-maximize glyph |
| `external-link` | `external-link` | Reserved external-link glyph |

Embedding applications can own app-chrome glyphs that KPress does not need.
For shared reader controls, they should reference the KPress sprite so the document
layer retains one glyph source.

### Adding a Glyph

1. Find the glyph in the [Lucide icon index](https://lucide.dev/icons) and record its
   Lucide ID.
2. Retrieve the pinned v1.17.0 SVG from the reviewed Lucide artifact, such as
   `https://unpkg.com/lucide-static@1.17.0/icons/<id>.svg`. Verify the version, source,
   and license before copying it.
3. Add a `<symbol id="kpress-icon-<name>">` to `icons.svg`. Copy only the source SVG’s
   inner geometry and use the wrapper attributes from the [SVG Contract](#svg-contract).
4. Reference `_icon("<name>")` in `render.py` or `icon("<name>")` in client JavaScript.
5. Add the name to `_REQUIRED_ICONS` when it becomes part of the guaranteed public set,
   and update the table above.
6. Run the icon and golden tests, regenerate intentionally changed goldens, and review
   that the rendered diff contains only the expected icon change.

### Replacing the Icon Family

A family replacement is one coordinated contract change:

1. Confirm that the family uses the same 24×24 stroke contract, or define and test the
   replacement contract before changing glyphs.
2. Map every entry in the required-glyph table to the new family.
3. Replace each symbol’s inner geometry and update the family, version, and license in
   `icons.svg`, `NOTICE.md`, packaged license files, and this section.
4. Run the package and golden tests.
5. Review standalone pages, static sites, and host embeds in light and dark themes.

### Optional Sprite Overrides

The built-in sprite is fixed in the alpha.
`kpr-e48f` tracks an optional declared sprite override or name-to-symbol map for
consumers that need brand icons or another family.
Until that contract is designed, hosts can reuse the built-in sprite for shared reader
controls and own separate app-specific icons.

## CSS Contract

It must not reference host-shell selectors such as `.tree-pane`, `.preview-pane`,
`.file-header`, or `.tab-bar`.

Foundation tokens are declared on `:root` as well as KPress document and overlay scopes.
The root declaration gives standalone page chrome and body-level fixed UI a complete
namespaced default token set; it does not make unlisted internal tokens stable.
Embedding hosts may rely on the variables in `contract.py::PUBLIC_CSS_VARIABLES` being
initialized at the root for root-inheriting chrome.
Document scopes redeclare their defaults, so a host customizes document tokens on
`.kpress`, not by assuming every root override crosses that scope.
Color and surface customization sets the public `--kpress-doc-*` variables directly.
The consumed `--kpress-host-*` hooks are limited to font roles and settings-menu insets.
The exhaustive lists live in `PUBLIC_CSS_VARIABLES` and `PUBLIC_HOST_CSS_VARIABLES`.

**Body-level overlays.** Tooltips and footnote previews are appended to `<body>`
(outside the `.kpress` subtree) so their `position: fixed` resolves against the
non-scrolling `.kpress-frame` (the standalone shell marks `<body>` itself as the frame)
rather than scrolling away inside the `.kpress-viewport` scroller.
The document tokens above are scoped to `.kpress`, so those overlay selectors
(`.kpress-tooltip`) must be listed alongside `.kpress` in the token-defining rules
(`style-tokens.css`, `theme-light.css`, `theme-dark.css`); otherwise they resolve no
background/color/font and render transparent with a fallback face.

CSS must cover light, dark, mobile, and print modes.
Print CSS forces a light paper palette, hides screen-only controls, preserves footnote
readability, avoids clipped tables and source lines, and makes generated PDFs readable
without host chrome.

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

### Design Tokens and Shared Primitives

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
  All three are public document variables, so a host can override them directly on the
  KPress document scope.
  The neutral default is a subtle link tint, re-derived per light/dark theme.
  All first-party color literals are written as `oklch()` (exact, round-trip-verified
  conversions; see `devtools/css_to_oklch.py`).
- **Palette presets:** default sets for common cases, each a named bundle of public
  document color tokens keyed on `.kpress[data-kpress-palette="<name>"]` and selected
  via `RenderOptions.palette` / `format.palette`. `neutral` is the default (no
  overrides); `warm` is *systematic with neutral*: every token keeps neutral’s lightness
  and near-identical chroma, and only a few are tastefully warm instead of neutral gray:
  ink/muted/border and the surface fills rotate to a warm greige/tan hue, the link keeps
  the warm preset’s own teal, and the hover/selected interaction tints are deliberately
  a step lighter than the plain rotation: gentle, quiet tan highlights.
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
  and the shipped default is **on**. Set the option to `false` for a flat, full-bleed
  page. Low-level fragment callers pass the same option; dynamic `render_view` uses the
  default content-card setting.

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
  Glyphs come from the shared [Icon System](#icon-system).

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

- **The theme engine is a headless client primitive:** `kpress.theme` and the public
  `setKpressTheme` / `initKpressTheme` exports in `theme.js` resolve `system` via
  `prefers-color-scheme`, set `data-kpress-theme` / `data-kpress-resolved-theme`,
  persist through `kpress.storage` (key `kpress.theme`), notify change listeners, and
  track OS theme changes.
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
  font hooks). The mount is a child of the `@container kpress-doc` viewport, so a host
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
own `html`/`body` stay untouched.

It is standalone-only: an embedding host renders the KPress *fragment* (the `.kpress`
article), not the page shell, so neither the settings menu nor `.kpress-page-main`
appears in the host.
The host owns its own pane background and drives the embedded document’s theme by
setting `data-kpress-theme` / `data-kpress-resolved-theme`. The host loads the declared
reader modules and can replace the registered `theme` behavior before runtime apply; see
[Host Integration](#host-integration).
The `system | light | dark` attribute contract is the shared seam; the gear chrome
itself is per-layer.

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

Vendored font files ship as package assets and static builds copy them into the output
tree.

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
- images and local-asset copying with authored URLs preserved
- math support exposes `off` and lazy `auto`. `auto` scans the document; documents
  without math do not parse math, load math JavaScript, fetch CDN assets, or include
  math dependencies in static output.
  Documents with math use KaTeX as the only active renderer, rendered **client-side**.
  The server emits, per expression, a hidden TeX source node and a semantic MathML node;
  a vendored, self-hosted KaTeX bundle (pinned `katex.min.js` + `auto-render` + a small
  init shim, loaded as deferred classic scripts) replaces the TeX node in place on
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
  All twenty faces are vendored (package size, not client transfer); codepoint
  subsetting is intentionally avoided because needed glyphs are content- and not
  vendor-time-determined, and the per-face native lazy load already bounds client bytes.
  KaTeX’s `@font-face` rules carry `font-display: swap` so the late face arrival is a
  clean glyph repaint, not a reflow or an invisible-text gap.
  Native MathML remains valuable as the semantic/accessibility output generated by the
  renderer and as the no-JS fallback (it stays visible until KaTeX swaps, then is moved
  to the accessibility tree).
  KPress has no parallel math-provider matrix.
  `kpr-xsog` owns any publishing changes needed for self-contained math assets.
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

Accepted fixtures and structural tests cover deterministic component output; browserless
tests cover interactive state.
The [end-to-end validation runbook](kpress-validation.runbook.md) owns visual and
real-engine acceptance.

### Component Authoring Contract

These conventions are binding for every interactive document component.
They keep the reader hand-rolled, zero-build, and self-hostable (no component kit, no
platform-only widgets, no positioning library yet).

1. **No JavaScript runtime dependency.** Components are native ESM modules under
   `src/kpress/format/static/js/`. No bundler, no framework, no CDN import.
   They must run from the complete self-hosted package-asset tree and progressively
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
   Registration is what makes every built-in overridable; modules do not call
   `initKpress<Name>()` directly at import time.
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
   (tooltips, video popover, or TOC drawer) must use `static/js/overlay.js`:
   `computePosition` for viewport-aware placement, `dismissOnEscape` / `dismissOnResize`
   / `dismissOnOutsideClick` for teardown, and `toggleBackdrop` for backdrop plus
   `aria-hidden` state.
   Per-component positioning or dismiss logic must not be reintroduced.
   KPress has no positioning-library dependency.
   Adding one requires a demonstrated need for behavior the current primitive cannot
   provide, such as simultaneous multi-axis flip and shift or virtual-element anchoring.
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
used, overridden, enhanced, and re-injected) plus the decision rules for where
customization belongs.
The placement rules themselves (no-JS, schema-with-the-code, dogfood) are Core Principle
5\.

Guardrail: nothing here is a plugin framework, hook lifecycle, or DI container.
The whole model is three concrete shapes: **published data** (the page model, state
attrs, and tokens), a **registry** (a dict you add to: JS at runtime, or the widget
presence map in Python at build time), and an **ordered list of stages** (the build
pipeline). A proposed seam that is not one of those shapes does not belong.

### The JavaScript/Python Boundary

> Customization is front-end code; Python orchestrates and injects it; whole-artifact
> build-time processing is a Python plugin.

| Concern | Lives in | Why |
| --- | --- | --- |
| Widget behavior and markup, new interactive widgets, replacing TOC logic, rebinding tooltip/footnote hover, per-reader state, restyling | JavaScript / CSS (layers A–C) | Interactive, runs in the browser, per-reader; standard front-end code |
| Which widgets ship, opaque widget config, injecting host JS/CSS, assembling the page, driving the build | Python (layer D) | Build/host wiring; transports data and snippets; implements no widget logic |
| Minify/compress, document-tree transforms, HTML post-processing, asset packaging | Python plugin (layer E) | Needs the whole artifact, runs once at build, no browser: a proper build step |

Litmus: *needs a browser or runs per reader?* → front-end (Python only injects it).
*Transforms the whole artifact once at build?* → Python pipeline plugin.

### Layer A: Page Model and State Contract (Published Data)

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

### Layer B: Client Primitives (Built-In Headless Engines)

The genuinely complex machinery ships built-in, headless, and reusable, separate from
any presentation:

- `kpress.theme`: resolve system preference, set and persist mode, apply the pre-paint
  state, and notify change listeners through the public `theme.js` exports.
- `kpress.storage`: persistence with a pluggable adapter (`{get, set}`; localStorage
  default; an embedding host can supply cookies for cross-port sharing).
- `kpress.menu`: popover behavior: open/close, outside-click/Escape dismiss,
  `aria-checked` segment marking.

A host that wants a bare dark/light toggle writes a few lines over `kpress.theme`; the
gear menu is only the default presentation of that engine.

### Layer C: Widget and Behavior Registries (Named, Optional, Replaceable)

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

Runtime mutation semantics are uniform:

| Operation | Alpha behavior |
| --- | --- |
| `mount(id, element, config)` | Replaces resolved config for that explicit mount. |
| `configure(id, config)` | Merges config and reapplies immediately after ready. |
| `register(id, implementation)` | Replaces the implementation and remounts/rebinds existing targets after ready. |
| Explicit mount before ready | The ready pass sees the bound marker and does not mount twice. |
| `theme:change` / `palette:change` | Reapplies presentation widgets and behaviors, except a widget containing keyboard focus is preserved mid-interaction. The theme behavior is excluded and nested presentation changes are ignored to prevent recursion. |

Widget mounts may return a disposer; KPress calls it before remounting.
Behavior binds have the same disposer contract.
A host changing palette state directly should emit `palette:change` after updating its
attributes.

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

### Layer D: Python Orchestration (What Ships; No Widget Semantics)

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

### Layer E: Build Pipeline Plugins (Python; the Build-Step Exception)

```python
build_site(config, extensions=BuildExtensions(
    pipeline=[my_js_preprocessor, "full"],          # pre-stage before the built-in compressor
    transform_tree=add_section_anchors,             # document-tree transform
    transform_page_html=stamp_build_info,           # final-HTML transform
))
```

Stages share the optimizer backend shape (`name` + `optimize(content, *, kind)`),
resolved by name (`none`, `full`) or passed as objects, and run in list order.
See [Optimizer and Precompression](#optimizer-and-precompression).

### The Tiers (Simple → Complex, Purpose-Agnostic)

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

### What a Plugin Is

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

### The Document Model

A KPress document is a body fragment: Markdown blended with an admitted set of custom
HTML/XML tags, one mixed vocabulary in which the standard tags Markdown compiles to and
a plugin’s custom hyphenated tags ride through under the same sanitizer policy.
A block-level custom tag surrounded by blank lines opens an HTML block whose inner
content re-parses as Markdown (standard CommonMark behavior), so links, math, and
footnotes render inside it; an inline custom tag wraps inline content.
Title and metadata travel as frontmatter, never guessed from the body.
A plugin can pass sidecar data through its own injected markup or a separate fetch.
The page model has no generic extension-data key; `kpr-4qxl` tracks that missing seam.

### The Plugin Boundary: Text and Files, Not an AST

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

### Conventions, Not a Closed Dialect

KPress documents the conventions; the tag vocabularies are the plugins’ business.

- **Prefixes.** A plugin claims a short tag prefix (such as `x-…`) and declares its tags
  in the admission config; data payloads follow a matching `data-…` convention.
  The `k-*` tag prefix and the `kpress-*` class/data/id prefix are reserved for KPress’s
  own use by convention, so plugins do not squat them.
  This is a governance signal, not a hard-coded list.
- **Attributes.** Plugin tags carry clean inert attributes.
  A plugin declares its semantic attribute names (`kind`, `term`, …) through
  `format.html.extra_attributes` and they survive `sanitized` on whitelisted tags, so
  `<x-block kind="epigram">` is the idiomatic form; `class` stays available and `data-*`
  remains the open-ended escape hatch for arbitrary payload (no declaration needed).
  `id` and ARIA survive only under `trusted`; `on*`, `style`, and unsafe-URL attributes
  are always stripped.
  Sanitization does not prove that surviving tags, classes, or data values came from a
  trusted plugin. Hosts must not use content-authored values as authorization or
  unforgeable identity signals.
- **No pinned vocabulary.** KPress does not freeze a closed dialect because that would
  place plugin-owned vocabulary in the KPress contract.
  The conventions are the contract.

### Graduated Complexity

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
  Basic CSS styles the block; an optional behavior reads sidecar data from injected
  markup or a separate fetch to add term tooltips elsewhere.
- **Table decorators** (front-end only).
  KPress emits neutral enrichment attributes on table cells; a client decorator consumes
  them to sort or chart, with no preprocessing and no KPress-specific code.
  KPress emits the hooks and never consumes them.

## Static Publishing

Static publishing reads `kpress.yml`, discovers source files, merges metadata, resolves
routes, renders pages, copies KPress-owned assets and eligible project-local media,
optionally optimizes output, and writes manifests.
It does not fetch external URLs or rewrite arbitrary HTML, CSS, or JavaScript asset
graphs.

Source conventions:

- Markdown files are renderable sources
- YAML frontmatter is part of the document
- sidematter files may provide additional metadata
- eligible relative media references inside the project tree are copied without
  rewriting their document URLs
- `sources[].static` patterns copy additional site-owned files verbatim
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
| Asset shaping | `publish.asset_mode` / `--asset-mode` | `linked` (readable) | `hosted`, `linked`, `hashed` |
| Optimizer | `optimizer.mode` / `--optimizer` | `none` | `none`, `full` |
| Precompression | `optimizer.precompress` / `--precompress` | none | `gzip`, `br` |

Every axis is independent.
`linked` keeps readable package-asset names; `hashed` fingerprints KPress-owned assets
for production caching; `hosted` delegates package-asset serving to an embedding host.
Selecting `full` without the Node toolchain or `br` without `kpress[optimize]` is a
clear error, never a silent downgrade.
`inline` is rejected for site builds because it is not self-contained.

### Named Output Modes

The independent axes (`asset_mode`, `optimizer`, `precompress`) cover both dynamic
per-request rendering and static publishing.
The following common combinations are conveniences over the underlying axes, not coarse
build modes that hide them.

| Mode | Layer | `asset_mode` | `optimizer` | `precompress` | Entry point | Status |
| --- | --- | --- | --- | --- | --- | --- |
| **Dynamic multifile** | Runtime | `hosted` | host-side, if any | host-side | `render_fragment` + host asset route | Supported |
| **Static build dev** | Publisher | `linked` | `none` | none | `kpress build` | Supported; readable multi-file tree |
| **Static build production** | Publisher | `hashed` | `full` when desired | optional | `kpress build` | Supported; content-hashed KPress assets |
| **Self-contained single file** | Publisher | `inline` | optional | n/a | format/render/export | Unsupported; tracked by `kpr-xsog` |

For a “share one HTML file by link” workflow, deploy a `hashed` static build or a
dynamic multifile embed.
KPress makes no integrity, fetching, or offline-completeness guarantee for external
URLs.

Dynamic and static differ in *layer*, not in shaping intent.
Dynamic emits one HTML fragment and a JSON asset manifest per request; static emits a
directory tree the deploying host serves verbatim.

#### Self-Contained Single File: Unsupported

KPress does not emit one HTML file that opens over `file://` without sibling assets.
Low-level `inline` rendering still has ES-module imports and font files, and math adds a
linked KaTeX subtree.
The CLI and static publisher therefore reject `inline` instead of emitting an artifact
that only appears self-contained.

Publish a complete `linked` or `hashed` directory and serve it over HTTP. `kpr-xsog`
tracks self-contained and verified-offline publishing.

#### Dynamic Multifile Optimization

The wheel ships source CSS and JavaScript, not parallel minified or hashed variants.
Embedding hosts that need optimized runtime assets apply their own deployment-time
optimization and serve the result through a custom `asset_url_prefix`. Static builds use
KPress’s explicit `full` optimizer instead.

## Asset Model

KPress sees four kinds of assets:

- **Package assets:** CSS/JS/fonts vendored inside the wheel (`format/static/`). Copied
  into the publish output tree (or served dynamically) by KPress itself.
- **Document-local assets:** relative references to existing files with supported media
  suffixes inside the project tree are copied beside the rendered route, preserving the
  authored URL. Other relative files are not discovered implicitly; declare them through
  `sources[].static` or provide them in the deploy layer.
- **External URL assets:** anything the document references with `http(s)://` or
  `//host/...`. These pass through verbatim; the rendered HTML still references the
  original CDN URL.
- **Generated assets:** KPress-generated content (KaTeX bundle when math is present,
  etc.). Treated like package assets.

Static-publisher package asset modes (`publish.asset_mode`):

- `hosted`: the embedding host serves package assets at a configured URL prefix (default
  `/kpress-static/`). Used by the dynamic host-app path; emits no copies.
- `linked`: package assets copied to `_kpress/assets/...` with stable (unhashed) paths.
  Readable, dev-friendly.
- `hashed`: package assets copied with `<name>.<sha>.<ext>` names so the CDN can mark
  them `cache-control: immutable`.

The low-level `AssetMode` type also includes `inline` for renderer and equivalence
internals.
Static config and CLI commands reject it because fonts, ES-module imports, and
KaTeX remain linked, so the result would not be self-contained.

No alpha asset-mode name implies fetching, integrity-pinning, or offline-verifying
external assets.

### Static Asset Caching

Dynamic `get_static_asset` responses carry a strong `ETag` (the SHA-256 of the bytes,
`"kp-<digest>"`). The embedding host can use it to answer `If-None-Match` with a `304`.
Cache policy depends on whether the URL fingerprints the asset by **content** or only by
**version**:

- **`hashed` (static build).** The filename embeds the content hash
  (`<name>.<sha>.<ext>`), so the URL changes whenever the bytes change.
  This is a true content fingerprint, so a deployment can safely serve these files with
  `cache-control: public, max-age=31536000, immutable`; a changed asset has a new URL.
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

The build manifest records source files, routes, output files, hashes, optimizer
settings, diagnostics, and warnings.
Build and asset manifests include explicit current schema markers:

- `kpress-build-manifest-v2`
- `kpress-asset-manifest-v1`

### Unsupported Complete Asset Sealing

Sealing the complete document-local and external-URL asset graph (downloading remote
references, content-hashing every file, rewriting every URL in HTML, CSS, and JavaScript
to its verified local path, then verifying that the tree is free of remote references)
is not part of the alpha contract.
`kpr-xsog` tracks that work.

Current boundary:

- **Parser boundary.** A complete graph needs syntax-aware HTML, CSS, and JavaScript
  parsing. Regex replacement would mishandle quoting, module specifiers, and URL forms.
- **Deployment ownership.** KPress emits HTML plus the assets it owns or explicitly
  discovers. The consuming project chooses whether remaining URLs stay remote, are copied
  by another build step, or are rejected by deployment policy.

What KPress does:

- Package assets (KPress’s own CSS/JS/fonts) are copied into the output tree with the
  selected `linked` or `hashed` shape, or served by the host in `hosted` mode.
  This is the only asset graph KPress owns and rewrites.
- KaTeX bundle is copied (unhashed, vendored) when math is present.
- Document-local refs are emitted verbatim.
  KPress copies eligible existing media from inside the project tree and files declared
  through `sources[].static`; the deploy layer owns any remaining files and broken-link
  policy.
- External refs (`https://...`) are emitted verbatim.
  The browser fetches at view time, same as any normal site.

The alpha makes no verified external-asset guarantee.

## Optimizer and Precompression

Optimization and precompression are publish steps, never render steps.
Dynamic host rendering must not invoke Node, a minifier, or a compressor.

Development checking and publish optimization are separate concerns.
Biome and `tsc --checkJs` reject bad source but never rewrite published output.
The publish optimizer rewrites deployable artifacts and does not replace those checks.

### Optimizer Modes and Build Pipeline Plugins

The built-in optimizer contract has exactly two modes and provides the default **build
pipeline**: an ordered list of named stage plugins (see
[Extension and Injection Model](#extension-and-injection-model), layer E). There is no
built-in regex pseudo-minifier and no silent fallback.

- `none` (default; stage name `none`): published HTML/CSS/JS is byte-for-byte the
  rendered output. No Node toolchain is required.
  This is a fully supported output; a static build with `none` is correct, readable, and
  deployable.
- `full` (stage name `full`): opt in to Node-backed minification/optimization.
  KPress ships a reviewed `package-lock.json` for `html-minifier-next@6.2.3`, copies it
  into a file-locked user cache, and installs only with `npm ci --ignore-scripts`.
  Callers keep no project `package.json`. This mode requires Node.js with npm on `PATH`.

Selection is explicit: `optimizer.mode` in `kpress.yml`, `--optimizer`, or
`BuildOptions.optimizer`. If `full` is selected and Node, npm, or the locked package is
unavailable, optimization raises `KPressMissingOptionalDependencyError` with an
actionable message. It never downgrades to `none` silently, and an unknown mode is an
error. If optimization is not requested, Node and npm are not required.

**Pipeline plugins.** A host generalizes the single mode into an ordered stage list via
`build_site(config, extensions=BuildExtensions(...))`:

- `pipeline`: a sequence of stages run in list order over each deployable text artifact.
  A stage is the existing optimizer-backend shape—`name: str` plus
  `optimize(content, *, kind) -> OptimizerResult` (`kind` ∈ html/css/js/other)—given
  either as a built-in stage name (`"none"`, `"full"`, pinned by
  `contract.py::PUBLIC_PIPELINE_STAGES`) or as a stage object.
  An unknown stage name is an error (never a silent skip).
  `pipeline=None` derives the list from `optimizer.mode`. Example:
  `[my_js_preprocessor, "full"]` runs a host preprocessing layer before the built-in
  compressor.
- `transform_tree`: an optional `DocumentTree -> DocumentTree` callable applied after
  parsing and before TOC/rendering, for document-level build transforms (e.g. injecting
  section anchors) that must be reflected in the TOC and page model; transforms that
  change headings rebuild `tree.toc`.
- `transform_page_html`: an optional `(html, route) -> html` callable applied to each
  rendered page before the pipeline stages, for whole-page stamps and rewrites.

These are callables and stage objects, not config-file values: the pipeline is the
Python-side extension seam (the build-step exception to the front-end-first rule), and
it stays an explicit ordered list: no priorities, no hook lifecycle.
The manifest records the configured stages in `pipeline` and the stages that changed
each file in `applied_pipeline` (see below).

The full optimizer is preflighted at the start of a publish operation, before creating,
purging, writing, or copying outputs.
The preflight is network-free: a cold cache fails with instructions to run
`kpress doctor --profile optimize --allow-network` once.
That explicit doctor command installs from the shipped lock; subsequent builds consume
only the warm cache.
If Node or the locked optimizer package is unavailable, the publish command fails
conspicuously with no partial success status and no fallback to `none`.

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

### Manifest and Equivalence

- The build manifest records the ordered configured stage names in `pipeline` and each
  file’s ordered changed-stage names in `applied_pipeline`. It also records
  `original_size` when a file was rewritten and the compression method and sizes for
  each sidecar.
- `none` plus optional precompression preserves the rendered document surface exactly.
  `full` must preserve functional equivalence with `none`: the only accepted differences
  are minification, hashing, URL shape, and compression.
- Tests prove dynamic rendering never imports the optimizer.

## Local Document Workflows

KPress provides local document workflows without hosted-service coupling.

Commands:

```bash
kpress init
kpress convert INPUT --output OUTPUT.md
kpress format INPUT --output-dir DIR
kpress render INPUT.md --output OUTPUT.html
kpress paste --title TITLE --text TEXT
kpress files
kpress export INPUT.md --html OUT.html
kpress clean --config kpress.yml
kpress build --config kpress.yml
kpress build --config kpress.yml --asset-mode hashed --optimizer full --precompress gzip
kpress doctor --config kpress.yml
kpress optimize INPUT --output OUTPUT --backend full
```

Relevant flags:

- the global `--work-root` option appears before the subcommand
- `format`, `render`, and `build` accept `--asset-mode` where they shape package assets
- `export --pdf` adds an optional browser-backed PDF when `kpress[pdf]` and Chromium are
  installed

The workflow layer owns workspace paths, cache semantics, output names, local reports,
paired Markdown/HTML output, and emission of package assets and eligible local media
without rewriting authored media URLs.
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
- `--allow-network`: the only gate that bootstraps a cold optimizer cache with the
  shipped lock. It is accepted by `doctor`; build and direct optimizer paths remain
  network-free. Warm-cache and Node/npm presence checks are always no-network.
- `--json`: stable `{kpress_version, platform, python_version, capabilities}` with the
  closed status set.

Capability semantics mirror the runtime contract: `optimizer=none` without Node is OK;
`optimizer=full` without the toolchain, `br` without `brotli`, or PDF without Playwright
are failures only when that path is requested, otherwise reported as unavailable or
skipped.

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
- CI job `lint`
- lefthook staged-file formatting and validation for KPress Python, JS, CSS, and JSON

Runtime JavaScript is native ESM and requires no build step for dynamic hosts.
Any proposal to introduce TypeScript source must first define a stale-build check and a
generated-output policy.

## Document Acceptance and Regression Harness

Accepted KPress output is the regression contract.
Each scenario compares current output with a reviewed KPress baseline.

Required layers:

- representative source scenarios under `tests/golden/scenarios/`
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

The [validation runbook](kpress-validation.runbook.md) defines the automated, agent, and
human acceptance evidence required for document components, browser behavior, and print
output.

## Accessibility

Current KPress output provides:

- document landmarks while preserving the author’s heading order
- accessible settings and TOC controls
- keyboard-operable details, tabs, and popovers
- live-region feedback for transient copy status
- reduced-motion behavior for animated reader controls
- tooltip triggers that degrade cleanly on touch/mobile
- print output that excludes screen-only controls

The reader-feature accessibility contract adds: heading landmarks and skip-friendly
structure, `aria` state on tabs, TOC, and copy controls, focus-visible interactive
elements, and semantic tooltip markup (`<aside role="tooltip">`).

Browserless tests cover deterministic interaction and ARIA state.
The validation runbook covers manual keyboard, light/dark contrast, responsive, and
print review. The broader accessibility audit remains tracked as `kpr-vxy5`.

## Host Integration

The embedding host should call KPress through the dynamic runtime and serve KPress
assets. It should not copy component CSS or JavaScript into host-specific selectors.

Host responsibilities:

- read files and frontmatter
- choose active view and printability
- map host view names to KPress profiles
- serve KPress package assets
- hide host chrome during print
- handle dependency or import failure if the host deliberately makes KPress optional
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
a serif/sans reading-font toggle, which sets `--kpress-host-font-prose`. Hosts customize
colors by setting the public `--kpress-doc-*` tokens on the document scope.

### Client Runtime (`window.kpress`)

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

An embedding host can mount the same settings widget used by a standalone page:
`kpress.widgets.mount("settings", el, {choosers: [...]})` plus
`kpress.storage.use(cookieAdapter)`, and keeps only its font-stack choices via the
`--kpress-host-font-*` vars.
Theme init itself is the registered `theme` behavior (it reads persisted state through
the current storage adapter at apply time and binds the OS listener): an embedding host
that owns theme resolution disables it before apply:
`kpress.behaviors.override("theme", () => {})`, and the engine API (`kpress.theme.set`,
…) stays callable.

### Dynamic Render Contract

The host calls `kpress.runtime.render_view(KPressRenderRequest)` and receives a
JSON-ready dict. Fields and semantics:

| `KPressRenderRequest` field | Required | Meaning |
| --- | --- | --- |
| `source_text` | yes | Document text the host has already decoded |
| `source_path` | yes | Relative path inside the host’s worktree; used for diagnostics, metadata, and the source-profile header |
| `kind` | yes | Host-side file kind (`markdown`, `text`, `structured`, etc.); carried in render metadata |
| `view` | yes | Host-side view name (`rendered`, `source`, `tree`, …); normalized via `normalize_print_profile` into a KPress profile |
| `ext` | yes | Lowercase file extension including the dot; carried in render metadata |
| `mtime_hash` | yes | Host-supplied content fingerprint; part of the in-process render-cache key |
| `size` | yes | Byte size of the source; reported when a source-profile preview is truncated |
| `frontmatter` | no | Parsed YAML metadata the host already extracted; KPress treats this as authoritative |
| `frontmatter_error` | no | Host-side YAML parse error string; surfaced as a visible reader banner |
| `profile` | no | Optional explicit KPress profile override; bypasses the view-name mapping |
| `theme_mode` | no | `"system"` (default), `"light"`, or `"dark"`: the user’s theme preference |
| `resolved_theme` | no | `"light"` or `"dark"`: the host’s resolution of `system` for SSR/no-flash bootstrap |
| `host` | no | Free-form host identifier for diagnostics; KPress never special-cases this value |
| `asset_url_prefix` | no | URL prefix the host uses to serve `/kpress-static/...`; defaults to `/kpress-static/` |
| `show_doc_header` | no | Whether a document-profile fragment renders its title header; defaults to `true` |
| `widgets` | no | Widget presence + opaque config map (same shape as `format.widgets`); echoed in the response payload so host-mounted widgets read the same config the standalone page model carries |
| `extra_tags` | no | Additional inert HTML/XML tags admitted by the sanitized render path |
| `extra_attributes` | no | Additional inert attributes admitted only on pass-through tags |

Render response shape:

```jsonc
{
  "type": "kpress-rendered-document",
  "html": "<!-- HTML fragment to inject into the document body -->",
  "profile": "document" | "source" | "table" | "tree" | "plain",
  "printable": true,
  "assets": { "css": ["<asset_url_prefix>v<version>/css/document.css", ...],
               "js":  ["<asset_url_prefix>v<version>/js/theme.js", ...] },
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

### Asset Serving

KPress package assets live at `/kpress-static/v<version>/<rel_path>`. The host mounts a
route that calls `kpress.runtime.get_static_asset(rel_path)` and returns the resulting
`KPressAsset` (`content`, `media_type`, `etag`, `cache_control`). The runtime
guarantees:

- Path traversal is rejected (paths with `..` or absolute prefixes raise
  `KPressAssetNotFoundError`).
- Versioned URLs (`/kpress-static/v<version>/...`) return
  `cache-control: public, max-age=31536000` (long-lived, but **not** `immutable`);
  unversioned URLs return `no-cache`. The version segment is only a coarse fingerprint,
  so the host can revalidate against the ETag rather than being locked to stale bytes;
  see “Static asset caching” above for the rationale.
- `etag` is content-stable; the host can honor `If-None-Match` (the route answers a
  matching conditional request with `304`).

A host that wants to point at a CDN-hosted KPress bundle passes a different
`asset_url_prefix` in `KPressRenderRequest`; KPress URL-builds against that prefix
without any code change.

### `postMessage` Protocol (Embedded Reader → Host)

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

### Theme Mode Plumbing

`theme_mode` is one of `"system" | "light" | "dark"` and represents the user’s
preference. `resolved_theme` (`"light" | "dark"`) is the host’s resolution of `system`
for the initial server render.
KPress uses it to stamp `data-kpress-resolved-theme` on `<html>` for a no-flash first
paint.

After load, `theme.js` listens for the system color-scheme media query and updates the
resolved attribute live; it also persists explicit `theme_mode` choices to the active
`kpress.storage` adapter under `kpress.theme`. The standalone full-page render ships an
accessible settings gear with System, Light, and Dark choices bound to the same
machinery. Embedded hosts with their own theme control set `theme_mode` per request and
can replace the registered `theme` behavior.

### Print Profile Mapping

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

### Static Export Seam

For “render this document into a publishable artifact” use cases, the host calls
`kpress.runtime.export_document(KPressExportRequest)` rather than `render_view`. The
current implementation supports the single-page export path.

| `KPressExportRequest` field | Choices | Meaning |
| --- | --- | --- |
| `path` | source path | Existing UTF-8 document to export |
| `print_profile` | `document`/`source`/`table`/`tree`/`plain` | Same as the render contract |
| `export_mode` | `page` | Supported output shape. `single-file` fails explicitly; the other declared literals are reserved and do not yet select distinct implementations. |
| `asset_mode` | `linked` (default), `hashed` | Package-asset shape. The declared low-level `inline` mode is not self-contained and is not a supported portable export. |
| `optimize` | bool | Maps to `optimizer=full` when true |
| `destination` | path | Where to write the artifact; KPress derives a default from `path` if omitted |
| `extra_tags` | tag names | Additional pass-through tags admitted by the sanitizer |
| `extra_attributes` | attribute names | Additional inert attributes admitted on pass-through tags |

The dataclass also carries `kind`, `view`, and `theme_mode`; the current single-page
implementation does not use those fields.
PDF export is available through the local `kpress export --pdf` workflow, not through
this runtime request.
A host surfaces the returned build report or a typed publishing error to the user.

### Failure Modes the Host Must Handle

| Exception | Origin | Host response |
| --- | --- | --- |
| `KPressInvalidRequestError` | Malformed request (e.g. unknown print profile) | 400 with the underlying message |
| `KPressRenderError` | Render pipeline raised | 502 with diagnostics |
| `KPressAssetNotFoundError` | Asset path rejected as unsafe or missing | 404 |
| `KPressPublishError` | Static export cannot complete safely, including unsupported modes | Surface as an export failure |
| `KPressMissingOptionalDependencyError` | Requested optimizer or PDF dependency is unavailable | Surface as a setup error; do not silently downgrade |
| `KPressOptimizerError` | The selected optimizer fails | Surface as an export failure with the original diagnostic |

`KPressInvalidRequestError` is a `ValueError` subclass for ergonomic catching, but hosts
should catch it specifically rather than catching all `ValueError`s.

### Embedding Adapter Guidance

An embedding adapter should import `kpress.runtime` as a required dependency, translate
KPress exceptions only at an application boundary that needs application-specific error
types, serve the full asset closure, and keep host chrome outside the KPress fragment.
If an application deliberately makes KPress optional, its availability probe and
fallback are application-owned; KPress itself does not provide a fail-quiet adapter.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
