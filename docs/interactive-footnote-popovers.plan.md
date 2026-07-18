---
title: Interactive Footnote Popovers
description: Proposed KPress interaction and accessibility contract for transient footnote previews and pinned evidence popovers
author: Joshua Levy (with Codex)
---
# Feature: Interactive Footnote Popovers

**Date:** 2026-07-18

**Author:** Joshua Levy (with Codex)

**Status:** In Review

**Tracking:** `kpr-4q0a` is the governing epic.
Its phase epics are interaction and semantics (`kpr-pw7v`), asset and real-browser
verification (`kpr-ipqy`), and documentation and release evidence (`kpr-x23v`).

## Overview

KPress footnote previews currently combine two jobs in one transient tooltip: quick
reading and link interaction.
The tooltip contains a navigation link, but its marker suppresses normal click and touch
navigation and blur removes the surface.
This makes the link difficult to activate and gives interactive content
`role="tooltip"`.

KPress will separate those jobs.
Hover and focus provide a transient, non-interactive preview.
Activating the marker pins a non-modal evidence popover whose links and controls can be
used deliberately. The complete document-end footnote section remains the no-JavaScript
and print representation.

## Goals

- Make footnote links reliable with pointer, keyboard, and touch input.
- Use distinct, correct semantics for descriptive previews and interactive popovers.
- Preserve native marker navigation whenever the behavior is absent, overridden,
  disposed, unable to resolve a target, or running without JavaScript.
- Keep one host-neutral behavior across standalone pages and injected fragments.
- Preserve KPress’s source-first ESM, behavior-registry, overlay, asset-manifest, and
  public-contract boundaries.

## Non-Goals

- New Markdown or citation syntax.
- An interactive or pinnable mode for ordinary internal-link previews.
- A modal dialog, focus trap, cross-document preview, or remote content fetch.
- Host-specific JavaScript or CSS.
- A new browser runtime dependency or bundler.

## Current Behavior

`src/kpress/format/static/js/tooltips.js` registers `tooltip` and `footnote-preview` as
separate behaviors over ordinary hash anchors and footnote markers.
It clones sanitized target HTML into an `aside[role=tooltip]`, appends a footnote
navigation link, and positions the surface with the shared overlay and viewport helpers.

The module also prevents footnote `click` and `touchend`, prevents `touchstart` for all
eligible hash anchors, and removes the tooltip on marker blur.
The transient surface therefore contains a focusable link without a dependable focus
path. These facts are covered by the existing browserless tests and must be converted
into failing regression cases before implementation.

## Design

### State model

The behavior has three states: closed, transient preview, and pinned popover.
One footnote can be active at a time.

| Action | State transition | Required result |
| --- | --- | --- |
| Marker hover | closed → transient | Delayed text preview with `role="tooltip"` |
| Marker focus | closed → transient | Immediate text preview associated by `aria-describedby` |
| Marker click, Enter, or tap | closed/transient → pinned | Non-modal evidence popover; initial valid unmodified activation is consumed |
| Second marker activation | any → pinned on new marker | Previous surface closes first |
| Close, Escape, or outside click | pinned → closed | Focus returns to the marker when focus was inside |
| Marker mouse leave or blur | transient → closed | Existing delay rules apply; pinned state is unaffected |
| Ordinary hash-link activation | preview → native navigation | The preview never prevents navigation |

Modified pointer activations and markers with missing targets retain native behavior.
The disposer removes global and per-marker listeners it owns and closes any active
surface. A host override must not inherit click suppression from a previously bound
built-in behavior.

### Transient preview

The transient preview keeps the current placement ladder and character cap.
It may preserve inline emphasis, but it has no focusable descendants and does not accept
pointer input. Links in the cloned footnote are rendered as readable text without link
styling, and a short “Activate note for links” hint appears only when the source
footnote contains links.
The marker references the preview with `aria-describedby` only while it is present.

Ordinary internal-link previews remain transient and their anchors keep native click,
Enter, modified-click, touch, and missing-target behavior.

### Pinned popover

The pinned footnote surface uses either the native Popover API or the existing overlay
primitive, as the supported-browser tests determine.
Its observable contract is independent of that internal choice:

- `role="dialog"` with a label derived from the visible footnote number;
- `aria-controls` and `aria-expanded` on the marker;
- sanitized footnote HTML with functional internal and external links;
- explicit Close and “View full footnote” controls;
- Escape and outside-click dismissal;
- no focus trap;
- keyboard activation moves focus into the surface, while pointer activation leaves
  focus on the marker;
- narrow viewports use the existing bottom placement as a pinned bottom sheet.

The “View full footnote” link is the explicit replacement for suppressed marker
navigation. It follows the original `#fn-*` target and closes the popover.
Other cloned links retain the sanitizer and renderer’s existing URL and external-link
policies.

### Public and host contracts

The public behavior id remains `footnote-preview`, and `initKpressTooltips()` remains
the direct initialization seam.
No compatibility flag preserves the old click suppression during the alpha.

New public class names, data attributes, exports, or behavior configuration keys are
declared in `kpress.contract` with matching docs, contract tests, and goldens.
Prefer private module state and existing overlay exports when no host-facing seam is
needed.

Standalone, linked, hashed, and hosted output must all select and materialize the full
transitive ESM closure.
Import maps precede module entry points, and hosts emit tags only for manifest entry
points while serving every dependency asset.

## Implementation Plan

### Phase 1: Behavior and semantics

- [ ] Add red tests for native ordinary-link activation, invalid footnote targets,
  pointer and keyboard pinning, touch pinning, interactive cloned links, focus restore,
  overrides, remounts, and disposal.
- [ ] Split transient and pinned state under the existing registered behaviors.
- [ ] Add accessible controls, state attributes, and responsive component styling.
- [ ] Update public contracts and goldens for any new stable hook.

### Phase 2: Asset and browser verification

- [ ] Prove linked, hashed, and hosted manifests resolve every reader-module import and
  install import maps before entry points.
- [ ] Extend the real-browser fixture for pointer travel, keyboard-only use, touch
  emulation, narrow placement, reduced motion, print, and no-JavaScript fallback.
- [ ] Verify injected fragments bind once after runtime readiness and dispose without
  leaving event cancellation behind.

### Phase 3: Documentation and release evidence

- [ ] Update `docs/kpress-design.md` to describe the delivered interaction and public
  hooks.
- [ ] Update `docs/kpress-operations-and-host-integration.md` with host readiness and
  complete-asset-closure checks.
- [ ] Update `docs/kpress-e2e-testing.runbook.md`, `TODO.md`, and release-facing notes
  with the verified browser matrix.
- [ ] Run `make lint-check`, `make test`, and `make verify`; record real-browser
  evidence separately from browserless behavior coverage.

## Testing Strategy

Browserless DOM tests establish the state machine, semantics, event cancellation,
dynamic insertion, lifecycle cleanup, and link behavior.
Python asset-contract and publisher tests enumerate the ESM graph and assert emitted
files and import-map order in every supported asset mode.
Real Playwright checks establish pointer, keyboard, touch, responsive, theme,
reduced-motion, print, and no-JavaScript acceptance.

Every regression begins red against the current behavior.
Browserless results do not substitute for the real-browser evidence recorded in
`TODO.md` and the end-to-end runbook.

## Rollout Plan

Develop on `codex/interactive-footnote-popovers`, currently stacked on the pending
`toc-tree-normalization` branch.
After that branch merges, rebase or retarget this work to `main`, run the complete
verification gate, and review it as an independent KPress pull request.
Embedding projects consume the reviewed commit through their normal exact source pin; a
package release can follow the KPress release process separately.

## Resolved Decisions

- The corrected behavior is the KPress default.
- Transient previews are non-interactive; pinned footnote popovers are interactive.
- The pinned surface is non-modal and does not trap focus.
- Ordinary internal-link previews never capture activation.
- No new runtime dependency or build step is introduced.

## Open Questions

None. Native Popover API use is an implementation choice gated by the supported-browser
tests, not an observable contract decision.

## References

- [KPress design and public contracts](kpress-design.md)
- [Operations and host integration](kpress-operations-and-host-integration.md)
- [End-to-end testing](kpress-e2e-testing.runbook.md)
- `src/kpress/format/static/js/tooltips.js`
- `src/kpress/format/static/js/overlay.js`
- `src/kpress/format/static/js/runtime.js`

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
