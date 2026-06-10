---
title: KPress Reader Features
description: Long-lived catalog of the document-reader features KPress provides and the behavior each one guarantees. Feature contract only; no implementation status, bead, or source-port detail.
author: Claude under Levy
---
# KPress Reader Features

This is the durable feature catalog for the KPress document reader: what a
KPress-rendered document supports and how each feature is meant to behave.

It is intentionally free of implementation status, bead ids, and any comparison to or
porting notes from other systems.
Current status and the remaining-work tracker live in [`TODO.md`](TODO.md) and
[`docs/kpress-completion-plan.md`](docs/kpress-completion-plan.md).
Architecture and the public contract live in [`kpress-design.md`](kpress-design.md).

## Foundation

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

## Markdown and document tree

- **GFM block and inline parsing.** Headings, paragraphs, nested lists, blockquotes,
  links and autolinks, strikethrough, task lists, hard/soft breaks, and code fences.
- **Stable heading anchors and TOC metadata.** Deterministic, de-duplicated heading ids
  with plain inline titles; broken-anchor diagnostics; a single leading H1 is excluded
  from the TOC.
- **Raw HTML trust modes.** Trusted-local, sanitized-local, public-static, and untrusted
  modes with a defined safe/unsafe policy and diagnostics.
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

## CSS and layout

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

## Theme and fonts

- **Light, dark, and system modes** with localStorage persistence,
  `prefers-color-scheme` response, and a synchronous pre-paint no-flash bootstrap.
- **Standalone settings menu.** Full pages ship an accessible, no-print gear-icon
  popover with a `system`/`light`/`dark` icon chooser (ported from metabrowser’s
  design); embedded hosts own the control instead.
- **Font model.** A global `font_mode` selects vendored reader faces (`custom`) or the
  platform stack (`system`); reader fonts, when used, are vendored and sealed offline
  (no CDN at publish).

## Interactions

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

## Media and assets

- **Images and figures.** Standalone images emit semantic `<figure>/<figcaption>`; raw
  HTML figures receive the same hooks; a document thumbnail renders when provided.
- **Offline sealed assets.** Local assets, and approved external assets, are
  fetched/sealed into the output with manifest provenance; published output is
  verifiably free of unexpected network references.

## Print and PDF

- **Print CSS.** Page rules, paper palette, no-print/print-only, TOC and video
  suppression, heading/table break control, repeated table headers, footnote
  simplification, code wrapping, and orphans/widows.
- **Browser-backed PDF.** An optional browser backend renders the print profile to PDF;
  absence of the optional dependency produces a clear error, never a silent downgrade.

## Accessibility

- **Reduced motion.** Reader transitions and animations honor
  `prefers-reduced-motion: reduce`.
- **Keyboard and ARIA.** Interactive components expose correct roles, manage focus (trap
  and restore for modal surfaces), support keyboard operation and Escape close, and
  target adequate contrast.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
