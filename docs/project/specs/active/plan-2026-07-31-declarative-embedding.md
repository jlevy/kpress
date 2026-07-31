---
title: Declarative Embedding
description: Plan for root-independent typography via one base size knob (issue #37) and single-scope, symmetric, theme-agnostic theming (issue #38)
author: Joshua Levy (with Claude)
---
# Feature: Declarative Embedding — Sizing and Theming

**Date:** 2026-07-31 (last updated 2026-07-31)

**Author:** Joshua Levy (with Claude)

**Status:** Implemented (in review on [PR #40](https://github.com/jlevy/kpress/pull/40))

**Tracking:** `kpr-t290` is the governing epic; its phase features are `kpr-2m8v`
(sizing, issue #37) and `kpr-lnzh` (theming, issue #38), with implementation beads
`kpr-sdbo`, `kpr-d0n1`, `kpr-xfee`, `kpr-jtaw`, `kpr-tf2i`, `kpr-wjtf`, `kpr-vlsr`,
`kpr-bgqq`, `kpr-c0kl` and review beads `kpr-2197`, `kpr-tjjd` (all closed).
Follow-ups remain open as `kpr-y20o` (base-relative container bands) and `kpr-gssj`
(overlays copy the anchor’s resolved theme).

## Overview

Two companion issues share one principle: resolution happens in exactly one place, and
embedded KPress is purely declarative.
[#37](https://github.com/jlevy/kpress/issues/37) derives all typography from one public
base knob instead of `rem`; [#38](https://github.com/jlevy/kpress/issues/38) collapses
theme state to one CSS input read at one scope, with theme-agnostic fragment SSR. An
embedding host sets two declarative inputs — a base size variable and a resolved-theme
attribute — and the document follows, with no knowledge of KPress internals and no
re-audit on upgrade.

The durable contracts live in the reference docs:
[Sizing Policy](../../../kpress-design.md#sizing-policy) and
[Theme and Fonts](../../../kpress-design.md#theme-and-fonts) in KPress Design, the
embedder guidance in
[Operations and Host Integration](../../../kpress-operations-and-host-integration.md),
the SELECTOR GRAMMAR and SIZING POLICY comments in `style-tokens.css`, and the
[0.3.0 release notes](../../../releases/0.3.0.md) with the migration table.

## Goals

- One public size knob (`--kpress-font-size-base`, default `1rem`) with every internal
  font size, the bullet glyph, and its offsets derived from it; standalone pages
  pixel-identical on a 16px-default browser and still reader-preference-respecting.
- Correct print ratios (print previously pinned the body at 11pt while headings and code
  stayed rem-rooted, printing h1/body at ~1.85 instead of the designed 1.7).
- One theme vocabulary in CSS (`data-kpress-resolved-theme` only), symmetric light/dark
  keying at ancestor and element scopes, `color-scheme` co-located with the palette.
- Theme-agnostic fragment SSR: no baked theme or palette attributes, byte-identical
  renders across themes, cacheable.
- A documented embedder contract plus mechanical enforcement (hygiene lints and
  real-browser regression tests for both seams).

## Non-Goals

- Layout lengths stay root-relative: the reading measure, container-query band
  conditions (`var()` is not valid there), grid tracks, tooltip width caps, page
  margins, and `--kpress-radius-lg`. Follow-up `kpr-y20o` tracks the `em`-condition
  alternative.
- No reader font-size chooser in the settings widget (future; composes with the base).
- `data-kpress-fonts` / `data-kpress-font-set` symmetry: the font-mode attribute is
  asset-coupled (vendored faces shipped or not), not a runtime theme.
- No compatibility shims, per project policy.

## Background

Decision record from reviewing both issues against kpress `f59c44f` and metabrowser
(`main` at `00af0be` plus the in-flight type-scale bridge on
[metabrowser#16](https://github.com/jlevy/metabrowser/pull/16), calibrated to the pinned
`kpress==0.2.2`):

- Sizing was rem-coupled in a token ramp plus literals bypassing it (h1, h5/h6,
  doc-header `clamp()`, hero, sans-text, key-claims label, the wide-band step-up), the
  fragment seam pinned no size token, and metabrowser’s single
  `--kpress-font-size-normal` override fixed body text only and could not reach
  body-portaled tooltips.
  The issue’s `0.8rem` bullet was version skew against 0.2.2, not an error.
- Theming keyed light as the unkeyed default against four dark selector forms (including
  one on the *mode* attribute), so a stale element-baked dark beat a root-level light
  while the reverse was masked; `color-scheme` lived in separate files whose
  element-level dark selector keyed the mode while the palette keyed the resolved theme,
  so an element-scoped embed could get a dark palette with light `color-scheme` with no
  staleness involved; SSR baked both attributes on every article, making renders differ
  only in those bytes; and print exhibited the same pinned-body-under-rem-headings drift
  in-repo.

## Design

Both designs are recorded in full in the reference docs; the decisions that shaped them:

- **`calc(base × ratio)` over bare `em` for every derived size:** unregistered custom
  properties substitute at the use site, so an `em` token would re-resolve per consumer
  and silently change ratios in nested contexts; `calc` reproduces the 16px-root
  rendering exactly. Intentionally context-relative `em`/`%` sizes stay.
- **The base knob reads a `--kpress-host-*` hook** so a host sets it once on `:root`,
  order-independent, reaching body-portaled overlays; redeclaring the base itself
  remains sanctioned but also overrides print re-rooting.
  The ramp/label/bullet tokens are public in both contract surfaces as the sanctioned
  divergence tier (spec review finding 2).
- **Two symmetric selector forms per theme state** — a `:where()`-flattened ancestor
  form (`:root` or any host wrapper) that beats the unkeyed light defaults by source
  order, and a full-strength element form that wins over any ancestor state — with
  `color-scheme` keyed identically, the mode attribute banned from CSS, and the palette
  matrix on the same grammar.
- **Fragment SSR bakes no theme or palette attributes**; the page shell stamps `<html>`;
  the dynamic render cache keys only the payload-relevant derivative of theme state
  (`system` mode ships `theme.js`).

## Implementation Plan

### Phase 1: Root-independent sizing (#37) — complete

- [x] Base knob + host hook; every size token, literal, and the bullet geometry
  converted to `calc(base × ratio)`; print re-rooted (`kpr-sdbo`)
- [x] Two-root real-browser regression, including a body-portaled overlay probe,
  verified red against the old CSS (`kpr-d0n1`)
- [x] Hygiene lint: no rem font sizes, fallback literals included (`kpr-xfee`)
- [x] Contract additions including the public divergence tier; sizing docs and release
  notes (`kpr-jtaw`, `kpr-2197`)

### Phase 2: Single-scope symmetric theming (#38) — complete

- [x] Symmetric selector matrix with co-located `color-scheme`; theme stylesheets folded
  into `style-tokens.css`; `syntax.css` on the same grammar (`kpr-tf2i`)
- [x] Theme-agnostic fragment SSR with byte-identical regression; render-cache key
  reduced to the payload-relevant bit (`kpr-wjtf`, review finding 6)
- [x] Real-browser coherence suite: both scopes, both island directions, `color-scheme`
  agreement, mode-attribute inertness, warm × theme composition, verified red against
  the old matrix (`kpr-vlsr`)
- [x] Hygiene lint: no mode-attribute selectors in CSS (`kpr-bgqq`)
- [x] Embedder theming contract in the reference docs; migration table in the release
  notes (`kpr-c0kl`, `kpr-tjjd`)

## Testing Strategy

Real-browser Playwright for everything cascade-dependent (two-root sizing matrix, theme
coherence at both scopes, stale-attribute islands); browserless pytest for SSR
properties (byte-identical fragments, absent attributes, cache identity); static
enforcement via the two hygiene lints; the contract scans and golden suite force
same-patch updates of every pinned surface.

## Rollout Plan

One release (0.3.0): the fragment-attribute removal and print-ratio change are
behavior-visible, and the [release notes](../../../releases/0.3.0.md) carry the
migration table. Downstream metabrowser follow-ups (tracked there): collapse the entire
[metabrowser#16](https://github.com/jlevy/metabrowser/pull/16) bridge into the base hook
plus deliberate ramp-token overrides, stamp `data-kpress-resolved-theme` at one scope
and delete the element-chasing loop, drop the retired color-hook bridge, and lift the
`kpress==0.2.2` pin.

## Open Questions

All resolved (element-over-ancestor precedence; palette attribute dropped from the
article; theme stylesheets folded into `style-tokens.css`), confirmed by the PR #40 spec
review and re-review.
Follow-ups tracked as `kpr-y20o` and `kpr-gssj`.

## References

- [Issue #37](https://github.com/jlevy/kpress/issues/37),
  [Issue #38](https://github.com/jlevy/kpress/issues/38),
  [PR #40](https://github.com/jlevy/kpress/pull/40) (spec review and re-review)
- [KPress Design](../../../kpress-design.md) — Sizing Policy, Theme and Fonts, CSS
  Contract
- [Operations and Host Integration](../../../kpress-operations-and-host-integration.md)
  — embedder guidance
- [KPress 0.3.0 notes](../../../releases/0.3.0.md) — migration table
- metabrowser: `main` at `00af0be` and
  [metabrowser#16](https://github.com/jlevy/metabrowser/pull/16)

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
