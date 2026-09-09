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
| Fonts | Vendored PT Serif / Source Sans 3 / quote subset with `custom`/`system` modes and per-role host overrides | Theme and Fonts |
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
- **GitHub-compatible heading anchors and TOC metadata.** Heading ids are generated from
  visible plain inline text by a dependency-free implementation pinned to
  `github-slugger` 2.0.0 at commit `3461c4350868329c8530904d170358bca1d31448` and its
  Unicode 13 exclusion data.
  The complete published 78-case fixture sequence pins the contract: lowercase, remove
  the upstream exclusion set, replace each literal ASCII space with one hyphen, preserve
  leading/trailing spaces as leading/trailing hyphens, allow an empty slug, and allocate
  collisions from `-1` with upstream occurrence bookkeeping.
  The generated id is the single source for heading markup, `Heading.id`, TOC links, the
  page model, browser behaviors, and broken-anchor diagnostics; percent-encoded and
  literal Unicode fragments resolve to that same id.
  A single leading H1 is excluded from the TOC. TOC entry levels are structural depths,
  not raw tag levels: each entry nests one level under its nearest preceding shallower
  heading, so the TOC always forms a proper tree.
  A heading with no enclosing ancestor (an H3 before the first H2) lists at the top
  level rather than indenting ahead of shallower entries, and skipped levels (an H4
  directly inside an H2) compress to one step.
  Rendered heading tags are unchanged; this normalization is TOC-only.
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
  DOM and model identities are parser ordinals: `fn-1`, `fnref-1`, and `fnref-1-2` for a
  repeated first reference.
  Authored labels remain source syntax and diagnostic context, never identity.
- **Code fences and syntax highlighting.** Language-classed code blocks with server-side
  token markup and a shipped light and dark highlight stylesheet.
- **Source profile.** Large source files are capped to a bounded preview with a visible
  truncation notice; a filename/extension language fallback applies.
- **Math.** Public modes are `off` and lazy `auto`. `off` leaves delimiters literal and
  loads nothing. `auto` detects math before doing any math work: a document with no math
  loads no math code or assets.
  When math is present KaTeX is the active renderer; it is applied progressively, after
  the rest of the document has rendered, so prose is never blocked on math.
  Native MathML is the fallback when scripting is unavailable or enhancement fails; it
  is temporarily suppressed while enhancement prepares the fonts.
  Once KaTeX has rendered, that MathML remains as the semantic and accessibility output.
  The runtime creates hidden math immediately, then waits for the rendered glyphs’
  matching fonts before revealing each formula.
  By default the Latin letters and digits inside mathematics are drawn from the reading
  face and KaTeX lays them out from matching metrics; see
  [Math Text Face](#math-text-face).
  (MathJax is out of scope unless real content proves KaTeX insufficient.)
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
  The bulleted marker is a drawn `currentColor` box, not a glyph: see
  [List Markers](#list-markers).
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
  platform stack (`system`); `mono_font` and `mono_weights` decide separately which mono
  faces a document declares at all.
  Reader fonts are vendored package assets rather than CDN dependencies.

### Interactions

- **Table of contents.** Desktop sticky rail with active-heading tracking and smooth
  scroll; mobile drawer with backdrop, body-scroll lock and restore, scrollbar-width
  compensation, outside-click and Escape close, and iOS overscroll handling.
- **Footnote controls.** The reference in the text, the backref after its footnote, and
  the navigation link in its preview are one control family: alike at rest, and
  answering a hover the way the document’s other small controls do (link colour,
  link-coloured border, the shared hover wash), so a host restyles them by setting the
  link and surface tokens rather than by matching selectors.
- **Footnote tooltips.** Hover, focus, and touch previews with truncation, a navigation
  link, delayed hide, and a trigger-to-tooltip hover bridge; accidental footnote
  navigation is prevented.
  The proposed replacement for this current alpha behavior is specified in
  [Interactive Footnote Popovers](interactive-footnote-popovers.plan.md): transient
  previews remain descriptive, while deliberate activation pins an accessible surface
  whose links can be used reliably.
- **Internal-link tooltips.** Previews for headings (with nearby text), figures, tables,
  code, and details, with viewport-aware placement, arrow positioning, touch fallback,
  and Escape close.
- **Tables.** Responsive wrapping, numeric-column alignment hooks, small-caps headers
  (hyphenating rather than letter-breaking when narrow), zebra rows, TOC-aware desktop
  breakout, mobile font reduction, and print flattening.
  Numeric detection is column-scoped: a column is numeric when at least one non-empty
  body cell matches the numeric pattern (sign — ASCII or typographic minus — currency,
  grouped digits, decimals, percent) and none mismatches; then every cell of the column,
  header included, carries `data-kpress-numeric`, while mixed columns keep the default
  start alignment with no marks.
  Header-backed cells carry `data-col="<visible header label>"`, preserving case,
  punctuation, and Unicode after whitespace normalization, plus the 1-based
  `data-col-index`. The index lets downstream decorators select duplicate or
  empty-labeled columns unambiguously without kpress depending on them.
  The wide presentation (bleeding past the reading column on wide panes; edge-bleed
  scroll regions on phones) is reserved for genuinely large tables: the renderer stamps
  `data-kpress-table-scale` (value `wide`) on the wrap only when the widest row has at
  least 6 columns AND the average row carries at least 100 visible characters.
  The resolved cutoff is stamped on the article root
  (`data-kpress-table-wide-min-columns` / `data-kpress-table-wide-min-row-chars`), and
  `tables.js` — which re-classifies tables for late-rendered/tabbed panels — resolves
  thresholds per table with explicit runtime config
  (`kpress.behaviors.configure("tables", { wideMinColumns, wideMinRowChars })`) first,
  then the stamped values, then its built-in defaults, so a custom
  `RenderOptions`/`kpress.yml` cutoff survives the runtime pass.
  Smaller tables keep the reading-column width and scroll internally.
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
  suppression, page-margin alignment for standalone and fragment shells, heading/table
  break control, repeated table headers, footnote simplification, code wrapping, and
  orphans/widows.
- **Browser-backed PDF.** An optional browser backend renders the print profile to PDF;
  absence of the optional dependency produces a clear error, never a silent downgrade.
- **Document-actions widget (opt-in).** Text badge buttons — PDF (the browser print
  dialog over the print CSS) and MD (the page’s `.md` twin) — client-rendered like the
  settings gear but off by default: `format.widgets: {doc-actions: on}`. See
  [Document Actions Widget](#document-actions-widget).

The architecture and contracts here are the current alpha surface; open implementation
work and capability status are indexed in [`TODO.md`](../TODO.md).

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
- `RenderOptions.include_theme_resolver` / `KPressRenderRequest.include_theme_resolver`:
  explicit ownership of the standalone theme resolver; pages default on and fragments
  default off.
- `build_site(config, options=None, extensions=BuildExtensions(pipeline=…, transform_tree=…, transform_page_html=…))`
  (the build pipeline seam).
- The client runtime `window.kpress` (`static/js/runtime.js`), see
  [Host Integration](kpress-operations-and-host-integration.md#host-integration).
- Name contracts in `kpress.contract`, mirroring `PUBLIC_CSS_VARIABLES` /
  `PUBLIC_CSS_CLASSES`: `PUBLIC_WIDGETS` (built-in widget ids), `PUBLIC_BEHAVIORS`
  (built-in behavior ids), `PUBLIC_RUNTIME_EVENTS` (event-bus names),
  `PUBLIC_JS_EXPORTS` (stability-pinned module exports), `PUBLIC_RENDER_REQUEST_FIELDS`
  (`KPressRenderRequest` fields in constructor order), `PUBLIC_PIPELINE_STAGES`
  (built-in stage names), and `PUBLIC_PAGE_MODEL_KEYS` (page-model block keys).

## Data Model Lifecycle

KPress normalizes inputs through these stages:

1. **Input:** Markdown or source text from a file, host request, or static source tree.
2. **DocumentInput:** typed payload with source and body text, paths, metadata, profile,
   and trust mode. `RenderOptions` carries theme, TOC, math, diagram, widget, and asset
   choices.
3. **DocumentTree:** normalized HTML with headings, TOC entries, footnotes, diagnostics,
   and a math-presence marker.
4. **RenderedDocument:** embeddable fragment with its profile, TOC, complete typed
   `AssetManifest`, diagnostics, and math-presence marker.
5. **RenderedPage:** complete HTML page with title, profile, the same resolved asset
   manifest, diagnostics, and math-presence marker.
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
- `PUBLIC_RENDER_REQUEST_FIELDS`: `KPressRenderRequest` field names in constructor
  order, pinning the dynamic host request shape
- `BUILD_MANIFEST_REQUIRED_KEYS` and `ASSET_MANIFEST_REQUIRED_KEYS`
- `OptimizerMode = Literal["none", "full"]` in `format.model`
- `PUBLIC_DATA_ATTRIBUTES`: the stable table `data-*` hooks kpress emits for downstream
  consumption. Per header-backed cell, `data-col` is the whitespace-normalized visible
  header label with case, punctuation, and Unicode preserved; `data-col-index` is its
  1-based positional identity, including duplicate and empty labels.
  `data-kpress-numeric` is set on every cell of a numeric column, decided over the whole
  column rather than per cell.
  These are renderer-agnostic seams a downstream decorator consumes to select a column
  by label or position or detect numeric columns; kpress emits them, never consumes
  them, and never imports a decorator.
  Per wrap: `data-kpress-table-scale` (value `wide`, stamped past the size cutoff),
  which kpress’s own CSS keys the wide presentation off and host stylesheets scope their
  width overrides to.
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
  stripped and each level is the entry’s structural TOC depth (one level under its
  nearest preceding shallower heading), not the raw document heading level.
  This is the published data client widgets compute from: a minimap reads `headings`;
  the settings widget reads its own `widgets.settings` config.
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
| `chevrons-up-down` | `chevrons-up-down` | TOC expand-all control (collapsed state) |
| `chevrons-down-up` | `chevrons-down-up` | TOC expand-all control (expanded state) |

One deliberate non-icon: the doc-actions widget’s “PDF” and “MD” badges are plain text
in the document sans stack, not sprite glyphs — a printer or generic file pictogram does
not say what an action yields; the format letters do.
See [Document Actions Widget](#document-actions-widget).

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

### Fragment Host Contract

Embedding applications should consume the narrower
`contract.py::PUBLIC_FRAGMENT_CSS_CLASSES` and
`contract.py::PUBLIC_FRAGMENT_CSS_VARIABLES` subsets.
These are the minimum stable seam for placing a rendered fragment inside a host shell;
other public reader hooks exist for standalone KPress customization but are not required
for an embed.

The supported fragment structure is:

- document scopes: `kpress`, `kpress-doc`, `kpress-doc-layout`,
  `kpress-content-with-toc`, `kpress-prose`, and `kpress-long-text`
- wide tabular content: `kpress-table-wrap` and `kpress-table`, with the public cell
  attributes `data-col`, `data-col-index`, and `data-kpress-numeric`
- wide figures: `kpress-figure`, `kpress-image`, and `kpress-figcaption`
- print and visibility: `kpress-print-surface`, `kpress-no-print`, and
  `kpress-print-only`

The supported fragment variables are:

- semantic document colors: `--kpress-doc-bg`, `--kpress-doc-text`,
  `--kpress-doc-muted`, `--kpress-doc-link`, `--kpress-doc-accent`,
  `--kpress-doc-border`, `--kpress-doc-code-bg`, `--kpress-doc-success`,
  `--kpress-doc-danger`, `--kpress-doc-surface-bg`, `--kpress-doc-surface-hover`, and
  `--kpress-doc-surface-selected`
- typography: `--kpress-font-body`, `--kpress-font-prose`, `--kpress-font-sans`,
  `--kpress-font-mono`, `--kpress-font-footnote`, and `--kpress-font-table`
- sizing: `--kpress-font-size-base`, the one knob the entire type ramp derives from
  (default `1rem`; every internal font size, the bullet square, and its offsets are
  `calc(base × ratio)`). Hosts set it once — preferably through the
  `--kpress-host-font-size-base` hook on `:root`, which also reaches the body-level
  overlays. The derived tier is the sanctioned divergence seam: `--kpress-font-size-h2`,
  `--kpress-font-size-h3`, `--kpress-font-size-h4`, `--kpress-font-size-large`,
  `--kpress-font-size-mono`, `--kpress-font-size-mono-small`,
  `--kpress-font-size-mono-tiny`, `--kpress-font-size-normal`,
  `--kpress-font-size-small`, `--kpress-font-size-smaller`, `--kpress-font-size-tiny`,
  `--kpress-caps-label-size`, and `--kpress-bullet-size` — override one only for a
  deliberate design departure from the derived ratio (for example aligning mono or label
  sizes with host chrome), never as the way to scale the document.
  See “Sizing policy” below.
- measure and host spacing: `--kpress-measure`, `--kpress-column-inset`,
  `--kpress-doc-gutter`, `--kpress-page-margin-inline`,
  `--kpress-page-margin-block-start`, and `--kpress-toc-toggle-clearance` (the inline
  gutter the document reserves for the floating TOC toggle in the narrow band; a host
  whose pane inset already contributes to that gutter shrinks it accordingly).
  See “Reading measure” below for what the first three mean and how they compose.
- print: `--kpress-print-page-margin`, `--kpress-print-font-size`, and
  `--kpress-print-footer`

Set these variables on the fragment’s `.kpress` scope.
A host stamps its resolved `light` or `dark` theme on `:root` or a wrapper.
Dynamic fragments omit the KPress resolver and all page-default widgets unless
explicitly requested.
Under the default `auto` asset policy, a plain fragment with no requested widgets has no
JavaScript. A rich fragment still declares only the modules needed by its rendered
features.
The host must not hide the settings widget with CSS, rebuild the table wrapper,
or reach for selectors and variables outside these pinned subsets.

**Overlay parenting.** Tooltips and footnote previews render outside the `.kpress`
subtree, and which element carries them is a placement decision rather than a detail.
A callout preview is appended inside the `.kpress-viewport` scroller and placed with
`position: absolute` in page coordinates — the on-screen placement plus the scroller’s
scroll offset — so it holds its place beside the word that opened it while the reader
scrolls, instead of hanging in the window as the text moves underneath it.
The narrow-screen sheet (`kpress-tooltip-mobile-bottom`) is the deliberate exception: it
is a bar across the bottom of the pane, not a callout beside an anchor, so it keeps
`position: fixed` on `<body>`, resolving against the non-scrolling `.kpress-frame` (the
standalone shell marks `<body>` itself as the frame).
A document that scrolls in the window rather than in a marked pane has no scroller
element to append to, so `<body>` carries both.
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
  shadow), appears only from 48rem of *pane* width (a narrow pane reads full-bleed even
  inside a wide window, which is why this is a container query and not a media query),
  and never prints. Shown or flat is a render-time setting: `RenderOptions.content_card`
  / `format.content_card`, stamped as `data-kpress-card="on|off"` on the document
  article, and the shipped default is **on**. Set the option to `false` for a flat,
  full-bleed page. Low-level fragment callers pass the same option; dynamic `render_view`
  uses the default content-card setting.

Three shared interaction primitives are documented so every component reuses them rather
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
- **Icon-button hover contract:** every icon-only control that performs an operation
  (settings gear, chooser segments, TOC drawer toggle, TOC expand-all, code copy, video
  close) hovers identically: the light hover fill (`--color-hover-bg`) plus slight text
  darkening (`--kpress-doc-text`), on the fast motion token — and **never a border
  introduced or recolored on hover**. Resting borders that exist for layout or
  legibility (the code-copy outline, the drawer toggle’s transparent border) stay
  untouched; selected/checked state uses `--color-bg-selected` + the link color, and
  state feedback (code-copy copied/error) may recolor its border — those are states, not
  hover. Enforced by `tests/test_icon_button_hover.py`, which pins the control list; a
  new icon control joins that list when added.

These primitives and tokens live in the KPress static layer deliberately: an embedding
host app consumes the same design (sharing the Lucide icon set) rather than
re-implementing it.

### Sizing Policy

All typography derives from one public base knob, `--kpress-font-size-base` (default
`1rem`): every internal font size — the size-token ramp, every heading, code, labels,
the bullet glyph, and its positional offsets — is expressed as `calc(base × ratio)`.
Ratios are design; units are the host’s choice.
No font-size rule may reference `rem` directly, because `rem` resolves against the host
page’s root font size, which an embedder does not control the way KPress does on its own
standalone pages: with a px-pinned host body, every rem-based size renders at a
browser-dependent ratio to the pinned text.
The derivations use `calc(base × ratio)` rather than bare `em` so a size means the same
thing in every context: an `em` token would resolve against each consumer’s inherited
size, silently changing ratios in nested contexts like captions and footnotes.

- **Standalone pages:** the `1rem` default resolves against the reader’s browser
  preference at the `.kpress` root, so published pages respect reader font settings.
- **Embedders** set the base once, preferably `--kpress-host-font-size-base: 17px` (or
  any length) on `:root`, which flows through every token scope including the
  body-appended overlays.
  Setting `--kpress-font-size-base` itself works too but must be declared at the
  `.kpress` scope (or deeper) with later order or higher specificity, does not reach
  body-level overlays from a wrapper scope, and (because it replaces the derivation
  chain) also overrides the print re-rooting below: use the hook if print should follow
  `--kpress-print-font-size`; redeclare the base only if the host intends to own print
  sizing too. Scaling goes through the base, never through individual sizes; the public
  ramp, label, and bullet tokens exist for *deliberate design divergence* from a derived
  ratio (a host aligning mono or label sizes with its own chrome), and stay derived from
  the base unless overridden.
- **Print** re-roots the base at `--kpress-print-font-size` inside `@media print`, so
  paper output keeps the designed ratios to the print body size regardless of the screen
  root or a host-pinned base.
- **Deliberately root-relative** (not derived from the base): container-query band
  conditions (where `var()` is not valid CSS), tooltip width caps, and page margins.
  A host that pins the base accepts that band boundaries stay root-relative.
  The reading measure is the exception and is derived from the base — see “Reading
  measure” below.
- **Contributors:** new sizes must be expressed relative to the base
  (`calc(var(--kpress-font-size-base) * ratio)`); intentionally context-relative
  `em`/`%` sizes (the summary chevron, the task-list checkbox, `sup`/`sub`) are the
  exception, not the pattern.
  The no-`rem` invariant is enforced by `devtools/public_hygiene.py` and a two-root
  real-browser regression test.

### Reading Measure

`--kpress-measure` is the width of the **text**, padding excluded.
It defaults to `calc(var(--kpress-font-size-base) * 45)`, so the column tracks the type
it holds: a host that pins `--kpress-host-font-size-base` keeps the same characters per
line at any size, where a root-relative length would hold the pixels and change the
line.

Three nested elements bound the column, each adding back the padding between it and the
text, so the text lands at the measure in every band:

| Element | Cap |
| --- | --- |
| `.kpress-doc` | measure + 2× inset + 2× gutter |
| `.kpress-doc-layout` | measure + 2× inset |
| `.kpress-long-text` | measure + 2× inset, padded by the inset |

`--kpress-column-inset` is the inline padding inside the column and varies by band
(1.5rem phone, 4rem single column, 2.5rem in the wide TOC grid); `--kpress-doc-gutter`
is the page margin outside it.
The bands reset those two on `.kpress-doc` and every cap follows.
A host setting the measure sets one value and gets one reading width; it should not
restate the caps.

Write the measure as `calc(base × N)`, not `N em`. An `em` inside a custom property
resolves at each *consuming* element, and the measure is read on three elements that do
not share a font-size, so `45em` would silently mean three different lengths.

**Characters per line.** The measure is a length, not a character count, because the
conversion depends on the face.
Measured over 507 characters of representative English prose, the average glyph advance
is 0.4335 em/char for PT Serif and 0.4039 em/char for Source Sans 3, so the 45 default
reads about 104 and 111 characters respectively.
Eight common proportional text faces span 0.392–0.434 em/char, which puts `45em` in the
104–115 character range for any of them.
Note this is the *average advance*, not the CSS `ch` unit: `ch` is the advance of “0”
and overstates a proportional face by roughly 23%, and its relation to the average
varies far more across faces (0.66–1.0) than the average itself does.

KPress ships no per-face constants, because `--kpress-host-font-prose` lets a host swap
the face and invalidate them.
A host that wants a true character count knows its own pinned face: measure that face
once and set the measure from it.

## Theme and Fonts

Theme mode values:

- `system`
- `light`
- `dark`

Standalone pages include a pre-paint bootstrap that resolves `system` using
`prefers-color-scheme`. Dynamic fragments let hosts resolve and set attributes.

**Theme scopes and the embedder contract.** CSS reads exactly one theme input:
`data-kpress-resolved-theme="light|dark"` — the resolver’s *output*. The mode
(`data-kpress-theme`) is resolver state and never keys CSS (lint-enforced).
Light and dark are keyed symmetrically at two scopes — any ancestor (`:root` or a plain
host wrapper) and the element itself — with the element winning, so a stamped element is
a coherent theme island in either direction and `color-scheme` travels in rules keyed
identically to the palette (the two cannot split).
Rendered fragments are **theme-agnostic**: they bake no theme or palette attributes, so
one render is cacheable across themes and the embedder contract is exactly:

- use `data-kpress-resolved-theme` (and optionally `data-kpress-palette`) on one chosen
  scope as the only CSS theme input;
- leave `include_theme_resolver=False` (the dynamic default), so the automatic fragment
  manifest omits `theme.js` and KPress cannot become a second root writer;
- if KPress settings controls are enabled, handle `theme:request`, apply host state, and
  emit `theme:change` with the resulting `{mode, resolved}`;
- combined palette × theme states bind fully when both attributes sit on the same scope
  element;
- the overlays still portaled to `<body>` — the mobile tooltip sheet, and every preview
  in a window-scrolled document — escape a non-`:root` wrapper scope: a wrapper-scoped
  host should stamp `:root` as well, or stamp overlays individually (overlay theme
  inheritance is tracked as `kpr-gssj`). A callout preview in a pane-scrolled document
  is appended inside the pane, so it inherits a wrapper- or pane-level stamp like the
  rest of the document.

The standalone page shell stamps `<html>` from the template plus the pre-paint
bootstrap; `theme.js` is the standalone resolver behind the same attribute.
Resolver inclusion is independent of the settings widget and configured color mode: even
a fixed `light` or `dark` standalone page with settings off includes `theme.js` by
default. Library callers that intentionally want a page shell without the resolver can
pass `RenderOptions(include_theme_resolver=False)`; `kpress.yml` does not expose that
page-level opt-out. The page’s inline pre-paint bootstrap remains in either case.

**Theme engine vs. settings widget.** These are two layers, deliberately separate (see
[Extension and Injection Model](#extension-and-injection-model)):

- **The theme engine is a headless client primitive:** `kpress.theme` and the public
  `setKpressTheme` / `initKpressTheme` exports in `theme.js` resolve `system` via
  `prefers-color-scheme`, set `data-kpress-theme` / `data-kpress-resolved-theme`,
  persist through `kpress.storage` (key `kpress.theme`), notify change listeners, and
  track OS theme changes.
  Engine *init* runs as the registered `theme` behavior at apply time.
  Standalone pages include it automatically; fragments include it only through explicit
  `include_theme_resolver=True`. Its first storage read goes through whatever adapter
  the consumer installed before `DOMContentLoaded`. The pre-paint bootstrap
  (`theme-bootstrap.js`, inlined render-blocking in `<head>`) applies persisted state
  attrs before first paint (theme, and the same pattern for the other persisted reader
  preferences (`kpress.proseFont` → `data-kpress-prose-font`, `kpress.fontSet` →
  `data-kpress-font-set`), so there is no flash regardless of which widget (if any)
  presents the controls.
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
  Theme controls live in the behavior-neutral `theme-controls.js` layer and emit
  `theme:request`; the standalone resolver handles that event, while an embedding host
  may handle the same request without loading the resolver.
  A host that wants a different presentation turns the widget off and uses the same
  request/change event contract.
  The resolver and gear are independently optional.

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
appears in the host unless the host explicitly enables and mounts the settings widget.
The host owns its own pane background and drives the embedded document’s theme by
setting `data-kpress-resolved-theme`. Automatic fragment manifests omit the resolver;
explicit settings controls request `system | light | dark` through `theme:request`, and
the host announces applied state through `theme:change`. See
[Host Integration](kpress-operations-and-host-integration.md#host-integration).

### Math Text Face

The canonical
[font and math loading architecture](project/architecture/arch-2026-09-08-font-and-math-loading.md)
describes publication preparation, runtime readiness, hydration, failure, and print.
This section retains the face construction and metric details.

Prose is set in PT Serif and mathematics in KaTeX, whose faces derive from Computer
Modern; the two disagree in x-height and stroke weight, and no size token reconciles
both. The math text face draws the Latin letters and digits inside mathematics from the
reading face instead, and gives KaTeX the metrics to lay them out.
It is on by default.

**What is drawn from what.** Latin letters (`U+0041–005A`, `U+0061–007A`) and digits
(`U+0030–0039`) inside KaTeX come from the reading face, in whatever weight and style
the expression asks for: `\mathbf`, `\mathit`, `\boldsymbol`, `\text`, `\mathrm`,
operator names, and plain digits.
Operators, relations, delimiters, big operators, radicals, accents, and the
calligraphic, blackboard and fraktur alphabets stay in the KaTeX faces on KaTeX’s own
math axis — PT Serif centres its operators 0.094em above that axis and has no `≤`, so
operators must not move.
KaTeX’s Greek stays KaTeX’s, scaled to the reading face: lowercase to its x-height,
capitals to its cap height.

**The composite family.** The swap is one CSS family, `KPress Math Text`, declared in
`katex/katex-text-face.css` and loaded as part of the lazy math closure, so a document
with no math still loads none of it.
The family has four style and weight slots, each two `@font-face` rules sharing
descriptors and carrying disjoint `unicode-range`s: the reading face over
`U+0030–0039, U+0041–005A, U+0061–007A`, and the KaTeX face over the Greek range with a
`size-adjust`. Everything else is claimed by no face: CSS Fonts 4 sends a code point no
face of a composite covers to the next family in the stack, and every rule names the
KaTeX face its slot replaces right after the composite, so operators, punctuation and
every other script are drawn by the face they always were, without a second declaration
of it.

| Slot | Reading face | KaTeX face for Greek, scaled, and next in the stack |
| --- | --- | --- |
| normal 400 | PT Serif Regular | KaTeX_Main-Regular |
| italic 400 | PT Serif Italic | KaTeX_Math-Italic |
| normal 700 | PT Serif Bold | KaTeX_Main-Bold |
| italic 700 | PT Serif Bold Italic | KaTeX_Math-BoldItalic |

The ranges are disjoint rather than overlaid onto `KaTeX_Main` so that the result does
not depend on which stylesheet is linked last — KPress links `katex.min.css` after its
own, and a host that inlines everything may concatenate in the other order.

**The sans composite.** A second family, `KPress Math Text Sans`, draws the same ranges
from Source Sans 3 wherever the words around the mathematics are sans: the document’s
sans roles (`.kpress-figcaption`, `.kpress-footnotes`, `.kpress-table`, `.sans-text`,
`.description`, `.key-claims`, `.summary`, `.concepts`, `.claim`, `.para-caption`,
`.tab-button`, `.kpress-tab-button`, `details`) and the reader’s sans reading face
(`data-kpress-prose-font="sans"`). The mathematics in a footnote is then set in the
footnote’s own face, which the size token beside it (`--kpress-katex-size-sans`, `1em`)
has always assumed. Under the sans reading face the whole document is sans and the
composite follows it, headings included, since the alternative there is a serif
expression in a sans paragraph.

**Headings and the TOC are left out, for two unrelated reasons.** Both are sans roles,
so it would be natural to read the exclusion as one decision; it is two, and neither is
the “both are set at the sans bold weight” reason this section gave until the sans
composite was reviewed.
Neither is set at that weight.

A heading is a weight step away from any table this feature can build.
The shared `.kpress-prose h1`–`h6` rule in `css/document.css` does declare
`--kpress-font-weight-sans-bold` (650), but every level overrides it: `h3` takes
`--kpress-font-weight-sans-medium` (550) and `h4` takes 540, while `h1`, `h2`, `h5` and
`h6` redeclare `--kpress-font-prose` and are not sans at all (`h2` is serif italic 400).
So the sans headings that exist are at 550 and 540, and a table built at 400 is no truer
of those than the 650 table would have been.
Either way a heading’s mathematics would sit a step off its own words, and the
pinned-weight design above is exactly what makes that unfixable per heading: KaTeX picks
the table from the TeX, not from the CSS, so a third pair of slots at the heading
weights would be the honest fix and is not in scope here.

The TOC is excluded for a reason that has nothing to do with weight: it carries no
mathematics to draw.
`_plain_inline_text` in `format/markdown.py` builds `Heading.title` from the `text` and
`code_inline` children of the heading’s inline token alone, so a `math_inline` token is
dropped before the title exists, and `_render_toc` in `format/render.py` HTML-escapes
what is left. A heading written `## Bound with $x$ inside` reaches the TOC with the
expression simply absent from its title, so no `.katex` node is ever built inside the
TOC for any rule to match.
That exclusion is a statement about the renderer, not about the cascade, and it holds
however the scope is spelled.

Same four slots, but each declares a **single** `font-weight` rather than the variable
face’s whole axis, and its metric table is built at that same weight — 410 for the
regular slots, `--kpress-font-weight-sans-bold` (650) for the bold ones, which is what
`.mathbf` and `.boldsymbol` ask for instead of upstream’s 700. A KaTeX metric table
describes one face *and one weight*, and Source Sans’s Latin advances move a median 7.1%
across the 370–700 axis while its ink heights move 0.035 em at most; CSS Fonts 4 clamps
a variable face to the range its `@font-face` declares, so a single value draws the
weight the table was built at whatever the context asks for.
The numeric `--kpress-font-weight-sans-regular` in `style-tokens.css` is the one
adjustable input for regular sans prose and mathematics.
It accepts 200–500; heavier regular requests would select bold KaTeX fallback glyphs.
After changing it, run `python -m devtools.instance_sans` and then
`python -m devtools.katex_text_metrics`. They generate the print instances and asset
manifest, composite descriptors, Greek scales, metric tables, private CSS weight, and
explicit font warmup requests.
The CSS overrides KaTeX’s shorthand reset with the generated weight.
`--kpress-font-weight-sans-light` aliases the regular token; medium and bold retain
their own intentional weights.
A host override of a prose token alone cannot change the fixed composite metrics.

Under `@media print`, and declared last, the static `KPress Print Sans` instances at the
same two weights are layered over the same ranges, so a printed page embeds a font
rather than the Type3 outline paths Chromium writes for a variable face away from its
default position (the reason [Print Sans Faces](#print-sans-faces) exists).
The two agree exactly: instancing the variable face at 410 and 650 reproduces every
Latin advance of the shipped instance, so one metric table is true of both — which is
also why the generator measures the sans slots from those instance files.

Operators stay in the KaTeX faces here as well, for the same three reasons and by the
same measurements: Source Sans centres `+ − =` 0.080 em above KaTeX’s math axis, sets
`+` on 0.497 em against KaTeX’s 0.778 em, and has no `≤` or `≥`. The measurements are in
[Sans Math Face Research](project/research/research-2026-09-07-sans-math-face.md).

**What `size-adjust` does not reach: accents over Greek.** No accent code point falls
inside any range either composite declares.
The vendored bundle draws `\hat` from `^` (U+005E), `\tilde` from `~` (U+007E), `\bar`
from U+02C9, `\ddot` from U+00A8, `\vec` from U+20D7 and the rest from U+02C7–U+02DA,
while the reading-face slots claim only `U+0030–0039, U+0041–005A, U+0061–007A` and the
Greek slots `U+0391–03A9` upright and `U+0370–03FF` italic.
Every accent is therefore drawn from the KaTeX face at scale 1.0, and
`devtools/katex_text_metrics.py` carries its metric row over from KaTeX unchanged -- the
generator scales `UPRIGHT_GREEK` and `ITALIC_GREEK` and nothing else.

Over a Latin base that is the intended result, since the base is the reading face at 1.0
and the accent is laid out from the row it is drawn from.
Over Greek it leaves a residual, because the base is scaled and the accent is not.
The accent is still *positioned* correctly -- KaTeX takes the placement from the base’s
own scaled width and skew -- but it is drawn for a base of another size: in a sans
context `\hat{\alpha}` gets a circumflex 9.3% narrow for its base (1/1.102) and
`\hat{\Gamma}` one 4.2% wide (1/0.960); in a serif context the italic slot’s larger
factor makes it worse at 13.0% narrow (1/1.15), with the upright slot 2.4% narrow
(1/1.025). The bold slots land within a couple of points of these.
It is sub-pixel at caption size, it is inherent to scaling one face inside another, and
it predates the sans composite, so it is a residual rather than a regression.

Widening each Greek slot’s `unicode-range` to cover the accent code points was
considered and not taken.
One accent glyph serves both kinds of base, and `\hat{x}` is the far more common
construct, so scaling U+005E would make the common case wrong to repair the rare one --
a judgement, not a measurement, but a one-sided one.
The mechanical objection is firmer: the scaling would have to reach the metric table
too, or the accent would be drawn at one size and laid out from another, which is the
single state this design forbids; and there is one table row per code point, so it
cannot be scaled for the Greek use and left alone for the Latin one.
A `unicode-range` cannot condition on what a glyph sits over.
The related accent question -- that the generator keeps KaTeX’s `skew` for the swapped
italic letters -- is in the plan’s open questions.

**Which sans roles can carry mathematics today.** The roles above are where the sans
composite applies; they are not all reachable from Markdown, and the gap matters to
anyone planning to judge the feature on a real page.
Rendering each container form through `format/markdown.py` and looking for a
`kpress-math` node gives four results:

- **A Markdown image caption never produces mathematics.** `_render_paragraph_close`
  emits `<figcaption class="kpress-figcaption">{escape(caption)}</figcaption>`, so
  `![caption with $x$](img.png)` reaches the page with `$x$` as literal text.
  There is no route from Markdown caption syntax to a rendered expression, and the
  branch’s own test file records this.
- **The natural inline spellings of the other containers do not work either.** A
  one-line `<figcaption class="kpress-figcaption">$x$</figcaption>`,
  `<p class="para-caption">$x$</p>` or `<details><summary>$x$</summary>` leaves `$x$`
  literal: markdown-it treats a line opening with a block-level HTML tag as an HTML
  block and copies it through to the next blank line without running the inline parser
  over it.
- **The raw-HTML block form does work.** The same containers written with blank lines
  around their content render the expression, and so does an inline-level wrapper such
  as `<span class="sans-text">$x$</span>`, which stays inside a paragraph and is parsed
  inline. Blank lines, not newlines, are what decides it.
- **Tables and footnotes need none of this.** A `$x$` in a Markdown table cell or a
  footnote definition renders from ordinary Markdown.

So tables and footnotes are the roles the sans composite pays off in today, and caption
mathematics is reachable only in the raw-HTML block form.

**Metrics.** `katex/katex-text-metrics.js` defines `globalThis.kpressKatexTextMetrics`:
complete KaTeX metric tables keyed by face name, generated by
`devtools/katex_text_metrics.py` from the vendored KaTeX bundle and the reading face’s
own woff2 files. The serif set is the object’s own face keys; the sans set is the same
six faces nested under `sans`, with its own `scale`. The original six tables are also
nested under `katex`, so a per-node opt-out can restore stock layout.
`katex-math-runtime.js` applies them through `katex.__setFontMetrics(face, table)`
before the first render, and chooses **per rendered node**: the tables are a KaTeX
singleton, so the render loop installs the set matching the node’s context, renders, and
leaves the serif set installed for whatever runs after it.
The same call stamps `data-kpress-math-face="sans"` on the node when the sans set is the
one it installed, and that mark is what the stylesheet draws the sans composite on — so
which face draws and which table lays out come out of one decision.
`SANS_CONTEXT` in `katex-math-runtime.js` is therefore the only place the sans roles are
listed; the stylesheet names none of them, which `tests/test_sans_math_face_css.py`
asserts in both directions.
The list lived in both languages until the composite was reviewed, seven copies in the
CSS for the roles and seven more for the reading face, and a role dropped from any one
of them drew Source Sans over PT Serif’s numbers in that role alone with the whole suite
green. Both sets are required: sans faces without sans tables would draw Source Sans and
lay out PT Serif inside every caption, so a missing `sans` key stamps the same opt-out
on `<html>` as missing tables anywhere else.
The tables are not a refinement of the CSS swap but a condition of it: KaTeX lays out
from its own `[depth, height, italic, skew, width]` table, so swapping the drawn glyphs
alone leaves fraction boxes, script positions and italic corrections computed for
Computer Modern. The tables are complete because KaTeX exports a setter and no getter.

**What the sans half costs, and when.** Both sets live in the one asset, so every page
with any mathematics links the sans tables whether or not it has mathematics in a sans
role. Measured against the serif-only asset: `katex-text-metrics.js` went from 34,960 B
to 69,455 B, and from 6,032 B to 11,336 B gzipped, so +5,304 B gzipped is the sans
tables. The stylesheet’s growth is nearly free beside that -- most of what
`katex-text-face.css` gained is the comments that explain the mechanism, and with
comments stripped the CSS delta compresses to under half a kilobyte.
Uncompressed the stylesheet is the larger file, which is why a byte count taken off disk
overstates it. The whole first-visit cost is therefore on the order of 8–9 KB gzipped,
and it is a first-visit cost only: both files are linked and cacheable, no `@font-face`
URL is new, and the rendered HTML is byte-identical whether the sans half is there or
not. Across a multi-page site with a warm cache it is paid once.

Making it lazy is a follow-up rather than something this design does, and three things
would have to move together.
The metrics asset is a single file with the sans set nested under `sans`, so there is
nothing to link separately.
The document model carries only `has_math` -- set in `format/markdown.py`, carried
through `format/model.py`, read in `format/render.py` to emit the math closure -- and no
notion of a sans role, so nothing upstream of the page knows whether the sans half is
wanted. And `applyTextMetrics` in `katex-math-runtime.js` requires both sets, stamping
the page’s opt-out when either is missing; that is the guard that keeps the drawn face
and the metric table together, so it cannot simply be relaxed.
Splitting the asset means giving all three a `has_sans_math` to follow.

**First visible mathematics.** The composite families use separate font files, and an
inlined font still decodes lazily.
The shared `katex-math-runtime.js` lays out each formula immediately with the selected
metric tables, then waits for the glyph fonts its HTML actually uses.
Every render uses the same boundary, including a host’s early resize or input callbacks.

The runtime renders each formula with visibility suppressed, reads the font combinations
and characters in its KaTeX HTML, and loads the faces those glyphs require before
revealing it. Large operators, delimiters and AMS symbols are therefore covered without
eagerly downloading every KaTeX family.
Source Sans and PT Serif metrics are selected immediately before rendering and restored
afterwards; an older pending request cannot overwrite a newer formula on the same node.
`ready()` remains an explicit batch warmup API; neither native enhancement nor an
ordinary render waits for unused families, styles or weights.

A host that needs exact space before its initial scripts execute can prepare measured
KaTeX markup during publication and explicitly `hydrate()` it.
Matching source, display mode and resolved font profile preserve the prepared DOM; a
changed request or unavailable composite declaration causes normal rendering.
The host owns the geometry reservations and other rendering options.
This keeps browser measurement optional for hosts that need it, without adding a browser
dependency to ordinary KPress generation.

The head bootstrap also suppresses the native MathML fallback during enhancement.
Otherwise a reader would first see the browser’s own math fonts, even if the first KaTeX
formula used its final fonts.
Space is retained, and completed formulas keep semantic MathML for accessibility.
JavaScript-disabled pages continue to show MathML. `complete()` releases the pending
state after a batch, and a three-second watchdog releases it if enhancement never runs.

Preparation is bounded to three seconds per request.
If a face required by a rendered formula still fails or times out, native KPress keeps
the semantic MathML rather than showing fallback glyphs on the unavailable face’s metric
table. Host rendering rejects so the host can show its own text fallback.
Failure of an unused warmup face does not discard an otherwise complete formula.
If a composite family has no registered declarations, the runtime selects stock KaTeX
families and their retained original metric tables for the affected formula.
It checks declaration presence rather than load status, so a missing family is distinct
from a failed unused weight.
See [Rendering Mathematics in a Host](math-rendering-api.md) for the public API and
readiness results.

**Original warmup measurement.** Warming Main, Math and the composite slots fetched the
whole set before the first formula, whatever the page drew.
On a `\sum … \int` fixture with no bold or italic constructs, that was 11 requests and
252,828 B against the pre-fix build’s 5 and 117,432 B — six more requests and 135,396 B,
a little over double — and 4 requests and 76,692 B more in `math_text_font: katex`. Most
of it is shared with the prose faces or the composite, but `KaTeX_Main-Italic` (17,288
B) and `KaTeX_Main-BoldItalic` (17,080 B) are drawn by nothing else and are fresh on
every math page in either mode.
That earlier warmup added about 12ms over loopback and put the transfer before the first
formula.
The current render path requests the actual glyphs instead, including `\mathbf`,
`\mathit` and `\boldsymbol` when they occur.
These figures describe the earlier implementation, not a current performance result.
`kpr-hhdc` (composite subsets) addresses the font bytes separately.

The optional `ready()` warmup asks for the two kinds of faces differently.
The KaTeX faces come from the pinned bundle, which is the only thing that declares them,
so `ready()` takes every face of those two families off `document.fonts` and calls
`FontFace.load()` on it: the bundle’s four and two rules are the complete list, all of
them are wanted, and naming each face leaves no font matching between the script and
faces the page already holds — which also makes the set the wait covers exact rather
than implicit, so the record below can say which face every request was for.
The composite is asked for by description instead (`700 1em 'KPress Math Text'` and the
other three slots), with a sample string (`a1αΩ`) that reaches both faces of every slot,
since `document.fonts.load` loads a face only for a code point its `unicode-range`
covers and the upright slots carry the Greek capitals alone.
That runs the same matching the renderer runs, which is what a host that declares its
own `KPress Math Text` rules needs: its faces are fetched and the rules it replaced are
not. Loading the family face by face would instead pull KPress’s PT Serif files onto a
page that never draws them — the same objection as the preload hints below.

What the wait asked for and what came back is left on `globalThis.kpressMathFaceWait`:
one entry per request, in order, each `{ request, outcome, faces, detail }`, where
`outcome` is `loaded`, `empty` (matched no face, so it waited on nothing), `error` (with
the reason in `detail`) or `pending` (the deadline won).
Nothing in the page reads it; it is where mathematics that still repaints is diagnosed.
The browser tests inspect glyph readiness at each formula’s first visible frame,
including formulas inserted into the DOM while hidden.
The wait record is a diagnostic hook; the rendering methods themselves are pinned in
`kpress.contract.PUBLIC_MATH_RUNTIME_METHODS`. The composite carries
`font-display: block`, like the prose faces and unlike the KaTeX bundle’s `swap`, for
the case the wait does not cover: a slot that is somehow still not ready hides its
glyphs for the block period rather than painting them twice.
A browser without `document.fonts` renders synchronously and reports the loading API as
unavailable.

No `<link rel="preload" as="font">` hints go with this.
Preload would start the fetches earlier than `DOMContentLoaded`, which is the one thing
the wait cannot do, but it has to name the font URLs in the page shell, a second copy of
the list `katex-text-face.css` already owns, and it would have to be gated on the
document containing math so that documents without any do not fetch the closure the lazy
emission exists to avoid.
Worse for the contract below: a host that declares its own `KPress Math Text` faces
replaces the `@font-face` rules but not the shell’s hints, so the hints would fetch
KPress’s PT Serif files its pages never draw from.
A host that wants the earlier start can emit its own hints for the faces its documents
actually use.

**Size.** `--kpress-katex-size-prose` is `1em` when the feature is on — with the letters
in the reading face, inline math is the prose size — and `1.05em` when it is off, the
lift that compensated for Computer Modern’s smaller x-height.
`--kpress-katex-size-display` is `1em` as well when the feature is on, since TeX sets a
displayed equation at the text size and the 1.1em lift read as a size jump once the
letters were the reading face; `--kpress-katex-size-sans` is unchanged.

**The option.** `MathTextFont` is `"prose" | "katex"`; `RenderOptions.math_text_font`
(`format.math_text_font`) defaults to `prose` and is stamped as `data-kpress-math-text`
on `<html>` by the standalone page shell.
Fragments bake no attribute, as with theme and palette, and the CSS reads the absence of
the attribute as `prose`, so an embedded fragment gets the feature and a host that wants
KaTeX’s faces stamps `data-kpress-math-text="katex"` on its own root.
The attribute is independent of `data-kpress-prose-font`, which selects between the two
composites rather than turning the feature on or off: a reader switching the reading
face to sans gets `KPress Math Text Sans` throughout, and one who opts out of the math
text face gets KaTeX’s own faces either way.
The feature rules are scoped positively, to a `.kpress` that has not opted out, so an
opted-out wrapper keeps KaTeX’s own rules and the `1.05em` token exactly.
There are three ways out — `data-kpress-math-text="katex"`, the wrapper’s
`data-kpress-fonts="system"`, and the reader’s persisted `data-kpress-font-set="system"`
(both system modes load no reading face, so there would be nothing to draw the letters
from) — and each is honoured **on the element it is stamped on and on any ancestor**.
`katex-math-runtime.js` reads them with `closest()`, which matches the element itself,
so the stylesheet lists each one twice, bare and as an ancestor: a scope that admitted
one placement the script refused would draw the composite over KaTeX’s own metrics, the
one state this design forbids.
The metrics follow the same three conditions.
KaTeX keeps one table per face, so the runtime installs the selected tables immediately
before each synchronous render and restores the serif default afterwards.
The original tables retained under `katex` support pages that mix opted-in and opted-out
nodes. When a wrapper wants the face but the tables cannot be applied,
`katex-math-runtime.js` stamps the opt-out on `<html>` and says so on the console, so
the faces are turned off with the metrics rather than drawn without them.
`\mathit` follows `KaTeX_Main`, the face it replaces, after the composite; its Greek is
drawn by the italic slot’s scaled `KaTeX_Math-Italic` face, so the generator copies
those rows from the `Math-Italic` table — not from `Main-Italic`, whose advances and
accent skews belong to a face this slot never draws — and scales them by that face’s
factor.
`\textrm` and `\text` take the family only: KaTeX emits one `.mord.textrm.textit`
leaf for `\textrm{\textit{x}}` and lays it out from the italic table, and upstream
leaves `.textrm` without a `font-style` precisely so that nesting still resolves to
italic. Pinning the upright slot there would draw one face over another’s metrics;
`.mainrm`, which upstream does pin, keeps its pin.
Browsers without `size-adjust` (before Chrome 92, Firefox 92 and Safari 17) draw the
Greek unscaled while laying it out scaled; the scope needs `:not()` with a selector list
(Chrome 88, Firefox 84, Safari 9) and `:is()` (Chrome 88, Firefox 88, Safari 14).

**Live preferences and overlays.** Two things outlive the first render, and both have to
keep the drawn face and the metric tables together.

- **Both of the reader’s font controls** move this feature, and neither can finish the
  move on its own. The CSS flips instantly, but the metric tables were handed to KaTeX
  once, at load, through a setter with no getter, over TeX that is gone as soon as it
  has been typeset — so they cannot be swapped in place.
  The **font-set** chooser turns the face on and off; the **reading-face** chooser
  selects between the two composites’ table sets, because
  `[data-kpress-prose-font="sans"]` is in the sans-context list the runtime picks a set
  from. Left un-reloaded, a reading-face switch draws every expression on the page in one
  face over boxes laid out for the other: measured at 3.9% on an italic `s`, 6.8% on a
  `2` and 14.4% on `\mathbf{D}`. So both persist the choice and reload, and
  `theme-bootstrap.js` stamps it on `<html>` before first paint, so the page returns
  whole in the new mode.
  The reload is taken only where it buys something: a page with no typeset math, or one
  where the text face is off page-wide, switches in place.
  A host that stamps `data-kpress-font-set` or `data-kpress-prose-font` through its own
  control owns the same reload.
  A host uses `globalThis.kpressMathText.render()` to select tables and await fonts on
  every render; see [Rendering Mathematics in a Host](math-rendering-api.md).
- **Footnote and section previews** are clones of already-rendered math that
  `tooltips.js` mounts on the viewport pane or the body, outside every `.kpress`, so the
  scoped rules above would stop applying to them and the overlay would draw KaTeX’s own
  faces over boxes measured for the reading face.
  The overlay therefore carries the originating wrapper’s resolved mode as
  `data-kpress-math-text`, and both the composite scope in `katex-text-face.css` and the
  `--kpress-katex-size-*` consumers in `components.css` admit `.kpress-tooltip`
  alongside `.kpress`. Which composite it admits is decided by the clone’s source rather
  than by the overlay’s position: the footnote preview is the only preview kind that
  carries rendered math (the others are escaped text), and a footnote is a sans role in
  every mode, so `.kpress-tooltip-footnote` takes `KPress Math Text Sans`. This is the
  one place the two engines are decoupled — nothing re-renders in an overlay, so the
  per-node table selection never reaches it — and the cascade alone keeps the drawn face
  and the metrics the clone was laid out from together.

**A host with another reading face.** The face is a contract, tuned for PT Serif and
open to another. A host that pins its own reading face satisfies it in two places:
declare its own `KPress Math Text` faces after KPress’s stylesheet — CSS Fonts 4 checks
the last-defined face first, so the host’s faces win for the ranges they declare and
KPress’s KaTeX fallbacks keep the rest — and ship its own
`globalThis.kpressKatexTextMetrics`, produced by the same generator against its own face
files, loaded before `katex-math-runtime.js`. Faces without matching metrics leave KaTeX
laying out Computer Modern boxes around the host’s glyphs, which is worse than not
swapping at all. A host that also pins its own sans does the same for
`KPress Math Text Sans` and the generator’s `sans` set; a host that pins only the serif
leaves the sans composite alone and keeps Source Sans in the sans roles.
See [Host Integration](kpress-operations-and-host-integration.md#host-integration) for
the inlining obligations.

### Print Sans Faces

On screen the sans role is drawn from one variable face, `Source Sans 3 Variable`, at
whatever weight the context asks for.
On paper it is drawn from a set of static instances of that face, declared as the family
`KPress Print Sans`, which the print stylesheet puts ahead of the variable face.
The screen is unaffected; the whole change lives under `@media print`.

**Why.** Chromium’s PDF writer cannot embed a variable font at any position but its
default, so every glyph of the variable face in a printed page is written as a Type3
outline path instead of set in an embedded font.
The outlines carry the right weight: a caption `h` at weight 410 measures a 0.083em stem
in the PDF and 0.083em on screen, against 0.030em for the ExtraLight default instance.
But a viewer that smooths text drawn through the font machinery has no font to smooth
and leaves the paths alone, so the sans reads a step lighter than the serif and the
mathematics beside it.
Measured with Quartz, the engine behind Preview, on one 12pt line, glyph `h`, as the
fraction of the glyph box covered in ink, with font smoothing off then on.
Weight 410 is what the measurement happened to be taken at, a weight a host asks for
rather than one KPress does; the effect is Type3 against embedded, not that weight, and
a 410 request lands on the 400 instance:

| How the glyph reaches the PDF | 3 px/pt | 2 px/pt |
| --- | --- | --- |
| Sans at 410, Type3 outline paths | 0.379 → 0.379 | 0.365 → 0.365 |
| Sans at 410, static instance, embedded | 0.376 → 0.395 | 0.362 → 0.422 |
| KaTeX_Main, embedded | 0.275 → 0.318 | 0.273 → 0.327 |

A static instance embeds like any other font and gains the same ink the serif and the
mathematics gain. MuPDF, which does not smooth, agrees with Quartz within 1% on the
smoothing-off column of all three rows, so the difference is the smoothing and not the
outlines. The measurements are recorded in
[Print Sans Faces Research](project/research/research-2026-09-07-print-sans-faces.md).

**The family split.** The static set is the family `KPress Print Sans` and the variable
face is `Source Sans 3 Variable`. The static faces are modified versions of Source Sans
3 — instanced at one weight, with the variation tables removed — and the OFL they ship
under reserves the name “Source” for the original, so a derived font distributed under
that name would need Adobe’s permission.
A name of KPress’s own is the alternative the license names, and the derived faces keep
Adobe’s copyright and the OFL notice in their name tables (see `NOTICE.md`). Distinct
names also mean the two families never share a weight range, so font matching never has
to break a tie between them: under print the static family is first and answers every
request, since a weight the set does not carry is matched to the nearest instance inside
`KPress Print Sans` rather than passed on to the next family.
The variable face stays behind it for the case where the family cannot answer at all, a
build that ships without the instances, which is the behavior before this feature.

**The set.** Six weights (370, 400, 410, 550, 600, 650) in normal and italic, twelve
files of about 15KB, generated from the vendored variable faces by
`devtools/instance_sans.py` into `static/fonts/` together with the stylesheet
`static/css/print-fonts.css` that declares them.
Both are generated files; `python -m devtools.instance_sans --check` verifies the
shipped bytes and runs in both `make lint` and `make lint-check`, the second of which is
what CI runs. The set includes the regular, medium and bold tokens (410, 550, 650), the
footnote controls’ 600, and the existing 370/400 instances for deliberately lighter
typography. The two sans-mode headings ask for 380 and 440, which CSS weight matching
lands on 370 and 410; `.kpress-prose h4`’s 540 lands on 550.

A 700 pair shipped until 2026-09-07, on the belief that bold asked for it.
It does not: `.kpress b, .kpress strong` sets the bold token, so a UA-default `bold`
never reaches a sans element inside `.kpress`, and the only `font-weight: 700` rules
left in the stylesheets are `.kpress-prose h5` (a prose family) and the syntax
highlighting (a mono family), neither of which can resolve to `KPress Print Sans`.
Measured in Chromium across both media and both reading-font modes, no sans element
resolves above 650. The pair was 30,912 bytes for nothing, and a host that raises a
weight token past 650 lands on 650 by the fallback rule below.
`tests/test_print_sans_faces.py` pins every landing place and fails if a stylesheet asks
for a weight the set does not account for, and
`tests/test_playwright_print_sans_face.py` measures the same table in Chromium.
The `@font-face` rules sit inside `@media print`, so a reader on screen never downloads
one, and `print-fonts.css` is registered right after `print.css` in
`DEFAULT_CSS_ASSETS`.

The instances copy the variable faces’ `unicode-range` verbatim, so their coverage is
the same Latin subset and no glyph is drawn from a static face that the variable one
would have passed down the stack.
The benefit is bounded by that subset: a code point outside it — Greek, CJK — matches
neither family, falls through to the platform font, and still prints as Type3. Improving
that means widening the vendored subset, not the instancing.

**Export readiness.** A face declared inside `@media print` starts loading only when
print layout asks for it, so an export that switches to print media and prints at once
draws the page before the instances arrive.
[`format/pdf.py`](../src/kpress/format/pdf.py) forces print layout, waits for
`document.fonts.ready`, and then asks for the families the `@page` margin boxes name
(`--kpress-font-sans` and `--kpress-font-prose`) before calling `page.pdf()`: a margin
box sits outside the document tree, so its face never enters `document.fonts.ready` on
its own and the footer would otherwise not print at all.
`tests/test_playwright_print_pdf_fonts.py` pins both cases through the public
`render_pdf`, one with the instances held back on the wire and one on a page where the
footer is the only 400-weight sans, and asserts the exported PDF holds no Type3 font.

The faces carry `font-display: swap` for the print paths that cannot wait: a browser’s
own Print dialog, or a host that goes straight to `page.pdf()`. Print layout gets one
chance to draw, and under `block` the text it has not got a face for is drawn as nothing
at all — measured, the sans headings and the footer both vanish from such a PDF. Under
`swap` the worst case is the fallback the stack already names, which is the variable
face and its outline paths: a page that reads correctly and prints a step light, rather
than a page with holes in it.
There is no flash to trade against, since nothing on screen uses these rules.

**The host hooks.** `--kpress-host-font-sans-print` is the print-only sans stack, ahead
of `--kpress-host-font-sans` in the print token: a host that ships instances of its own
points at them there.
A host that sets only the screen hook, `--kpress-host-font-sans`, has named a family for
both media and gets it in both — the static set is KPress’s default, not an override of
a host’s deliberate choice — so such a host prints whatever its own family prints,
outline paths included if it is a variable webfont.
That is the case to know about, and
[Host Integration](kpress-operations-and-host-integration.md#print-sans-faces-and-host-weights)
states the obligation, along with what a host that overrides the sans weight tokens
needs.

### Quotation Marks

Quotation marks and apostrophes come from **KPress Quotes**, a six-glyph subset of
Source Serif 4 that KPress ships.
It leads `--kpress-font-prose` over `U+0022`, `U+0027`, `U+2018`, `U+2019`, `U+201C` and
`U+201D`, and every other character passes down to PT Serif.

**The history, as far as the record goes.** The borrowing was a family `LocalPunct`
whose `src` was `local("Georgia")` and whose `unicode-range` was those same six code
points, placed at the head of the prose stack.
It is present in the first commit this repository has, the 2026-06-10 extraction
`5f2d466`, and so is PT Serif: the prose token there already reads
`"LocalPunct", "PT Serif", Georgia, …`. The two arrive together, so nothing here shows
Georgia being replaced as the reading face and the marks then being kept back.
What the record shows is narrower and still worth recovering: reaching outside the
document for six glyphs was a deliberate part of the design from the beginning, and its
reason was never written down.
It was nearly lost, because from the outside the borrowing looks like an oversight.

One document with three answers is what it cost.
A document’s punctuation came from Georgia when the reader had Georgia, from PT Serif
when they did not, and from PT Serif on paper either way, since a `local()` face cannot
be embedded in a PDF.

The one text that pairs a Georgia prose stack with `LocalPunct` is a token table in the
extraction commit’s own copy of this document, listing
`--kpress-font-prose: ui-serif, Georgia, serif` beside
`--kpress-font-punctuation: LocalPunct`. The 2026-07-13 consolidation `7b09584` removed
it. It contradicted the shipped stylesheet on the day it was written, so it is evidence
of an earlier default somewhere behind this repository, not of the order things happened
in.

**What it was buying.** PT Serif draws these six glyphs badly, and the fault is
measurable. In Chromium at 18px, `measureText` on the four curly marks:

| Face | `“` `”` width | `‘` `’` width | Opening pair, ink above baseline | Closing pair |
| --- | --- | --- | --- | --- |
| PT Serif | 8.53px | 5.26px | 14.83px | 12.58px |
| Georgia | 7.38px | 4.08px | 13.41px | 13.44px |
| KPress Quotes | 7.92px | 4.05px | 13.34px | 13.34px |

Two things are wrong with the PT Serif row.
Its opening pair hangs 2.25px above its closing pair, so a quotation does not sit level
with the marks that close it, and its doubles are 16% wider than Georgia’s, which makes
them loud in a line of text.
Georgia’s open and close are level to within 0.03px. PT Serif’s opening single quote
also reads as a near-vertical tapered tick rather than a comma.
The preference for Georgia was real, and it was right.

**Why it is shipped rather than borrowed.** The rule is that every glyph in a KPress
document comes from a face KPress ships, on screen and in print
([Vendored Fonts](../src/kpress/format/static/fonts/README.md)). Borrowing broke it in
the way that matters most: a reader without Georgia saw the marks the borrowing existed
to avoid, and a printed page always did.
So the marks are shipped instead.
Source Serif 4 is the companion of the Source Sans 3 face KPress already vendors, and
its marks are level to 0.00px and only 7% wider than Georgia’s. Taking six glyphs of it
costs 724 bytes, which is why the whole 20 KB face is not vendored:
`devtools/subset_quotes.py` reads the upstream `@fontsource/source-serif-4` file from
outside the repository, subsets it to those six code points, renames the result to the
family `KPress Quotes`, and writes `static/fonts/kpress-quotes.woff2`.
`python -m devtools.subset_quotes --check` runs in `make lint`, comparing the shipped
bytes against a fresh subset when the source is at hand and against a pinned digest when
it is not; provenance and both hashes are in the fonts README.

**The name.** The subset is the family `KPress Quotes`, not `Source Serif 4`. It is a
modified version of an OFL face, and that license reserves the upstream name for the
original, so shipping it under Adobe’s name would need Adobe’s permission, exactly as
for the `KPress Print Sans` instances above.
Adobe’s copyright notice, version string and the OFL URL stay in the subset’s name
table. The rename also settles font matching, since the generated family never shares a
code-point range with the face it came from.

Print needs nothing special.
A static face embeds like any other, so `KPressQuotes-Regular` appears in the exported
PDF’s font list beside `PTSerif-Regular`; `tests/test_playwright_print_pdf_fonts.py`
pins that, and `tests/test_playwright_quote_face.py` pins that the marks resolve to the
face on screen and under print media while the letters beside them stay PT Serif.

**The host hook.** `--kpress-font-punctuation` names the family that answers those six
code points, and it is the first entry in the prose stack.
`--kpress-host-font-punctuation` points it somewhere else: another family for different
marks, or the reading face itself to give the marks back to PT Serif.

```css
:root {
  --kpress-host-font-punctuation: "PT Serif";
}
```

A host that replaces the whole reading stack through `--kpress-host-font-prose` gives
the marks up as a side effect rather than as a choice: the host hook is the first entry
in `--kpress-font-prose`, so a value for it discards the rest of the list, and
`var(--kpress-font-punctuation)` is the head of that list.
Keeping the marks means naming them at the head of the replacement stack.
[The Prose Hook and the Quote Face](kpress-operations-and-host-integration.md#the-prose-hook-and-the-quote-face)
has both declarations and the migration note for a host already setting the hook.

The built-in sans reading mode takes the same path deliberately.
`data-kpress-prose-font="sans"` repoints `--kpress-font-prose` at the sans stack, so the
marks there come from Source Sans 3 on screen and `KPress Print Sans` in print — both
shipped faces, and a serif quote face in a sans paragraph would be the mismatch this
token exists to prevent.

### List Markers

The bulleted list marker is a **drawn box**, not a glyph: `content: ""` on the
`::before`, sized in em of `--kpress-bullet-size`, filled with `currentColor`. It was
`\25AA\FE0E`, and U+25AA is in none of the faces KPress ships, so it fell down whichever
stack its rule inherited — Georgia on a Mac, 16 KB of embedded Georgia in a printed PDF
for 48 bullets, and a different mark on a machine without Georgia.
A box depends on no font and is identical everywhere.

The size and offsets reproduce what the glyph drew, measured in Chromium at a 16px base:
a 3.255 × 3.255 px square whose centre sat 11.05px left of and 13.14px below the item’s
top-left corner. `0.226em` of the marker size is that square, and the offsets carry the
box from the old text origin onto the ink the glyph put there; both are in em of the
marker size, so the same pair of numbers serves `print.css`’s smaller nested marker.
After the change every marker is within 0.02px of its former size and 0.08px of its
former position.

The one deliberate move is `.claim`. Its rule is sans, so its U+25AA resolved a
different fallback and drew 5.20px against the prose marker’s 3.26px — 60% larger, under
a token whose stated purpose is that every bulleted list matches.
All three rules now draw the one square.

Three rules own the marker: `.kpress-prose ul > li::before` and
`.kpress .concepts ul > li::before` in `document.css`, `.kpress .claim::before` in
`components.css`, and `.kpress ol ul > li::before` under `@media print`. A host that
replaces the marker sets `content` **and** clears `background`, since an empty box still
paints.

### Mono Face

Code is set in **Planetaire Mono Text**: B612 Mono’s letterforms with Hack’s punctuation
and symbols, under the SIL Open Font License, vendored as latin subsets from
[jlevy/planetaire](https://github.com/jlevy/planetaire).
It was chosen from a four-way comparison beside PT Serif (Menlo, Source Code Pro, Hack
and Planetaire), each sized from its own ink rather than from its nominal point size.
Before it, code was the one role a document did not draw from a face KPress ships, so a
printed page carried whatever mono the exporting machine had: the explainer PDF that
started this work embedded 56 KB of the build machine’s Menlo.

**The size, derived rather than picked.** `--kpress-font-size-mono` is `0.87` of the
prose size. Planetaire draws an x-height of 1120/2000 = 0.560 em against PT Serif’s
500/1000 = 0.500, so at 0.87 code’s x-height is 0.487 em, about **97%** of the prose
x-height beside it — under parity, so a code span reads as an inset rather than bulging
out of its line. The width follows from the same number: a mono column is 1204/2000 =
0.602 em wide, so 45 / (0.87 × 0.602) ≈ **85 columns** fit the `--kpress-measure`
reading column (85.9, and a column is not divisible).
`tests/test_mono_face.py` re-derives both figures from the shipped faces, so the token
and the ink cannot drift apart.
The `-small` and `-tiny` rungs derive from the mono rung rather than from the base, so
`--kpress-host-font-size-mono` retunes all three at once.
Their multipliers are `0.9` and `0.85` — the prose ramp’s own steps, since the two ramps
pair by index — which is what holds all three rungs at the same 97%. They were `0.915`
and `0.855`, the pre-Planetaire absolutes rescaled and tuned for the system monos this
face replaced, which left the small and tiny rungs at 99% and 98%, drifting toward the
parity the rung above them is chosen to stay under.

**What ships, and what a document declares.** `devtools/subset_mono.py` subsets seven
upstream styles to the same latin `unicode-range` every other vendored face covers and
writes each one beside a stylesheet of its own: `mono-planetaire-<weight>-<style>.css`,
one `@font-face` each.
One stylesheet per style is the mechanism behind `mono_weights`, and selecting
stylesheets is how a render says so without rewriting CSS. What it buys is the built
tree: a style nobody declared is never linked or copied, so the default set leaves three
of the seven subsets (48 KB of woff2) out of a static build, and `mono_font: system`
leaves all seven out (104 KB). It does not buy fewer fetched bytes on top of that, and
the earlier claim that it did — that a single-file page inlines every face it declares —
described behaviour KPress does not have: `single-file` export is refused, inline mode
leaves woff2 external, and no asset mode base64s a font.

**The default is every style the packaged stylesheets ask for**: regular, bold, italic
and bold-italic. `code` resolves to 400 and the highlighter’s keywords to 700;
`syntax.css` sets comment tokens italic and preprocessor and docstring tokens italic
*and* 700. A style a rule asks for and a document does not declare is not absent from
the page — the browser invents it, which is the one thing this face was vendored to
stop.

Two facts settle the default, and they pull the same way:

- **Declaring is not loading.** A browser fetches a declared face only when a glyph
  resolves to it, so the cost of a declaration falls on the page that uses the style and
  on no other. Measured with all four declared: a prose page with no code fetches nothing
  and leaves all four faces `unloaded`; a page of Python fetches `400-italic` for its
  comments and leaves `700-italic` `unloaded`, because Pygments’ Python lexer emits no
  italic-and-700 token — a page of C, whose `#include` does, fetches that one too.
  KPress already declares four PT Serif faces on this reasoning; mono declaring two of
  four was the outlier.
- **Synthesis is what breaks the rule that every glyph comes from a shipped face.** The
  two axes fail differently.
  A missing slant is drawn by shearing the upright face: still `/Type0` in a PDF, but
  leaning about 3° steeper than the drawn italic (Chromium’s shear is a flat 0.25, i.e.
  14.04°, against the 11° the face is drawn with).
  A missing weight is drawn by emboldening a lighter face, which Chromium cannot express
  as an embedded font and emits as **`/Type3` glyph procedures** — a page of paths that
  only looks like text, unsearchable and unselectable, and the precise failure this
  feature exists to remove.

Because of the second, a set that leaves either axis synthesized is refused rather than
accepted and quietly degraded, at both surfaces that take it (`format.mono_weights` and
`RenderOptions.mono_weights`) and in one shared message — see the table below.
The three heavier italics upstream offers are not vendored at all, since no rule reaches
an italic above 700.

`mono_font: system` declares none of them, hands `--kpress-font-mono` back to
`ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`, and drops the faces from the
manifest, so a hosted page fetches nothing and an inlining host carries nothing.
That asset consequence is why it is a render option and not only a CSS switch; the
reader-facing `font_mode="system"` also puts code in the platform mono, but leaves the
asset set alone, exactly as it does for PT Serif.
The two are not equivalent in print, though: `mono_font: system` prints code from the
platform mono as an embedded `/Type0` font, while `font_mode: system` prints the *sans*
roles as `/Type3` outlines on macOS, because Chromium cannot embed the system UI face at
any weight. Measured in
[System Fonts and Printed Outlines](#system-fonts-and-printed-outlines).

Provenance, sha256 and licences are in
[`static/fonts/README.md`](../src/kpress/format/static/fonts/README.md); what a host
that inlines assets prunes is in
[Operations and Host Integration](kpress-operations-and-host-integration.md#host-integration).

### Document Actions Widget

The `doc-actions` chrome widget renders small text badge buttons for taking the document
away: **PDF** (export via print) and **MD** (the Markdown twin).
The badges are plain text in the document sans stack, deliberately not icons: the format
letters say what each action yields.
It follows the settings gear’s architecture — a client-rendered widget over a
server-emitted mount, built only from the public layers (runtime registry, pinned CSS
classes) — but is **off by default**: a page opts in with
`format.widgets: {doc-actions: on}` (or `RenderOptions(widgets={"doc-actions": "on"})`),
or with a config map, which implies on:

```yaml
format:
  widgets:
    doc-actions:
      print: true         # the Export PDF button (default true)
      markdown: true      # the View as Markdown link (default true)
      markdown_url: ""    # explicit Markdown URL; empty derives it (default)
```

The two actions differ in what they need from the host:

- **Export PDF** needs nothing: the button calls the browser’s own print dialog, and the
  printout is the clean `print.css` rendering (badge “PDF”, label “Export PDF”).
- **View as Markdown** needs a URL. The strongly encouraged convention is a Markdown
  twin at the page’s own URL with a `.md` suffix — `.html`/`.htm` replaced, an
  extensionless path appended, a directory path given `index.md` (`/note.html` →
  `/note.md`, `/note` → `/note.md`, `/blog/post/` → `/blog/post/index.md`). The widget
  derives that URL from `location.pathname` by default (`markdownTwinUrl`, a pinned
  export); `markdown_url` overrides it for hosts with a different twin layout (badge
  “MD”, label “View as Markdown”).

**Anatomy.** Each control is two layers, mirroring the other chrome controls: the
*button* (`kpress-doc-actions-btn`) is the interaction layer — the settings gear’s quiet
28px hit target and color states (muted → text on the shared hover surface, no border of
its own) — and the *badge* (`kpress-doc-actions-badge`) is the “icon”, hand-drawn from
type: the format letters in the caps-label idiom one notch below the TOC “Contents”
label, inside a tight 1px `currentColor` frame, so frame and letters stay one color
through every state.
Badge size and corner are host-tunable tokens (`--kpress-doc-actions-badge-size`,
`--kpress-doc-actions-badge-radius`; the corner ships square to match the document’s
square corners).
Both buttons carry `kpress-no-print` chrome semantics through the mount.
**Placement:** on card documents the widget relocates its mount into the content card
(`.kpress-long-text`) and pins to the card’s upper-right corner — the same placement
embedding hosts give their own document actions, so the control sits in one place across
standalone pages and embeds.
Without a card the cluster stays fixed at the doc-actions inset tokens
(`--kpress-host-doc-actions-inset-block` / `--kpress-host-doc-actions-inset-inline`,
same `:root` pattern as the settings insets; default just inline-left of the gear).
Embedding hosts that render fragments (no widget mounts) build their own document
actions with the same text badges, keeping one visual vocabulary.

Font mode (`RenderOptions.font_mode`, type `FontMode = Literal["custom", "system"]`):

- `custom` (default): the vendored faces (PT Serif, Source Sans 3, the quote subset) via
  CSS variables.
- `system`: `.kpress[data-kpress-fonts="system"]` overrides font variables to system-ui
  stacks with no custom font loading.

Font roles. Each role is a CSS variable that resolves through a host hook to a vendored
default, `var(--kpress-host-font-<role>, <vendored stack>)`, so an embedding host can
override any single role on its own, and otherwise the vendored reader faces apply:

| Variable | Default (vendored) | Used by | Host hook |
| --- | --- | --- | --- |
| `--kpress-font-prose` | serif: KPress Quotes, then PT Serif | reading body (`.kpress-prose`), H1/H2 | `--kpress-host-font-prose`, and `--kpress-host-font-punctuation` for the marks alone |
| `--kpress-font-sans` | sans: Source Sans 3 (`KPress Print Sans` instances under print) | UI chrome: TOC, captions, H3–H6, code-copy, **tooltips** | `--kpress-host-font-sans`, and `--kpress-host-font-sans-print` for print alone |
| `--kpress-font-footnote` | sans (via `--kpress-font-sans`) | footnote previews and the bottom footnotes section | `--kpress-host-font-footnote` |
| `--kpress-font-table` | sans (via `--kpress-font-sans`) | data tables | `--kpress-host-font-table` |
| `--kpress-font-body` | sans: Source Sans 3 | `.kpress` wrapper base (a fallback; `.kpress-prose` overrides it for content) | `--kpress-host-font-body` |
| `--kpress-font-mono` | mono: Planetaire Mono Text | code fences, inline code | `--kpress-host-font-mono` |

**Every font setting, on one surface.** Four settings and two sizing hooks decide which
faces a document uses; each is a `RenderOptions` field, most are also a `kpress.yml`
key, and each is readable from the rendered markup.
Two of the rows carry a consequence the row itself cannot hold: none of the five is a
`kpress render` flag ([The CLI Is Not a Font Surface](#the-cli-is-not-a-font-surface)),
and `font_mode: system` changes what an exported PDF is made of
([System Fonts and Printed Outlines](#system-fonts-and-printed-outlines)).

| Setting | Options | Config key | Data attribute | Host hook |
| --- | --- | --- | --- | --- |
| `font_mode` | `custom` (default), `system` | none (render option only) | `data-kpress-fonts` on the `.kpress` article; the reader’s own choice is `data-kpress-font-set` on `<html>` | `--kpress-host-font-mono` still leads under `system`; every other role token is overridden outright |
| `prose_font` | `serif` (default), `sans` | `format.prose_font` | `data-kpress-prose-font` on `<html>` | `--kpress-host-font-prose-sans` for the sans reading stack |
| `math_text_font` | `prose` (default), `katex` | `format.math_text_font` | `data-kpress-math-text` on `<html>` | none: the composite hard-names `KPress Math Text` and reads no host hook; a host substitutes a math face through the two seams below |
| `mono_font` | `planetaire` (default), `system` | `format.mono_font` | `data-kpress-mono-font` on `<html>` | `--kpress-host-font-mono` |
| `mono_weights` | `regular`, `bold`, `italic`, `bold-italic` (all four the default), plus any of `medium`, `semibold`, `extrabold` | `format.mono_weights` | none: it selects stylesheets, not a switch | none |
| the type ramp | — | — | — | `--kpress-host-font-size-base`, the one knob everything derives from |
| the mono rung | — | — | — | `--kpress-host-font-size-mono`, which carries small and tiny with it |

**Two cells above read “none”, and each reads that way for its own reason.**
`math_text_font` reads no host hook because the composite is more than a family name.
`katex/katex-text-face.css` names `KPress Math Text` in all 44 of its `font-family`
declarations and reads none of the `--kpress-host-font-*` variables, so a host that sets
`--kpress-host-font-prose: Palatino` moves the prose and the headings and leaves the
mathematics in PT Serif.
Measured: `.kpress-prose p` computes `Palatino, serif` while `.katex .mord.mathnormal`
computes `"KPress Math Text", KaTeX_Math, serif` on the same page.
That is the design and not a gap in it.
KaTeX lays out from the per-face metric tables in `globalThis.kpressKatexTextMetrics`,
and the Greek slots carry `size-adjust` values computed against PT Serif’s x-height and
cap height, so a family swapped by CSS variable alone would leave Computer Modern boxes
around the new face’s glyphs.
A host substitutes a math face by redeclaring the `KPress Math Text` faces after
`katex/katex-text-face.css` and regenerating the tables with
`devtools/katex_text_metrics.py`; both seams, the sans twin, and the two KaTeX families
a host must *not* redeclare are in
[Operations and Host Integration](kpress-operations-and-host-integration.md#host-integration).
`mono_weights` reads no host hook for an unrelated reason: it selects stylesheets rather
than setting a token, and `--kpress-host-font-mono` is the hook for the face those
stylesheets declare.

`mono_weights` is checked rather than merely parsed, because the interesting values fail
quietly. Both surfaces that accept it refuse the same sets: `format.mono_weights` at
config load, and `RenderOptions.mono_weights` in `__post_init__`, so an export or an
embedding host’s own call cannot slip a set past the gate a `kpress.yml` could not.
One message serves both (`format.assets.mono_weights_rejection`), differing only in
whether it names the YAML key or the dataclass field.
Under `mono_font: planetaire` the set must cover all four styles the packaged
stylesheets ask for; anything less is refused, naming the missing styles and what the
browser would have drawn instead:

| set | what it leaves to the browser | verdict |
| --- | --- | --- |
| the four defaults, with or without `medium`/`semibold`/`extrabold` | nothing | accepted |
| `[regular, bold]` | comment and docstring tokens sheared from the upright faces | refused (slant synthesis) |
| `[regular, bold, italic]` | docstring tokens emboldened from `400-italic` | refused — measured `/Type3` |
| `[regular, italic]`, `[regular]` | keyword tokens emboldened too | refused — measured `/Type3`, up to 2.8× the PDF size |
| `[medium, bold]` | nothing, but no 400 face exists, so ordinary code is set in Medium | refused (no `regular`) |
| `[]` | everything: the page names a family nothing declares, keeps Planetaire’s 0.87 size ratio, and draws in the platform mono | refused — use `mono_font: system` |

Under `mono_font: system` no Planetaire face is declared at all, so `mono_weights` is
ignored and any value is accepted, `[]` included.
That is the supported way to ship no mono face; an empty weight list is not.

Two of those change what ships rather than only how it renders.
`mono_font: system` drops every Planetaire face and its stylesheets from the manifest,
and `mono_weights` narrows that set to the styles named; the rest are display switches
over an unchanged asset set.
A reader’s persisted `font_mode` and `prose_font` choices override the site default at
display time, which is why those two are stamped where a bootstrap can re-stamp them;
`mono_font` and `mono_weights` are publishing decisions and are not reader-switchable.

The reading body is therefore serif by default and is settable serif↔sans per role: a
host flips it by setting `--kpress-host-font-prose` (a host app’s serif/sans
reading-font toggle does exactly this), and `font_mode="system"` swaps every vendored
face for the platform stack.
Footnotes and tables each carry their own stack (`--kpress-font-footnote`,
`--kpress-font-table`) so they can be retargeted independently; both default to the UI
**sans**. The bottom footnotes section uses the same `--kpress-font-footnote` as the
footnote preview tooltips, so the two always agree.

Every text stack leads with a face KPress ships, so a document draws the same glyphs on
any machine and a printed page embeds them rather than borrowing from the renderer; the
system stacks trailing each family are the fallback for a face that failed to load, not
part of the design. `font_mode="system"` and `mono_font="system"` are the two places the
platform is asked for a font on purpose.

Vendored font files ship as package assets and static builds copy them into the output
tree; per-file provenance, sha256 and licence are recorded in
[`static/fonts/README.md`](../src/kpress/format/static/fonts/README.md).
The sans role resolves to a different stack under print, through its own hook
`--kpress-host-font-sans-print`: see [Print Sans Faces](#print-sans-faces).

#### System Fonts and Printed Outlines

`font_mode: system` prints outlines on macOS, and a reader can reach it.
The setting changes no assets, but an exported PDF carries `/Type3` glyph procedures for
every sans role: unsearchable, unselectable paths that only look like text.
That is the same failure the `mono_weights` gate exists to prevent, reached through the
settings widget’s own **System fonts** toggle rather than through a config file.
Measured on one page (prose, a sans heading, a footnote, a table and a code block) taken
through `render_pdf`:

| `font_mode` | PDF size | what the PDF embeds | `/Type3` |
| --- | --- | --- | --- |
| `custom` | 31,846 bytes | PT Serif, the three print-sans instances, three Planetaire styles | none |
| `system` | 91,339 bytes (2.9×) | Georgia and Menlo from the exporting machine, plus PT Serif and one print-sans instance for the print-only roles | 7 objects over 3 descriptors, every one `.SFNS` |

The cause is the face, not the weight.
Chromium writes the macOS system UI font’s descriptors (`EAAAAA+.SFNS-Regular`,
`JAAAAA+.SFNS-Regular`, `LAAAAA+.SFNS-Bold`) with **no `FontFile` at all**, so every
glyph drawn in that face becomes a path.
Rounding KPress’s own sans weight tokens (550 and 650, which no platform face has) to
400 and 700 inside the `system` block was measured and does not remove them: the same
three descriptors appear, still with no `FontFile`, and the PDF only shrinks to 83,363
bytes because the synthetic embolden strokes go away.
So this is written down rather than rounded away.
`mono_font: system` is not affected: code goes to Menlo, which Chromium does embed, as
`/Type0`. A reader who wants the platform faces on screen and a printable PDF should
export from the default `custom` setting.

#### The CLI Is Not a Font Surface

`kpress render`, `kpress format` and `kpress export` take no font flags, so a document
that wants a non-default face is produced through `kpress build --config`, through
`KPressExportRequest`, or through `RenderOptions` directly.
That is the CLI’s shape rather than a gap in this feature: no per-document command
exposes *any* `RenderOptions` field beyond `--output` and `--asset-mode`, so there is no
`--theme`, `--palette`, `--content-card` or `--no-toc` either.
Adding five font flags to `render` alone would leave `format` and `export` behind, which
moves the asymmetry instead of removing it, and would pin a new public command surface
in `kpress.contract` on the strength of one feature.
What matters is that the surfaces which *do* carry the settings agree:
`format.mono_weights` and `RenderOptions.mono_weights` refuse the same sets in the same
words, and `KPressExportRequest` carries `mono_font` and `mono_weights` through to both
the render and the emitted asset tree.

## Document Components

Interactive page parts come in three kinds (see
[Extension and Injection Model](#extension-and-injection-model)); naming the kind first
keeps each new feature on the right seam:

- **Document components:** server-rendered markup, meaningful without JS: prose, tables,
  tabs panels, footnotes, the TOC markup and links, code blocks.
  These are the components listed below.
- **Behaviors:** JS bindings over that markup, each a registered, overridable id: `toc`
  (scroll-spy / drawer / toggle), `tooltip`, `footnote-preview`, `history`
  (viewport-aware scroll restoration across hash history — the scroll pane is invisible
  to the browser’s own Back/Forward restore — plus smooth in-pane section-link
  navigation, since Chromium scrolls a non-root pane instantly on fragment navigation),
  `code-copy`, `video`, `tables`, `tabs`, `diagrams`, and `theme` (engine init over the
  root element). The markup is the binding surface; a host can rebind an id over the same
  markup, or register a new behavior over its own injected HTML.
- **Chrome widgets:** client-rendered, JS-only chrome (`settings`, the opt-in
  `doc-actions`; host-defined ids like a minimap), rendering into server-emitted mounts.

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
- TOC with desktop sticky rail, mobile affordance, active-heading state, threshold, and
  optional depth collapse (below)
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
  This is progressive enhancement: prose does not wait for math.
  Ordinary KPress generation remains browser-free.
  Hosts can optionally prepare measured math geometry during publication and hydrate it
  through the shared runtime; see the
  [font and math loading architecture](project/architecture/arch-2026-09-08-font-and-math-loading.md).
  The cost is accepted: ~290K of KaTeX CSS+JS for documents that contain math (zero for
  documents that do not).
  The KaTeX font faces are not subsetted or bundled eagerly.
  KaTeX lays out using precomputed metrics, including the custom reading-face tables
  where enabled. The shared runtime inspects each hidden rendered formula and waits for
  the faces matching its rendered glyph requests before revealing it; see
  [Math Text Face](#math-text-face).
  Fraktur/Script/Caligraphic/SansSerif/Typewriter, AMS and Size1–4 are fetched only when
  used. An embedding host with a pruned, inlined set may explicitly request all its
  declared faces. All twenty faces are vendored (package size, not client transfer);
  codepoint subsetting is intentionally avoided because needed glyphs are content- and
  not vendor-time-determined, and the per-face native lazy load already bounds client
  bytes. KaTeX’s `@font-face` rules carry `font-display: swap`; the runtime suppresses
  the formula’s visibility until its required faces are ready.
  Native MathML remains valuable as the semantic/accessibility output generated by the
  renderer and as the no-JS fallback.
  A head bootstrap temporarily suppresses its visibility while enhancement runs, with a
  bounded watchdog for missing scripts.
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

### When a Document Earns a TOC

A table of contents is navigation, and navigation only earns its space on a document a
reader cannot take in by scrolling.
`include_toc="auto"` (the default) therefore tests two independent properties and
requires both:

- `format.toc_min_headings` (`RenderOptions.toc_min_headings`, also on
  `KPressRenderRequest`): TOC entries the document must have.
  Default 7.
- `format.toc_min_words` (`RenderOptions.toc_min_words`, also on `KPressRenderRequest`):
  words of visible rendered text the document must have.
  Default 800, between one and two printed pages.

Either test alone admits documents a TOC does not help.
A count-only rule gives one to a half-screen note whose every section is already on
screen; a length-only rule gives one to a long unbroken essay with three headings.
The pairing asks the question that actually matters: is this long enough to scroll past,
and divided finely enough that scrolling is a poor way to reach a part of it?

Length is measured on the **rendered HTML’s visible text**, not the Markdown source, so
table cells and list items count while link targets, attributes, and fence syntax do not
— a page of one-line sections full of long URLs cannot buy a TOC it has no reading
length to justify. The count is `DocumentTree.word_count`.

`include_toc="on"` and `"off"` bypass both thresholds.
A host that wants the historical count-only behavior sets `toc_min_words: 0` and
`toc_min_headings: 4`.

### Collapsible TOC

Long documents overflow the TOC pane, so the TOC supports depth collapse, off by
default:

- `format.toc_collapse_depth` (`RenderOptions.toc_collapse_depth`, YAML key
  `toc_collapse_depth`; also on `KPressRenderRequest` for the dynamic path): the deepest
  **normalized TOC depth** that stays visible when collapsed.
  `None`/absent (the default) disables the feature; the markup is byte-identical to the
  always-expanded TOC. Must be an integer ≥ 1 (validated at the YAML and dynamic-request
  boundaries). Depth is `TocEntry.level`, not the heading tag: the title H1 is dropped
  and level gaps are closed, so in the common one-H1-title document depth 1 is the H2
  spine, depth 2 reaches H3, and depth 3 reaches H4.
- `format.toc_expand_on_scroll` (default `true`, meaningful only with collapse on):
  scroll-follow — the top-level group containing the scroll-spy’s active entry is always
  expanded, so the reader sees the subsections of where they are.
  Collapse-all returns to this baseline, which still shows the active group.

When collapse is on *and* at least one entry is deeper than the threshold, the server
wraps the Contents title in `kpress-toc-header` and renders the `kpress-toc-expand-all`
icon button — a deliberately quiet chevrons control (both sprite glyphs
`chevrons-up-down` / `chevrons-down-up` render, colored like the Contents label; CSS
shows one per `aria-expanded` state) — plus `data-kpress-toc-collapse-depth` /
`data-kpress-toc-expand-on-scroll` on the nav.
The `toc` behavior partitions the flat entry list into spine groups (entries before the
first spine entry form an always-visible head group), and a deep row is visible iff
expand-all is on or scroll-follow marks its group active; hidden rows carry
`kpress-toc-collapsed` and animate closed with the standard motion tokens
(reduced-motion suppression applies).
The scroll-follow handoff waits for the reading position to **settle** in one group
(`TOC_SCROLL_FOLLOW_SETTLE_MS` in `toc.js`): rapid scrolling and the smooth glide after
a TOC click sweep the scroll-spy across intermediate sections, and only the group the
position rests in expands — the highlight itself still moves instantly.
JS-channel config `collapseDepth` / `expandOnScroll` via
`kpress.behaviors.configure("toc", ...)` overrides the data attributes (a config
`collapseDepth` of `0` disables collapse).
When JS config enables collapse on server markup that rendered the feature off, the
behavior creates the same accessible header and expand-all chrome and adds the CSS
activation attribute for that binding.
Disposal removes generated chrome, restores the original attribute, clears collapsed
rows, and resets an existing control’s ARIA label and expanded state before rebind.
There are no per-entry disclosure toggles and no cross-page persistence; deep entries
stay in the markup and the page model — collapse is visibility only.

### Reserved TOC Rail

In the wide band (≥ 75rem of *pane* width) the TOC is a sticky left sidebar and the
reading column is grid track 2, left-aligned: a constant 48rem of text at a constant
distance from the pane’s left edge.
A document that misses either TOC threshold gets no TOC, so by default it also gets no
grid and reverts to the centred, measure-capped single column.
That fallback moves the prose sideways **and** narrows it — the 2.5rem inset on
`.kpress-content-with-toc .kpress-long-text` is sized for the 53rem grid track, so
against the 48rem cap it costs 5rem of measure.
Across a set of documents with varying heading counts the column visibly jumps.

`format.toc_rail` (`RenderOptions.toc_rail`, also on `KPressRenderRequest`) chooses
which behavior a surface wants:

- `auto` — the default and the historical behavior: the rail exists only when a TOC
  does. Renders are byte-identical to before this option existed.
- `reserved` — the rail is a fixed part of the layout whenever TOCs are enabled at all
  (`format.toc != "off"`), so the reading column keeps one position and one measure with
  or without the sidebar.
  The TOC itself is still omitted on short documents; only the empty track remains.

Reserving suits surfaces that show one document after another — a file browser, a
multi-page site — where a stable column matters more than centring any single page.
A lone standalone document usually wants `auto`.

Mechanically, `render.py` stamps `data-kpress-toc-rail="reserved"` on the layout wrapper
in the held-open-but-empty case only; a rendered TOC needs no stamp because the CSS
already keys off the nav, and `format.toc: off` is never stamped.
Every wide-band rule that keys off the TOC therefore selects on three conditions —
`.has-toc`, `:has(.kpress-toc)`, and `[data-kpress-toc-rail="reserved"]` — and adding a
rule that lists fewer splits the two layouts apart again.
The layout comment at the top of `components.css` is the binding reference.

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
  `-prose-font`, `-font-set`, `-fonts`, …): the shared state seam.
  CSS keys theme only from `-resolved-theme`; the pre-paint bootstrap applies standalone
  persisted values before first paint.
- **Tokens:** the CSS-var contract (see [CSS Contract](#css-contract)), including
  per-widget position tokens (`--kpress-<widget>-inset-*`).

### Layer B: Client Primitives (Built-In Headless Engines)

The genuinely complex machinery ships built-in, headless, and reusable, separate from
any presentation:

- `kpress.theme`: the optional standalone resolver: resolve system preference, set and
  persist mode, apply the pre-paint state, and notify change listeners through the
  public `theme.js` exports.
- Theme controls: normalize and synchronize choices, emit `theme:request`, and remain
  independent of root mutation, persistence, and OS-theme listeners through the public
  `theme-controls.js` exports.
- `kpress.storage`: persistence with a pluggable adapter (`{get, set}`; localStorage
  default; an embedding host can supply cookies for cross-port sharing).
- `kpress.menu`: popover behavior: open/close, outside-click/Escape dismiss,
  `aria-checked` segment marking.

A host-owned resolver handles `theme:request` directly; a KPress-resolved surface uses
`kpress.theme`. The gear menu is only the default presentation.

### Layer C: Widget and Behavior Registries (Named, Optional, Replaceable)

Two kinds of registrable things, one registry family, both plain DOM/JS over layers A+B,
no framework:

- **Widgets:** client-rendered *chrome* with a mount point (`settings`, a host’s
  `minimap`). For enabled widgets the server emits only a positioned mount element
  (`<div data-kpress-widget="<id>">`); the widget renders into it (no-JS rule).
  Position stays CSS (the inset tokens).
- **Behaviors:** JS bindings over *server-rendered document markup*: `toc`, `tooltip`,
  `footnote-preview`, `code-copy`, `video`, `tables`, `tabs`, `diagrams` (plus the
  standalone/explicit-opt-in `theme`, which binds resolver initialization to the root
  element). The HTML contract is the binding surface; KPress’s defaults bind to it, a
  host can rebind the same markup, and HTML injected by the host (slots, markdown, build
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
| `theme:request` | Announces a control’s requested theme mode without choosing or mutating the owning scope. The resolver owner applies state. |
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
Dynamic emits one HTML fragment and a JSON serialization of its typed asset manifest per
request; static emits a directory tree the deploying host serves verbatim.

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

`render_fragment` and `render_page` return one `AssetManifest` resolved from the
`RenderOptions.asset_mode` and `asset_url_prefix`. Every `AssetRef` records its package
path, media type, content hash, output path, public URL, browser loading mode, and
whether it is an entry point or dependency-only file.
The manifest contains the complete KPress-owned closure, including stylesheet font URLs,
transitive ESM imports, and conditional KaTeX assets.
It also carries the import map required by hashed ESM output.
Hosts emit tags only for ordered entry points but serve or materialize every manifest
file; they never need to parse CSS or JavaScript to discover dependencies.

`RenderOptions.asset_policy` controls how much of that closure is selected:

- `auto` (default) includes the base styles and fonts, then adds only the entry points
  required by rendered features and their declared transitive dependencies.
  The feature checks cover explicitly requested settings and theme resolution, a
  rendered TOC, footnote previews, code copy, enhanced tables, tabs, diagrams, video
  popovers, and math. Standalone pages request their default settings and resolver;
  fragments do not.
- `none` returns an empty manifest for a host that supplies every required style and
  behavior itself.
- `all` returns the complete reader and KaTeX closure, independent of document content
  or feature flags. It therefore includes the theme resolver; a host-owned fragment uses
  `auto` or `none`.

A host-controlled plain fragment is therefore CSS-only under `auto` without extra
configuration. A fragment may opt into settings presentation without pulling in the
resolver, or set `include_theme_resolver=True` to request KPress ownership explicitly.
A standalone page keeps the default system-theme and settings behavior, so its automatic
manifest includes both modules.

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
- `kpress-asset-manifest-v2`

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

## Operations and Host Integration

Runtime capability probes, browser quality gates, acceptance evidence, accessibility,
and the dynamic embedding protocol live in
[KPress Operations and Host Integration](kpress-operations-and-host-integration.md).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
