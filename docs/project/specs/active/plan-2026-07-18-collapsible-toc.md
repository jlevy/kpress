---
title: Collapsible TOC
description: Depth-collapsed TOC entries with an expand-all toggle and scroll-follow expansion of the active section
author: Joshua Levy (with Claude)
---
# Feature: Collapsible TOC (Depth Collapse, Expand-All, Scroll-Follow)

**Date:** 2026-07-18 (last updated 2026-07-19)

**Author:** Joshua Levy (with Claude)

**Status:** Implemented (feat/toc-collapse; see Implementation Notes)

**Tracking:** `kpr-vuaw`.

## Overview

Long documents produce tables of contents that overflow the sidebar and the narrow-mode
drawer. This feature makes the KPress TOC collapsible by depth:

- **Pre-collapsed deep entries:** TOC entries below a configurable depth (typically
  everything under the H2 level) start hidden, so the TOC shows only the document’s
  top-level spine.
- **Expand-all toggle:** a small icon button on the right of the “Contents” header
  (vertical-expand icon) expands every hidden entry; it then swaps to a
  vertical-collapse icon, and clicking again re-collapses everything below the
  configured depth.
- **Scroll-follow expansion (`toc_expand_on_scroll`, default on):** the top-level
  section the viewport is currently in is always expanded, riding the existing
  scroll-spy, so the reader always sees the subsections of where they are.

## Goals

- The TOC of a long document fits its pane: collapsed by default to the top-level
  entries, with deeper structure one click (or one scroll) away.
- Collapse depth is a typed TOC setting (`toc_collapse_depth`), off by default (`None` =
  today’s fully expanded TOC, byte-identical output, zero goldens drift for existing
  hosts); hosts opt in per site or per render.
- Scroll-follow expansion is a second setting (`toc_expand_on_scroll`), default **on**
  whenever collapse is enabled: the active top-level section’s subtree is always
  visible, independent of the global toggle.
- The expand/collapse-all control is server-rendered chrome with proper ARIA state,
  contract-registered classes, and sprite icons — no host-injected markup.
- Behavior ships inside the existing `toc` runtime behavior (registered, disposable,
  overridable/configurable via `kpress.behaviors.configure("toc", ...)`).
- KPress docs updated so the setting surface and behavior contract are documented.

## Non-Goals

- No per-group disclosure triangles or per-section manual toggles on individual TOC
  entries; the only controls are the global button and the automatic scroll-follow.
  (Clicking a collapsed section’s entry navigates there, which expands it via
  scroll-follow — per-entry toggles can be a later feature if wanted.)
- No persistence of the expanded/collapsed state across page loads (decided: per-page
  state is predictable; the storage adapter stays out of this feature).
- No per-document frontmatter overrides for these settings.
  Per-doc overrides of format settings should arrive as one uniform frontmatter policy
  covering all settings, not one-off keys added feature by feature; that policy is
  tracked separately (`kpr-gjm8`).
- No change to which headings the TOC *contains* (that remains all headings, normalized
  by `_toc_entries`); collapse is a visibility concern only, so deep entries stay
  reachable, linkable, and in the page model.
- No change to the scroll-spy/active-highlight logic itself, or to the narrow-drawer
  open/close mechanics.

## Background

How the TOC works today:

- **Server markup is a flat list.** `_render_toc` (`src/kpress/format/render.py:95`)
  emits `<nav class="kpress-toc" data-kpress-toc>` containing an
  `<a class="kpress-toc-title" data-kpress-toc-top>Contents</a>` title link followed by
  one `<ol class="toc-list">` of *sibling* `<li class="kpress-toc-level-N toc-hN">`
  items — there is no nesting; depth is expressed only through the level classes, which
  CSS maps to indentation and weight (`components.css:355-405`).
- **Depth is structural, not tag-based.** `TocEntry.level` is a normalized TOC depth
  from 1 (`_toc_entries`, `format/markdown.py`): the title H1 is dropped and level gaps
  are closed, so the same heading tag can sit at different TOC depths.
  In the common one-H1-title document shape, depth 1 is H2, depth 2 is H3, depth 3 is
  H4. Settings must therefore be specified in TOC depth, documented with that
  typical-case mapping.
- **TOC config precedent.** `RenderOptions.include_toc: TocMode` and `toc_min_headings`
  (`format/model.py`); mirrored on `FormatConfig` (`publish/config.py`) with YAML keys
  in `_KNOWN_FORMAT_KEYS`, loading/validation in `load_config()`, and threading into
  `RenderOptions` in `publish/build.py`. The dynamic path maps request fields in
  `runtime.py`.
- **Client behavior.** `toc.js` wires each `[data-kpress-toc]` nav: drawer toggle, touch
  handling, and a scroll-spy (IntersectionObserver over the heading ids with a 25%-band
  root margin) that drives `setActiveLink`. It is registered as the `toc` behavior
  (`behaviors.register("toc", ...)`), returns a disposer, and already accepts JS-channel
  config (`icon`, `visible`) via `behaviors.configure("toc", ...)`. TOC clicks navigate
  natively (the history behavior owns scroll restoration), so any collapse state must
  key off `setActiveLink`, not the click handler.
- **Icons.** Chrome glyphs live in the Lucide sprite (`format/static/icons/icons.svg`,
  Lucide v1.17.0, ISC); server renders via `_icon(name)` and client via
  `icons.js icon(name)`. The sprite has no fold/unfold glyphs today; Lucide’s
  `unfold-vertical` and `fold-vertical` are exactly the vertical expand/collapse pair.
- **Contract.** `kpress-toc*` structural classes are pinned in
  `contract.py PUBLIC_CSS_CLASSES`; the behavior id in `PUBLIC_BEHAVIORS`; `toc.js`
  exports in `PUBLIC_JS_EXPORTS`. Contract tests enforce registrations; goldens pin
  rendered markup byte-for-byte.

## Design

### Approach

Server renders the settings and the control; the `toc` behavior owns the state.

**Settings (Python + YAML):**

- `toc_collapse_depth: int | None = None` — deepest TOC depth that stays visible when
  collapsed. `None` (default) disables the feature entirely: markup is byte-identical to
  today. `1` shows only depth-1 entries (the H2 spine in one-H1-title documents); `2`
  shows depths 1-2 (through H3); `3` through H4. Validated ≥ 1.
- `toc_expand_on_scroll: bool = True` — meaningful only when collapse is enabled: keep
  the active top-level group expanded as the reader scrolls.

**Server markup (`_render_toc`):** when `toc_collapse_depth` is set *and* at least one
entry is deeper than the threshold, render:

- the title row wrapped in a header container so the button can sit flush right of
  “Contents”:

  ```html
  <div class="kpress-toc-header">
    <a href="#" class="kpress-toc-title toc-link toc-title" data-kpress-toc-top>Contents</a>
    <button class="kpress-toc-expand-all" type="button" data-kpress-toc-expand-all
            aria-expanded="false" aria-label="Expand all sections">
      <svg…><use href="#kpress-icon-unfold-vertical"></use></svg>
      <svg…><use href="#kpress-icon-fold-vertical"></use></svg>
    </button>
  </div>
  ```

  Both icons render; CSS shows one per `aria-expanded` state (no innerHTML swapping).

- the settings on the nav for the behavior to read: `data-kpress-toc-collapse-depth="1"`
  and, when scroll-follow is disabled, `data-kpress-toc-expand-on-scroll="false"`
  (attribute omitted in the default-on case).

When the feature is off (or nothing is collapsible), none of this renders — existing
hosts and goldens see identical bytes.

**Client state (`toc.js`, inside the existing `toc` behavior):**

- On wire-up, if the nav carries `data-kpress-toc-collapse-depth` (JS-channel config
  `collapseDepth`/`expandOnScroll` from `behaviors.configure("toc", ...)` overrides the
  attributes, per the existing config pattern), partition the flat `<li>` list into
  groups: each entry with level ≤ depth is a *spine* entry and owns the deeper siblings
  that follow it up to the next spine entry.
  (Entries before the first spine entry — possible after depth normalization — form a
  head group treated as always visible.)
- An entry deeper than the threshold is visible iff **allExpanded** (the button state)
  **or** (`expandOnScroll` and its group is the *active group*, i.e. contains the
  scroll-spy’s active link).
  Hidden entries get a `kpress-toc-collapsed` class; visibility is recomputed from that
  one predicate on every state change, so the button and scroll-follow can never fight.
- Button click toggles `allExpanded`, updates `aria-expanded`, and swaps the
  `aria-label` ("Expand all sections" / “Collapse all sections”). Collapse-all returns
  to the baseline state — which still shows the active group when scroll-follow is on;
  that is the setting’s documented meaning ("always expand where the viewport is").
- The active group updates inside the existing `setActiveLink` path (the
  IntersectionObserver and at-top handling already centralize it), so scroll, TOC-click
  navigation, and hash arrival all follow for free — clicking a collapsed section’s link
  navigates there and its group expands.
- All new listeners go through the existing `on()`/`cleanups` disposer plumbing.

**CSS (`components.css`):** `.kpress-toc-header` (flex row, title left, button right);
`.kpress-toc-expand-all` (small quiet icon button, hover treatment matching
`.kpress-toc-toggle`, icon visibility keyed off `aria-expanded`). Expand/collapse
transitions animate with the standard KPress motion tokens (`style-tokens.css` §4
Motion: `--kpress-transition-med` with `--kpress-ease`; the button’s own hover/icon
states use `--kpress-transition-fast` like the other chrome buttons).
Because `display: none` can’t transition, `.kpress-toc-collapsed` animates each affected
row closed — `block-size`/opacity to zero with `overflow: hidden`; every `<li>` is a
fixed single row, so the flat list animates cleanly without measured heights — and the
global prefers-reduced-motion suppression applies as it does to all KPress motion.

**Icons (`icons.svg`):** add Lucide `unfold-vertical` and `fold-vertical` glyphs as
`#kpress-icon-unfold-vertical` / `#kpress-icon-fold-vertical`, same v1.17.0 set as the
existing glyphs.

### Components

- `format/model.py` — `RenderOptions.toc_collapse_depth`, `toc_expand_on_scroll`.
- `format/render.py` — `_render_toc` header row, button, data attributes;
  collapsible-content check.
- `format/static/icons/icons.svg` — the two Lucide glyphs (and the icon-contract
  registration in `docs/kpress-icons.md` / tests).
- `format/static/js/toc.js` — grouping, visibility predicate, button wiring,
  scroll-follow hook in `setActiveLink`; config keys `collapseDepth` / `expandOnScroll`.
- `format/static/css/components.css` — header row, button, collapsed-entry rules and
  motion.
- `publish/config.py` + `publish/build.py` — `FormatConfig` fields, YAML keys
  (`toc_collapse_depth`, `toc_expand_on_scroll`) in `_KNOWN_FORMAT_KEYS`, load +
  validation (int ≥ 1 / bool), threading into `RenderOptions`.
- `runtime.py` — dynamic-path mapping on `KPressRenderRequest`, like `show_doc_header`.
- `contract.py` — register `kpress-toc-header`, `kpress-toc-expand-all`, and
  `kpress-toc-collapsed` alongside the existing `kpress-toc-*` classes.
  No new `toc.js` module exports planned (exports are added deliberately, not by
  reflex).

Documentation (part of the feature):

- `docs/kpress-design.md` — TOC settings surface and the extended `toc` behavior
  contract (config keys, override story).
- `docs/kpress-operations-and-host-integration.md` — host-facing: enabling collapse, the
  depth semantics (TOC depth vs heading tags), overriding via `behaviors.configure`.
- `docs/kpress-e2e-testing.runbook.md` — manual QA additions (below).
- `TODO.md` — backlog/status row.

### API Changes

New `RenderOptions` / `FormatConfig` fields and YAML keys (`toc_collapse_depth` default
`None`, `toc_expand_on_scroll` default `True`); new contract-registered classes; new
sprite glyphs; new `toc` behavior config keys `collapseDepth` / `expandOnScroll`; new
data attributes `data-kpress-toc-collapse-depth`, `data-kpress-toc-expand-on-scroll`,
`data-kpress-toc-expand-all`. All additive; disabled-mode output is byte-identical.

## Implementation Plan

- [x] Add the two Lucide glyphs and their icon-contract coverage (`kpr-yooa`).
- [x] Settings plumbing: `RenderOptions`, `FormatConfig`, YAML keys, validation, build
  threading, dynamic-path mapping (`kpr-nc71`).
- [x] `_render_toc`: header row + button + data attributes behind the setting; contract
  registrations; CSS (including the motion rules) (`kpr-szwk`).
- [x] `toc.js`: grouping, visibility predicate, button toggle, scroll-follow via
  `setActiveLink`; JS-channel config overrides; disposer coverage (`kpr-myvd`).
- [x] Tests (below); goldens: new collapse-enabled scenario, existing scenarios
  byte-identical (`kpr-8rny`).
- [x] Doc updates (`kpress-design.md`, host-integration, e2e runbook, `TODO.md`)
  (`kpr-vhta`).

### Implementation Notes

Deviations and discoveries from the build (branch `feat/toc-collapse`):

- **Reduced-motion specificity:** the row-collapse transition selector initially
  outranked the global `prefers-reduced-motion` block (`.kpress [class]`), so the motion
  was not suppressed — caught by the real-browser smoke.
  The row rules wrap their ancestor scope in `:where()` so the suppression wins; this is
  the pattern for any future rule whose compound selector beats the reduce block.
- **Dynamic-path cache fix:** the render_view cache key omitted `show_doc_header`, so
  requests differing only in presentation flags shared a cached payload.
  The key now carries `show_doc_header` and both TOC-collapse settings.
- **Sprite drift:** adding glyphs drifts every golden page (the sprite inlines per
  document) — an expected, reviewed diff; the “byte-identical” guarantee applies to the
  TOC markup gate, not to sprite additions.

## Testing Strategy

- **pytest:** unit tests for the render gate (off → identical bytes; on with nothing
  collapsible → no button; depth validation); a golden scenario with
  `toc_collapse_depth: 1` pinning header/button/attribute markup; contract and icon
  tests pick up the new registrations/glyphs.
- **vitest (`tests/js/`):** new `toc-collapse` coverage — group partitioning (including
  skipped levels and pre-spine entries), the visibility predicate under all four
  (allExpanded × activeGroup) combinations, button ARIA state, config-override
  precedence, disposer removes the added listeners.
- **E2E (headless Chrome, per the e2e runbook):** long-document script — initial
  collapsed state, expand-all, collapse-all, scroll to a deep section expands its group
  and collapses the previous one, TOC click into a collapsed section; with reduced
  motion emulated, state changes apply without transition.

## Rollout Plan

Ships off by default in the next release — no host sees any change until it sets
`toc_collapse_depth`. Hosts enable it per site (YAML) or per render
(`RenderOptions`/`KPressRenderRequest`), and can tune or replace the client behavior via
`behaviors.configure("toc", ...)`.

## Open Questions

- Should the narrow-mode drawer *always* open fully expanded (small screens may prefer
  seeing everything once the drawer is explicitly opened)?
  Initial answer: keep behavior identical in both modes for predictability.

## References

- `src/kpress/format/render.py` (`_render_toc`), `format/markdown.py` (`_toc_entries`),
  `format/static/js/toc.js`, `format/static/css/components.css`,
  `src/kpress/contract.py` — the code seams.
- [`history-navigation.plan.md`](../../../done/history-navigation.plan.md) — the
  adjacent TOC behavior change this design builds on (native hash navigation,
  `setActiveLink` as the single active-entry path).
- [`content-size-indicators.plan.md`](../../../content-size-indicators.plan.md) — the
  config-plumbing and contract-registration conventions this plan mirrors.
- [`kpress-design.md`](../../../kpress-design.md) — behaviors/component contract and the
  public-surface rules.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
