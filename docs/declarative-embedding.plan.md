---
title: Declarative Embedding
description: Root-independent typography via one base size knob (issue #37) and single-scope, symmetric, theme-agnostic theming (issue #38)
author: Joshua Levy (with Claude)
---
# Feature: Declarative Embedding — Sizing and Theming

**Date:** 2026-07-31 (last updated 2026-07-31)

**Author:** Joshua Levy (with Claude)

**Status:** In Review

**Tracking:** `kpr-t290` is the governing epic.
Its phase features are root-independent sizing (`kpr-2m8v`, issue #37) and single-scope
symmetric theming with theme-agnostic SSR (`kpr-lnzh`, issue #38).

## Overview

Two companion issues share one principle: resolution happens in exactly one place, and
embedded KPress is purely declarative.

- [#37](https://github.com/jlevy/kpress/issues/37): all typography derives from a single
  public base knob instead of `rem`, so a host that pins its own body size (metabrowser
  pins px) gets correct proportions on every browser.
- [#38](https://github.com/jlevy/kpress/issues/38): theme state collapses to one CSS
  input (`data-kpress-resolved-theme`) read at one scope with symmetric light/dark
  keying, `color-scheme` travels with the palette, and fragment SSR output becomes
  theme-agnostic (cacheable across themes).

After this work an embedding host sets exactly two declarative inputs — a base size
variable and a resolved-theme attribute — and the document follows, with no knowledge of
KPress internals and no re-audit on upgrade.

## Goals

- One public size knob (`--kpress-font-size-base`, default `1rem`) with every internal
  font size, the bullet glyph, and its offsets derived from it.
  Standalone pages are pixel-identical to today on a 16px-default browser and keep
  respecting reader font preferences.
- Correct print ratios: print already pins `.kpress` to `--kpress-print-font-size` while
  headings and code stay rem-rooted, so printed h1/body renders ~1.85 instead of the
  designed 1.7. Routing print through the base knob fixes this.
- One theme vocabulary in CSS: only `data-kpress-resolved-theme`, keyed symmetrically
  for light and dark, honored from either an ancestor scope or the element itself, with
  `color-scheme` declared in the same rules as the palette so the two can never split.
- Theme-agnostic fragment SSR: rendered fragments carry no baked theme attributes, so a
  render is cacheable and reusable across themes; hosts own theming at display time.
- A documented embedder contract plus mechanical enforcement: a hygiene lint for the
  sizing invariant and real-browser regression tests for both seams.

## Non-Goals

- Layout lengths stay root-relative: the reading measure (`--kpress-measure: 48rem`),
  the container-query bands (48/64/75rem — `var()` is not valid in query conditions),
  grid tracks, tooltip width caps, page margins, and `--kpress-radius-lg`. This is
  documented as policy, with a possible later phase using `em` container-query
  conditions (which resolve against the query container’s font size).
- No reader font-size chooser in the settings widget (a future feature; it composes with
  the base knob).
- `data-kpress-fonts` / `data-kpress-font-set` symmetry is out of scope; the font-mode
  attribute is asset-coupled (vendored faces shipped or not), not a runtime theme.
- No compatibility shims, per project policy: contract, docs, tests, and goldens change
  in the same patch.

## Background

Findings from reviewing both issues against kpress `f59c44f` and metabrowser `00af0be`
(attic checkout):

**Sizing (#37).** Font sizes live in a rem token ramp (`style-tokens.css`) plus literal
rules that bypass it: h1 `1.7rem` (`document.css`), h5/h6 `1rem`, doc-header h1
`clamp(1.75rem, 4.5vw, 2.3rem)`, hero `1.6/1.5rem`, sans-text `1.75/1.25rem`, the
key-claims label `calc(1.2rem × multiplier)`, and the wide-band heading step-up
(`1.4/1.2/1.2rem` inside `@container (min-width: 64rem)`). Version-skew note (not issue
errors): the issue’s `0.8rem` bullet and its offsets are the values at the
`kpress==0.2.2` tag metabrowser pins (where the bullet genuinely is `0.8rem` with
`top: 0.25rem`); at current HEAD the bullet is `0.9rem` with `−0.85`/`0.1` offsets, and
h2–h4 are tokenized.
The fragment seam (`PUBLIC_FRAGMENT_CSS_VARIABLES`) pins **no** font-size token, so
there is no supported sizing seam today.
metabrowser `main` carries a single higher-specificity override of
`--kpress-font-size-normal` to 17px, which fixes body text only — headings, code, and
labels stay root-relative, and the override cannot reach tooltips because they portal to
`document.body` (`tooltips.js:562`); the full em bridge (ramp remap plus `em`
restatements of h1–h6, bullet geometry, and widget labels, calibrated to 0.2.2) lives on
the in-flight type-scale branch
([metabrowser#16](https://github.com/jlevy/metabrowser/pull/16)), which is the real
downstream migration target.
metabrowser also still sets retired `--kpress-host-bg`-family color hooks, demonstrating
the re-audit-on-upgrade cost.
`tooltips.js:22` additionally hardcodes px mirrors of the rem width caps “at a 16px
root” (existing wart, out of scope here).

**Theming (#38).** All claims verified.
Light is the unkeyed default (`:root, .kpress`) while dark keys four selector forms
including one on the *mode* attribute (`.kpress[data-kpress-theme="dark"]`), so a stale
element-baked dark beats a root-level light (specificity 0,2,0 over 0,1,0) while the
reverse is masked — the asymmetric flaky bug metabrowser observed.
Sharper than the issue states: `color-scheme` lives in separate files (`theme-light.css`
/ `theme-dark.css`) whose element-level dark selector keys on **mode** while the
palette’s keys on **resolved-theme** — so an element-scoped embed rendered with
`theme_mode="system", resolved_theme="dark"` gets a dark palette with light
`color-scheme` even with no staleness involved.
SSR bakes both attributes on every article (`render.py:275-276`); a light and a dark
render differ only in those bytes.
metabrowser’s toggle chases every rendered element (`app.js:490-501`). One correction:
the escape hatch is partially documented — `kpress-operations-and-host-integration.md`
covers `behaviors.override("theme", () => {})` — but the per-element re-stamp
requirement and the stale-attribute hazard are not.

## Design

### Sizing: one base knob (#37)

**The knob.** `style-tokens.css` declares, on the existing four token scopes
(`:root, .kpress, .kpress-page-main, .kpress-tooltip`):

```css
--kpress-font-size-base: var(--kpress-host-font-size-base, 1rem);
```

The host-hook indirection matters: the token scopes declare their own values, so a bare
`--kpress-font-size-base` set by a host on `:root` or a wrapper would be shadowed by
KPress’s own declaration.
The `--kpress-host-*` idiom (already used for every font family) is order-independent,
settable once on `:root`, and reaches body-portaled tooltips.
Hosts may alternatively redeclare the base itself at matching scope and higher
specificity (metabrowser’s existing pattern).

**Derivation form.** Every font-size token and literal becomes
`calc(var(--kpress-font-size-base) * R)` with today’s ratios preserved.
Bare `em` is **not** used for tokens: unregistered custom properties substitute at the
use site, so a token holding `0.82em` would resolve against each consumer’s inherited
size (code in a figcaption ≠ code in prose) — a design change, where `calc(base × R)`
reproduces today’s 16px-root rendering exactly.
Existing intentionally-local sizes stay em/% (summary chevron `0.85em`, checkbox
`1.15em`, sup/sub `85%`).

Ratio table (units change, design does not): h1 1.7; h2 1.32 (wide 1.4); h3 1.15 ×
caps-multiplier (wide 1.2); h4 1.12 (wide 1.2); h5/h6 1.0; doc-header h1 clamp(1.75…2.3,
vw-fluid); hero 1.6 / 1.5; sans-text h1 1.75, h2 1.25; key-claims label 1.2 ×
caps-multiplier; size ramp large 1.2, normal 1.0, small 0.95, smaller 0.9, tiny 0.85,
mono 0.82, mono-small 0.75, mono-tiny 0.7; bullet 0.9 with offsets −0.85 (inline) and
0.1 (block).

**Consequences.** `--kpress-font-size-normal` becomes `calc(base * 1)` and is documented
as derived — hosts set the base, not normal.
The `@media print` block sets `--kpress-font-size-base: var(--kpress-print-font-size)`
so the whole ramp follows the print size; printed output visibly changes (to the
designed ratios) and the release notes say so.

**Contract.** `--kpress-font-size-base` joins `PUBLIC_CSS_VARIABLES` and
`PUBLIC_FRAGMENT_CSS_VARIABLES`; `--kpress-host-font-size-base` joins
`PUBLIC_HOST_CSS_VARIABLES` (the consumed-set equality scan forces same-patch updates).

### Theming: one input, symmetric keying, agnostic SSR (#38)

**One vocabulary.** CSS keys exclusively on `data-kpress-resolved-theme="light|dark"`.
`data-kpress-theme` (the mode) disappears from every stylesheet; it remains resolver
state that `theme.js` and the pre-paint bootstrap write on `<html>` for widget sync.

**Two symmetric selector forms per state; element wins.** For each theme (and each
palette × theme combination), exactly two forms, both declaring the palette tokens *and*
`color-scheme` in the same rule:

```css
/* ancestor scope — :root or any host wrapper; :where() keeps specificity at
   (0,1,0) so it beats the unkeyed defaults by source order only */
:where([data-kpress-resolved-theme="dark"])
  :is(.kpress, .kpress-page-main, .kpress-tooltip) { … }

/* element scope — (0,2,0), wins over any ancestor state */
:is(.kpress, .kpress-page-main, .kpress-tooltip)[data-kpress-resolved-theme="dark"] { … }
```

Light gets identical twins re-asserting the light values, so a stale or deliberate
element attribute always yields a coherent whole-document theme in either direction —
per-document theme islands become possible, and the ancestor form works for hosts that
cannot touch `:root` (the current `:root`-only descendant forms cannot).
The unkeyed light defaults remain as the no-attribute fallback.
`theme-light.css` and `theme-dark.css` fold into the palette blocks in
`style-tokens.css` (their comments reference a retired `--kp-pal-*` indirection anyway);
the files are deleted from the manifest.

**Theme-agnostic SSR.** `render.py` stops baking `data-kpress-theme` and
`data-kpress-resolved-theme` (and `data-kpress-palette`, which participates in the same
selector matrix) on the article.
The standalone page shell is unchanged: `<html>` carries the attributes from the
template plus the pre-paint bootstrap, and the CSS ancestor form picks them up.
Fragment renders become byte-identical across themes and palettes — cacheable — and the
embedder contract is: stamp the resolved theme (and optionally palette) on your chosen
scope, update it on toggle, nothing else; do not load `theme.js` or override the `theme`
behavior with a no-op if your assets include it.
metabrowser then deletes its per-element chasing loop.

**Precedence note.** Element-over-ancestor inverts today’s root-over-element order for
the palette attribute.
Since the article no longer bakes a palette attribute, the standalone palette chooser
(which stamps `<html>`) keeps working; a host that stamps both scopes identically
(metabrowser today) sees no difference.

### API Changes

- CSS contract: add `--kpress-font-size-base` (+ host hook); no class or data-attribute
  names change, but fragment output drops three baked attributes — a behavior change for
  any host that *read* them from rendered HTML (none known; metabrowser writes, not
  reads).
- Python: `RenderOptions.theme_mode`, `resolved_theme`, and `palette` keep their meaning
  for the page shell, bootstrap, widget initial state, and asset selection (`theme.js`
  ships for `system` mode); they no longer affect fragment markup.
- JS: no API changes; `theme.js` remains the standalone resolver behavior.

## Implementation Plan

### Phase 1: Root-independent sizing (#37)

- [ ] Declare the base knob + host hook in `style-tokens.css`; convert the size ramp,
  heading tokens, caps-label and badge derivations, and bullet size to `calc(base × R)`.
- [ ] Convert literal font sizes and bullet offsets in `document.css` and
  `components.css` (including the wide-band redeclarations and the `clamp()` bounds).
- [ ] Route `print.css` through the base knob.
- [ ] Contract additions; sizing-policy comment atop `style-tokens.css`.
- [ ] Hygiene lint (`devtools/public_hygiene.py`): fail any `font-size` declaration or
  size token containing `rem`, with an explicit allowlist for the documented
  root-relative remainder.
- [ ] Playwright two-root test: pinned base ⇒ identical computed sizes at 16px and 13px
  roots; default base ⇒ proportional scaling; ratio spot-checks (h2/body = 1.32, code
  0.82, bullet 0.9).
- [ ] Update pinned strings in `test_asset_contract.py`; regenerate goldens.
- [ ] Docs: sizing policy in `kpress-design.md`, embedder guidance in
  `kpress-operations-and-host-integration.md` and the using-kpress skill; changelog with
  the print-output note and the “set base, not normal” migration line.

### Phase 2: Single-scope symmetric theming (#38)

- [ ] Rewrite the palette × theme selector matrix in `style-tokens.css` to the two
  symmetric forms; co-locate `color-scheme`; delete `theme-light.css` / `theme-dark.css`
  and their manifest entries.
- [ ] Remove the mode attribute from all CSS; extend the hygiene lint to forbid
  `data-kpress-theme` in stylesheets.
- [ ] Stop baking theme/palette attributes on the article in `render.py`; update
  `test_document_contract.py` expectations and regenerate goldens.
- [ ] Pytest: light vs dark (and neutral vs warm) fragment renders are byte-identical.
- [ ] Playwright: element-dark inside root-light renders coherently dark with
  `color-scheme: dark` (and the reverse); host-wrapper (non-`:root`) scope works;
  standalone toggle and pre-paint bootstrap still pass existing tests.
- [ ] Docs: the embedder theming contract (scope, toggle, no `theme.js`), the precedence
  rule, and the SSR cacheability note; changelog migration lines for element-stamping
  hosts.

Phases are independently shippable in either order; both land in one release.

## Testing Strategy

Real-browser (Playwright, existing harness pattern from `test_playwright_clearance.py`)
for everything cascade-dependent: the two-root sizing matrix, theme coherence and
`color-scheme` agreement at both scopes, and stale-attribute scenarios.
Browserless pytest for SSR properties (byte-identical fragments, absent attributes).
Static enforcement via the hygiene lint.
The contract scans and golden suite force same-patch updates of every pinned surface.

## Rollout Plan

One release (0.3.0: the fragment-attribute removal and print-ratio change are
behavior-visible). Release notes carry a migration table (base knob, print-path
divergence, wide-band step-up reappearing in embedded panes once bridge suppression is
deleted, dropped baked attributes breaking downstream assertions).
Downstream metabrowser follow-ups (tracked there, not here): collapse the **entire**
type-scale bridge from [metabrowser#16](https://github.com/jlevy/metabrowser/pull/16) —
the ramp remap, the `em` restatements, and the `--kpress-font-size-normal` override —
into `--kpress-host-font-size-base: 17px` on `:root` plus deliberate ramp-token
overrides via the now-public divergence tier; stamp `data-kpress-resolved-theme` at one
scope and delete the element-chasing loop; drop the retired `--kpress-host-*` color-hook
bridge; and lift the `kpress==0.2.2` pin.

## Open Questions

All three resolved as recommended, confirmed by the PR #40 spec review:
element-over-ancestor precedence; `data-kpress-palette` dropped from the article; the
theme stylesheets folded into `style-tokens.css` with the required source order pinned
in the SELECTOR GRAMMAR comment.

Tracked follow-ups from that review: base-relative container bands via `em` query
conditions (`kpr-y20o`) and overlays copying the anchor’s resolved theme so wrapper
scopes reach portaled tooltips (`kpr-gssj`).

## References

- [Issue #37](https://github.com/jlevy/kpress/issues/37) — sizing;
  [Issue #38](https://github.com/jlevy/kpress/issues/38) — theming
- [kpress-design.md](kpress-design.md) — architecture and public-contract reference
- [kpress-operations-and-host-integration.md](kpress-operations-and-host-integration.md)
  — current host guidance
- metabrowser: `main` at `00af0be` (`src/metabrowser/static/styles.css` bridge tokens
  and `--kpress-font-size-normal` override; `static/app.js:490-501` element re-stamping)
  and the in-flight type-scale bridge on
  [metabrowser#16](https://github.com/jlevy/metabrowser/pull/16), the actual migration
  target

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
