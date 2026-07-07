---
title: KPress Completion Plan
description: Status and tracking companion to kpress-design.md; implementation status, acceptance milestones, the bead map, planned packaging tiers, and the Kash/TextPress reference-migration record (source areas, component matrix, Tailwind migration, conscious departures), plus the manual browser acceptance process.
author: Claude under Levy
---
# KPress Completion Plan

**Date:** 2026-05-17

**Status:** Active

## Executive Summary

“KPress end-to-end works” means every row in the reader parity ledger (moved to the
2026-05-18 MVP-stability-and-doctor plan spec, in the original monorepo) reads
**Implemented**, every open/in-progress bead under `orig-xgzj` (reader parity epic) and
`orig-wkzp` (package/publisher epic) is closed with acceptance evidence, and both
dynamic rendering and sealed static publishing produce equivalent document surfaces
across desktop, mobile, dark mode, print, and PDF.

The single structural blocker is that the majority of remaining beads are “code-side
done, manual browser acceptance remains.”
An automated agent can write Python, CSS, and JavaScript.
It cannot open a real Chromium window, visually confirm typography rendering, touch-test
a mobile TOC drawer, verify dark mode has no flash, inspect a print preview, or judge
whether a PDF page break lands correctly.
Approximately two thirds of the open work requires a human operator (or a Playwright
operator with real-browser access) to discharge acceptance evidence.
Until that happens, the beads stay open and parity cannot be claimed.

## Categorized Bead Table

Every open or in-progress KPress bead, categorized by what kind of work remains.

Category key:

- **ACTIONABLE-CODE**: can be finished headlessly now (write code, tests, goldens).
- **AUTOMATED-HARNESS**: can be strengthened with browserless tests/fixtures, but the
  bead’s exit criterion also requires manual browser evidence.
- **MANUAL-BROWSER**: code-side done; the remaining work is real-browser visual,
  interaction, or PDF acceptance that an automated agent cannot perform.
- **GROUPING/GATE**: epic or closure bead that auto-closes when its children close.

### Epic and Gate Beads

| Bead | Title | Category | Status | Exit criterion |
| --- | --- | --- | --- | --- |
| `orig-xgzj` | KPress reader feature parity completion | GROUPING/GATE | in_progress | All child feature beads closed with acceptance evidence. |
| `orig-wkzp` | KPress package and static publisher | GROUPING/GATE | open | All child publishing/runtime beads closed. |
| `orig-mfwo` | Host-embedded KPress document views and print support | GROUPING/GATE | in_progress | Host integration beads closed. |
| `orig-08y5` | Final reader parity audit and closure gate | GROUPING/GATE | open | Every parity ledger row is Implemented, goldens/browser checks linked, TODO.md clean. |

### Publishing and Optimizer Beads

| Bead | Title | Category | Status | Remaining work | Exit criterion |
| --- | --- | --- | --- | --- | --- |
| `orig-owjr` | Preflight full optimizer before output | ACTIONABLE-CODE | open | Preflight the `full` optimizer before any output is written, so a missing `npx` fails early. | `kpress build --optimizer full` fails before writing any output when `npx` is absent. |
| `orig-zc7g` | Locked sminify/html-minifier-next dependency layer | ACTIONABLE-CODE | open | Replace raw `npx --package` with a locked dependency cache for `html-minifier-next`. | Optimizer `full` uses a locked dependency rather than live `npx` resolution. |
| `orig-8kis` | Dynamic-vs-sealed equivalence harness | AUTOMATED-HARNESS | in_progress | Harness code done. Manual browser console/network, interaction, computed-style, mobile, dark-mode, print, PDF review evidence remains. | Only accepted differences are URL shape, hashing, minification, compression, and documented optional optimizations. |
| `orig-aquv` | Static publishing production maturity | ACTIONABLE-CODE | in_progress | Routes, sitemap, and cache-invalidation done. Frontmatter-format precedence fixtures remain. | Deterministic routes, complete metadata, clear diagnostics, cache invalidation proofs. |

### Grouping Beads (Older Broad Parity)

| Bead | Title | Category | Status | Exit criterion |
| --- | --- | --- | --- | --- |
| `orig-8is3` | Markdown/GFM and document-tree reader parity | GROUPING/GATE | open | Child markdown/document beads closed with accepted goldens and manual rich-Markdown visual review. |
| `orig-131h` | Document CSS, theme assets, print CSS, JS helpers | GROUPING/GATE | open | CSS/theme/print/font beads closed with selector coverage and manual review. |
| `orig-d6g2` | TOC, footnotes, tooltips, tables, code components | GROUPING/GATE | open | Interaction beads closed with DOM tests and browser acceptance. |
| `orig-selz` | Semantic content and document-format component parity | GROUPING/GATE | open | Semantic beads closed with selector tests and manual desktop/mobile/dark/print review. |
| `orig-5dmd` | Font and packaged asset sealing reader parity | GROUPING/GATE | open | Font/asset beads closed with offline verification and computed-style probes. |
| `orig-n7ok` | Browser-print PDF artifact generation | GROUPING/GATE | open | PDF backend done (via `orig-14v1`); real fixture PDFs and manual inspection remain. |
| `orig-0xa1` | Public-contract hardening, accessibility, host readiness | GROUPING/GATE | open | Accessibility/ARIA review, host contract, and manual keyboard/mobile acceptance complete. |

### Reader Feature Beads (Code-Side Done, Browser Acceptance Remains)

| Bead | Title | Category | Status | Remaining work | Exit criterion |
| --- | --- | --- | --- | --- | --- |
| `orig-97c1` | GFM Markdown block/inline document tree | MANUAL-BROWSER | in_progress | Manual rich-Markdown visual review. | Accepted goldens and visual confirmation for all GFM row features. |
| `orig-1rc7` | Raw HTML trust and sanitizer matrix | MANUAL-BROWSER | in_progress | SVG/iframe/script policy detail, duplicate-id diagnostics, browser review. | Sanitizer fixtures and browser-rendered proof of safe/unsafe handling. |
| `orig-oxs3` | Images, figures, captions, local media | MANUAL-BROWSER | in_progress | Manual image/static-output review, responsive variants, sidematter precedence. | Fixtures for local/relative/absolute/missing assets with browser no-network check. |
| `orig-c5xy` | Code fences, source profiles, syntax highlighting | MANUAL-BROWSER | in_progress | Source-profile language fallback, host adapter regression, manual code visual review. | Fixtures cover language/no-language fences, long lines, source files, print, and syntax-highlighted output. |
| `orig-g0ra` | `off`/lazy-`auto` KaTeX math | ACTIONABLE-CODE + MANUAL-BROWSER | in_progress | Math `off` + lazy `auto` KaTeX refactor (KaTeX active, MathML kept as semantic/accessibility output); backend matrix deferred; manual browser/PDF review remains. | Documents without math load no math assets; documents with math render through KaTeX while preserving MathML as semantic/accessibility output. |
| `orig-lir6` | Diagram rendering providers | MANUAL-BROWSER | in_progress | Manual browser/PDF review; bundled Mermaid/pre-rendering decision. | Browser diagram rendering and sealed output confirmation. |
| `orig-vdbu` | Typography, document CSS, themes | MANUAL-BROWSER | in_progress | Host control mapping, dark component review, manual light/dark/system browser acceptance. | Computed-style probes and human review confirm long-prose quality. |
| `orig-boxw` | Print CSS and print profiles | MANUAL-BROWSER | in_progress | Manual print preview and browser-backed PDF fixture review. | Print-media browser probes and manual print preview readable for all content types. |
| `orig-i4rj` | Desktop TOC behavior | MANUAL-BROWSER | in_progress | Manual desktop browser review for scroll, active states, anchors. | Browser tests and DOM-state goldens cover desktop TOC. |
| `orig-o59o` | Mobile TOC drawer behavior | MANUAL-BROWSER | in_progress | Manual mobile viewport review for drawer open/close, scroll locking. | Mobile browser tests and manual narrow-viewport review. |
| `orig-2z84` | Internal-link preview tooltips | MANUAL-BROWSER | in_progress | Manual tooltip browser/touch review. | Browser tests for all preview target classes. |
| `orig-09i3` | Responsive tables and numeric-cell hooks | MANUAL-BROWSER | in_progress | Manual wide-table desktop/mobile/print browser review. | Fixtures for narrow/wide/numeric tables with mobile/print confirmation. |
| `orig-vy98` | Code-copy controls | MANUAL-BROWSER | in_progress | Manual code-copy browser review. | Browser interaction tests cover success/error/reset. |
| `orig-m83y` | Video popovers and embedded media policy | MANUAL-BROWSER | in_progress | Manual desktop/mobile/sealed-output video review. | Browser tests and no-network audits for desktop/mobile/sealed output. |
| `orig-wv4m` | Tabbed content components | MANUAL-BROWSER | in_progress | Manual desktop/mobile/accessibility tab review. | Fixtures and browser tests cover tab switching, keyboard, print, nested components. |
| `orig-3l2o` | Semantic content components | MANUAL-BROWSER | in_progress | Manual desktop/mobile/dark/print visual review. | Selector coverage, goldens, and manual review for every semantic class. |
| `orig-mzp0` | Fonts and packaged reader assets | MANUAL-BROWSER | in_progress | Browser-computed font confirmation, no-network sealed output. | Font assets deterministic, offline, verified by computed-style/browser audits. |
| `orig-4mdl` | Canonical fixture corpus and accepted goldens | AUTOMATED-HARNESS | in_progress | Build fixture corpus and accepted goldens for every reader feature. | Each fixture has accepted KPress goldens with documented approval status. |
| `orig-azna` | Manual browser acceptance playbook | MANUAL-BROWSER | in_progress | Run the playbook, record results, document deviations. | Playbook run results recorded for accepted fixtures. |
| `orig-zwc2` | Browser-backed PDF generation and fixtures | MANUAL-BROWSER | open | Real Chromium fixture PDFs, cache/report metadata, manual PDF inspection. | PDF tests and manual review prove production-ready output. |
| `orig-t2rf` | Accessibility and host-readiness checks | MANUAL-BROWSER | in_progress | Manual host iframe handling, keyboard/ARIA/contrast review. | Automated checks plus manual keyboard/mobile review pass. |

### Matrix-Specific Beads Still Open

| Bead | Title | Category | Status | Remaining work |
| --- | --- | --- | --- | --- |
| `orig-dz9t` | Ship syntax highlight themes | MANUAL-BROWSER | in_progress | Manual browser/print visual acceptance of light/dark Pygments themes. |
| `orig-4iuf` | Frontmatter-error reader affordance | MANUAL-BROWSER | in_progress | Host placement review, manual browser acceptance. |
| `orig-o2vp` | Source large-file guard | MANUAL-BROWSER | in_progress | Host adapter regression, manual source-print acceptance. |
| `orig-viq1` | Code-copy control styling | MANUAL-BROWSER | in_progress | Manual browser acceptance of position/hover/focus/copied/error states. |

### Closed Beads (Done)

| Bead | Title | Category | Status |
| --- | --- | --- | --- |
| `orig-pufr` | Production asset graph and CDN sealing | ACTIONABLE-CODE | done |
| `orig-gsre` | Production optimizer and precompressed output | ACTIONABLE-CODE | done |
| `orig-kf28` | Genericize host references in KPress docs | ACTIONABLE-CODE | done |
| `orig-5bjm` | Overlay primitive | ACTIONABLE-CODE | done |
| `orig-bkr6` | Component contract | ACTIONABLE-CODE | done |
| `orig-4uwa` | Dev/production mode removal | ACTIONABLE-CODE | done |

### Standalone Cleanup Beads

| Bead | Title | Category | Status | Remaining work |
| --- | --- | --- | --- | --- |
| `orig-hoq7` | Shrink host markdown CSS | ACTIONABLE-CODE | open | Audit the host app’s `styles.css` `.md-body` rules (in the host repo), remove KPress-redundant subset, verify plugin views. |

## Dependency-Ordered Execution Plan: ACTIONABLE-CODE Beads

These beads can be completed by an automated agent right now.

### Phase 1: Production Publishing Hardening

**`orig-pufr` (production asset graph and CDN sealing):** CLOSED.

**`orig-gsre` (production optimizer and precompressed output):** CLOSED.

The optimizer is two explicit modes only: `none` (default, no Node) and `full`
(`html-minifier-next@6.2.3` via `npx --package`; hard error if absent; no fallback; no
built-in pseudo-minifier).
Precompression is explicit, off by default, orthogonal to the optimizer.

**1. `orig-owjr` (preflight full optimizer before output)**

Remaining scope:
- Preflight the `full` optimizer at build start, before any output is written, so a
  missing `npx` fails early rather than after partial output

Files: `src/kpress/publish/optimizer.py`, `publish/build.py`

Tests: `tests/test_optimizer.py`

Acceptance test: `kpress build --optimizer full` with no `npx` fails before writing any
output files.

**2. `orig-zc7g` (locked sminify/html-minifier-next dependency layer)**

Remaining scope:
- Replace raw `npx --package` invocation with a locked dependency cache for
  `html-minifier-next`

Files: `src/kpress/publish/optimizer.py`

Tests: `tests/test_optimizer.py`

Acceptance test: optimizer `full` resolves the tool from a locked cache rather than live
`npx` resolution.

**3. `orig-aquv` (static publishing production maturity)**

Routes, sitemap, and cache-invalidation are done.

Remaining scope:
- Add publisher fixtures for shared `frontmatter-format` precedence contract

Files: `src/kpress/publish/routes.py`, `publish/build.py`, `publish/cache.py`

Tests: `tests/test_routes.py`, `tests/test_cache_invalidation.py`,
`tests/test_golden_publish.py`

Acceptance test: frontmatter-format precedence fixtures pass and routes respect
frontmatter-driven overrides.

### Phase 2: Fixture and Harness Expansion

**4. `orig-4mdl` (canonical fixture corpus and accepted goldens)**

Remaining scope:
- Build fixture documents for every reader feature (prose, headings, lists, tables,
  footnotes, tooltips, math, diagrams, images, fonts, dark mode, mobile TOC, print,
  semantic components, tabs, video)
- Add accepted goldens with fixture metadata documenting approval status

Files: `tests/fixtures/documents/`, `tests/golden/scenarios/`, `tests/golden/accepted/`

Acceptance test: each fixture has an accepted golden; `test_golden_render.py` passes.

**5. `orig-8kis` (dynamic-vs-sealed equivalence harness)**

Depends on: `orig-pufr` (closed), `orig-gsre` (closed)

Harness code is done.
Remaining scope (browser portion):
- Manual browser console/network, interaction, computed-style, mobile, dark-mode, print,
  PDF review evidence

Files: `tests/test_equivalence.py`

Note: the browser console/network/interaction/print portion of this bead’s exit
criterion falls under MANUAL-BROWSER and cannot be completed by an agent.

### Phase 3: Standalone Cleanup

**`orig-kf28` (genericize host references in KPress docs):** CLOSED.

**6. `orig-hoq7` (shrink host markdown CSS)**

Remaining scope:
- Audit the host app’s `styles.css` `.md-body` rules (in the host repo)
- Remove reader-only subset that KPress replaced
- Keep the other plugin subset
- Verify structured plugin views visually

Files: the host app’s `styles.css` (host repo)

Acceptance test: `styles.css` net-reduced; lmdb views render correctly.

## Manual Browser Acceptance Process

This section describes exactly how to discharge the MANUAL-BROWSER beads using the
existing validation runbook at `docs/kpress-validation.runbook.md`.

### Prerequisites

- A real Chromium-based browser (Playwright-driven or manual).
- The KPress static site built via Part 4 of the runbook.
- For PDF beads: `uv pip install 'kpress[pdf]'` and `playwright install chromium`.
- A way to capture evidence (screenshots, console logs, or written observations).

### Execution Order

Run acceptance in this order, because later groups depend on earlier visual baselines.

**Round 1: Typography, themes, and layout foundations**

Beads: `orig-vdbu`, `orig-dz9t`, `orig-mzp0`

1. Serve the production static site (runbook Part 5, “Local Browser Smoke”).
2. Review prose typography, heading scale, font rendering (PT Serif body, Source Sans
   headings), and punctuation fallback on the rich-components fixture page.
3. Toggle System/Light/Dark theme: confirm no flash on reload, localStorage persistence,
   correct color tokens in each mode.
4. Check dark mode component coverage: code blocks, tables, TOC, tooltips, details.
5. Open DevTools, inspect computed font families for body, headings, mono, and
   punctuation elements.
6. Record evidence: screenshots of light, dark, and system modes; computed-style
   font-family values.

Maps to closing: `orig-vdbu`, `orig-dz9t` (syntax highlight visual confirmation),
`orig-mzp0` (computed font confirmation).

**Round 2: Document tree and content rendering**

Beads: `orig-97c1`, `orig-1rc7`, `orig-oxs3`, `orig-c5xy`, `orig-g0ra`, `orig-lir6`,
`orig-3l2o`, `orig-4iuf`, `orig-o2vp`

1. Open the rich-components fixture and any supplemental fixtures from the corpus.
2. Verify GFM tables, nested lists, blockquotes, task lists, strikethrough, footnote
   refs/backrefs, code fences with syntax highlighting, and heading anchors.
3. Verify images render with lazy loading, figures have captions, and local assets seal
   when `asset_mode: sealed`/`hashed` is selected.
4. Verify math behavior: no-math fixtures load no math assets; `off` leaves delimiters
   literal; math fixtures render inline/display equations through KaTeX while preserving
   MathML as semantic/accessibility output.
5. Verify SVG diagrams render inline; Mermaid figures show source fallback without a
   host-provided Mermaid library.
6. Verify semantic components (`.highlight`, `.citation`, `.summary`, `.concepts`,
   `.hero`, `.boxed-text`, etc.)
   have visible styling.
7. Verify frontmatter-error documents show the in-document alert.
8. Verify large source files show the truncation warning.
9. Verify raw HTML trust modes: safe HTML preserved, unsafe stripped.
10. Record evidence: screenshots of each content type.

Maps to closing: `orig-97c1`, `orig-1rc7`, `orig-oxs3`, `orig-c5xy`, `orig-g0ra`,
`orig-lir6`, `orig-3l2o`, `orig-4iuf`, `orig-o2vp`.

**Round 3: Interactive components**

Beads: `orig-i4rj`, `orig-o59o`, `orig-2z84`, `orig-09i3`, `orig-vy98`, `orig-m83y`,
`orig-wv4m`, `orig-viq1`

1. **TOC (desktop):** confirm sticky rail, active heading highlight on scroll, smooth
   scroll to heading, “Contents” scroll-to-top, progressive toggle visibility on
   non-first-section pages.
2. **TOC (mobile):** resize to narrow viewport; confirm drawer opens/closes, backdrop
   dismisses, body scroll locks, iOS overscroll prevention works.
3. **Tooltips:** hover footnote refs to confirm HTML preview, truncation, nav link,
   delayed hide, moving-toward timing.
   Hover internal links for heading/figure/table/code previews.
   Test Escape close. Test touch behavior on mobile.
4. **Tables:** verify responsive wrapping on wide tables, numeric cell alignment,
   small-caps headers, zebra rows, TOC-aware desktop breakout, mobile font reduction.
5. **Code copy:** click copy buttons on multiple code blocks; confirm idle/copied/error
   state transitions, two-second reset, print-hidden behavior.
6. **Video popovers:** click a YouTube link; confirm popover opens, maximize/restore
   toggles, close/Escape works, TOC hides/restores.
   On mobile: confirm body lock.
   In sealed output: confirm no eager YouTube network requests.
7. **Tabs:** click tab buttons; confirm active/inactive state, keyboard arrow
   navigation, ARIA roles.
   In print preview: confirm all panels show with titles.
8. Record evidence: interaction screenshots, console logs.

Maps to closing: `orig-i4rj`, `orig-o59o`, `orig-2z84`, `orig-09i3`, `orig-vy98`,
`orig-m83y`, `orig-wv4m`, `orig-viq1`.

**Round 4: Print and PDF**

Beads: `orig-boxw`, `orig-zwc2`

1. Open print preview (Command+P or `window.print()`).
2. Verify: page margins/footer/page-number, light paper palette, heading/table/code
   break avoidance, orphans/widows, ordered-list grid alignment, footnote
   simplification, code wrapping, TOC/video/copy-button suppression, print-only surfaces
   visible.
3. Generate browser-backed PDFs for the fixture corpus:
   `uv run kpress export fixture.md --pdf fixture.pdf` (requires `kpress[pdf]` and
   Chromium).
4. Open each PDF. Verify page breaks, wide tables, footnotes, images, math, diagrams,
   fonts, and print-only controls.
5. Record evidence: print preview screenshots, PDF file hashes, and visual observations.

Maps to closing: `orig-boxw`, `orig-zwc2`.

**Round 5: Accessibility and host readiness**

Beads: `orig-t2rf`, `orig-azna`

1. Keyboard-navigate the document: Tab through TOC, tooltips, tabs, popovers, theme
   toggle, code-copy buttons.
   Confirm focus visibility and ARIA roles.
2. Run a contrast check on light/dark/print modes.
3. Confirm `prefers-reduced-motion` suppresses transitions.
4. Open in the embedding host: confirm `kpress:ready`/`kpress:resize`/`kpress:expand`/
   `kpress:close` postMessage events fire correctly.
   Confirm Escape-close opt-in.
5. Run through the full runbook Part 6 checklist.
6. Record the completed Part 6 checklist as the playbook evidence for `orig-azna`.

Maps to closing: `orig-t2rf`, `orig-azna`.

**Round 6: No-network sealed output review**

1. Serve the production static site with network disabled (or monitor DevTools Network
   tab).
2. Confirm zero unexpected remote requests.
3. Confirm all assets load from local hashed files.
4. This satisfies the no-network portions of `orig-pufr`, `orig-8kis`, and `orig-mzp0`.

### Evidence Format

For each round, record:
- Date and operator.
- Browser and version.
- Viewport dimensions tested (desktop and mobile).
- Pass/fail per checklist item, with screenshots or console excerpts for failures.
- File the evidence alongside the bead closure (in bead notes or a linked review doc).

## Closure Chain

### From feature beads to `orig-08y5` (final audit/closure gate)

`orig-08y5` depends on (blocks) `orig-xgzj`. It closes when:

1. Every child feature bead of `orig-xgzj` is closed.
2. Every row in the parity ledger (moved to the 2026-05-18 MVP stability plan spec)
   reads **Implemented**.
3. Tests, goldens, and browser checks are linked per row.
4. Manual approvals are recorded.
5. `TODO.md` has no open reader-parity feature gaps.

### From `orig-08y5` to `orig-xgzj` (epic)

`orig-xgzj` (reader parity epic) closes when `orig-08y5` and all other child beads are
closed.

### Full closure dependency order

Phase A (can proceed in parallel):
- CLOSED: `orig-pufr`, `orig-gsre`, `orig-kf28`, `orig-5bjm`, `orig-bkr6`, `orig-4uwa`
- ACTIONABLE-CODE beads: `orig-owjr`, `orig-zc7g` (optimizer hardening)
- ACTIONABLE-CODE beads: `orig-aquv` (frontmatter precedence remains)
- ACTIONABLE-CODE beads: `orig-hoq7` (host CSS shrink)
- ACTIONABLE-CODE + MANUAL-BROWSER: `orig-g0ra` (math off+lazy-auto KaTeX refactor)
- AUTOMATED-HARNESS: `orig-4mdl` (fixture corpus)

Phase B (requires real browser, depends on Phase A fixture corpus):
- MANUAL-BROWSER Rounds 1-6 (all reader feature beads)
- `orig-azna` closes when the playbook has been run and results recorded
- `orig-zwc2` closes when real Chromium PDFs pass manual inspection

Phase C (gates, close automatically when children close):
- `orig-8is3`, `orig-131h`, `orig-d6g2`, `orig-selz`, `orig-5dmd`, `orig-n7ok`,
  `orig-0xa1` close when their child feature beads close.
- `orig-q72a` closes when the acceptance playbook, fixture corpus, and browser checks
  are complete.

Phase D (final):
- `orig-08y5` closes (final audit gate).
- `orig-xgzj` closes (reader parity epic).
- `orig-wkzp` closes (package/publisher epic).

## What an Automated Agent Cannot Do and Why

An automated agent (Codex, Claude Code, or similar headless CI) can write Python,
JavaScript, CSS, tests, goldens, fixtures, documentation, and configuration.
It can run pytest, Ruff, basedpyright, Biome, `tsc --checkJs`, and Vitest with
happy-dom.

It cannot:

1. **Render fonts visually.** Font rendering is OS/browser-dependent.
   An agent cannot confirm PT Serif renders correctly, that punctuation fallback works,
   or that small-caps are visually correct.
   jsdom/happy-dom do not render fonts.

2. **Judge visual layout quality.** Prose width, heading spacing, line height, color
   contrast, and overall “readability” require human visual judgment.
   Computed-style assertions can check declared values, but cannot confirm the rendered
   result looks right.

3. **Test real touch/mobile behavior.** iOS overscroll prevention, mobile drawer
   gestures, touch tooltip dismissal, and narrow-viewport overflow all require a real
   mobile browser or mobile emulation with visual confirmation.

4. **Confirm dark mode has no flash.** The pre-paint bootstrap prevents FOUC, but
   proving “no flash” requires watching a page load in a real browser.

5. **Inspect print preview and PDF output.** Print CSS behavior (page breaks, margins,
   orphans/widows, ordered-list grid alignment) must be visually confirmed in a browser
   print preview or a generated PDF. There is no headless DOM API for “does the print
   preview look correct.”

6. **Verify no-network sealed output.** While an agent can grep for remote URLs, the
   definitive proof is loading the site in a browser with the network tab open (or
   network disabled) and confirming zero unexpected requests.

7. **Run Playwright with a real Chromium install.** The KPress test suite intentionally
   does not require Playwright or Chromium in CI. Browser-backed PDF generation and the
   manual acceptance playbook both require `kpress[pdf]` plus a locally installed
   Chromium, which an automated agent in a sandboxed environment typically cannot
   provide.

8. **Make subjective design decisions.** Whether the mono web font divergence from Kash
   is acceptable, whether KaTeX should be client-rendered only or also pre-rendered in
   production builds, and whether bundled Mermaid belongs in the package are human
   product decisions.

The beads categorized as MANUAL-BROWSER are blocked on items 1-7 above.
The ACTIONABLE-CODE beads can and should be completed by an agent first, so that the
manual browser acceptance rounds have complete fixture coverage and production-quality
output to review.

## Bead Categorization Summary

| Category | Count |
| --- | --- |
| CLOSED | 6 (`orig-pufr`, `orig-gsre`, `orig-kf28`, `orig-5bjm`, `orig-bkr6`, `orig-4uwa`) |
| ACTIONABLE-CODE (open/in_progress) | 5 (`orig-owjr`, `orig-zc7g`, `orig-aquv`, `orig-hoq7`, plus code portion of `orig-g0ra`) |
| AUTOMATED-HARNESS | 2 (`orig-4mdl`, `orig-8kis`, both also have MANUAL-BROWSER exit criteria) |
| MANUAL-BROWSER | 24 (all reader feature beads, matrix beads, `orig-azna`, `orig-zwc2`, `orig-t2rf`) |
| GROUPING/GATE | 11 (`orig-xgzj`, `orig-wkzp`, `orig-mfwo`, `orig-08y5`, `orig-8is3`, `orig-131h`, `orig-d6g2`, `orig-selz`, `orig-5dmd`, `orig-n7ok`, `orig-0xa1`) |

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->

## Current Implementation Status

The current package slice is the first end-to-end implementation of the package
boundary. It proves dynamic rendering, static build, workflow, asset, quality-gate, PDF,
and golden-test paths, but it is not yet the full source-port of the TextPress/Kash
document client. The package-local implementation ledger is [`TODO.md`](../TODO.md).

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
- asset sealing (document-local asset copying, external URL fetching and
  integrity-pinning, HTML/CSS/JS URL rewriting, and offline tree verification) is
  deferred to v2 (see “Asset Model” below); v1 leaves document-local and external refs
  in the rendered HTML verbatim and lets the deploy layer own delivery
- browser-backed PDF generation

Parity closure rule: KPress reader/doc-format parity is not complete until every row in
the format feature ledger has accepted KPress fixtures, automated checks for stable
structure/package behavior, and explicit manual confirmation for
visual/mobile/dark/print/PDF quality where listed.

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

## Planned Dependency Tiers

The extras that exist today are `kpress[pdf]` and `kpress[optimize]`. Planned dependency
tiers:

| Tier | Scope |
| --- | --- |
| `kpress` | Markdown/simple HTML rendering, package assets, dynamic fragments, static build basics, HTML export |
| `kpress[import]` | DOCX/PDF/URL/rich HTML import adapters |
| `kpress[clipboard]` | clipboard paste workflow |
| `kpress[pdf]` | browser-backed PDF generation |
| `kpress[office]` | DOCX export |
| `kpress[optimize]` | Brotli (`br`) precompression sidecars |
| `kpress-publish` | hosted login, upload, and public service URLs |

## Asset Sealing v2 Roadmap

What v2 sealing should look like (when it returns):

- Drive the asset graph through a **real parser** (selectolax/lxml + tinycss2 for the
  Python-side option, or—preferred—delegate to a JS bundler at the publish step).
  Stop reinventing HTML/CSS parsing in regex.
- Keep sealing strictly opt-in (`asset_mode=sealed` plus an explicit fetcher config).
  Default `asset_mode` stays `linked` / `hashed`, which require zero network access at
  build time.
- Make the bundler step a clean optional extra (e.g. `kpress[bundle]`) so users who
  don’t need sealing never install Node tooling.

Tracking beads: `orig-t3ud` (v1 removal) and `orig-mfvi` (v2 design).

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

## Tailwind Migration Record

The Kash/TextPress reference templates used Tailwind (the `@tailwindcss/browser` CDN and
utility classes such as `container`, `max-w-3xl`, `mx-auto`, `bg-white`, spacing
utilities, `hidden`, `flex`, and text sizing).
The migration replaced every active utility with semantic KPress classes and CSS
variables; KPress ships no Tailwind runtime, generated CSS, or build step, and
`tests/test_asset_contract.py` guards shipped assets against any Tailwind reference.
The migration inventory fixture and its test were retired when the migration completed.

| Reference utility | KPress-owned replacement | Behavior preserved |
| --- | --- | --- |
| `container`, `max-w-3xl`, `mx-auto` | `.kpress-long-text` | centered readable document width |
| `bg-white` | `.kpress-long-text` | paper background for the document content surface |
| `py-4`, `px-6`, `md:px-16` | `.kpress-long-text` | mobile and tablet document padding |
| `flex`, `items-center` | `.kpress-header-row`, `.kpress-header-actions` | centered horizontal header/action layout |
| `flex-grow`, `ml-2` | `.kpress-header-grow` | expanding header/nav region with small inline gap |
| `ml-auto` | `.kpress-header-actions` | action cluster pushed to the inline edge |
| `mt-6` | `.kpress-page-spacer` | top spacing before main page content |

## Conscious Departures from kash/textpress

KPress mirrors the kash/textpress design system for TOC, tooltips, footnotes, and serif
typography (the visual-parity reconciliation spec
`plan-2026-06-01-kpress-visual-polish.md`, with the full divergence matrix in its
evidence file, lives in the originating monorepo’s spec archive).
Parity is pinned by
`tests/test_asset_contract.py::test_visual_parity_css_contract_pins_kash_reconciliation`
and the golden/DOM suites.
The following divergences are **intentional and approved**: do not “fix” them toward
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
4. **Single-tooltip architecture:** one tooltip created on demand and removed on hide,
   vs kash’s persistent pre-created map.
   More memory-efficient.
5. **`<aside role="tooltip">`** instead of a `<div>` (semantic upgrade).
6. **Focus/blur tooltip triggers** for keyboard accessibility (kash lacks this).
7. **Escape and resize dismiss** for tooltips.
8. **`<section class="kpress-footnotes">`** wrapper instead of
   `<div class="footnotes">`.
9. **Footnotes-section container styling** (border-top, muted, 0.9em): kash has none.
10. **Dual active-state signal** on TOC links (`data-active` attribute + `.active`
    class) so embedding hosts get an attribute hook.
11. **Cool-blue primary in the default palette:** the link/primary stays the KPress blue
    (`oklch(45.76% 0.1445 254.7)`, was `#0756a5`), not kash’s teal, with fully-opaque
    tokens; the kash `--color-*` token *names* are provided but mapped to KPress values.
    This departure applies to the default `neutral` palette only: the `warm` preset
    keeps kash/textpress’s teal link (exact conversion) atop a warm-rotated neutral
    structure (see the palette presets in [kpress-design.md](../kpress-design.md)).
12. **Blue-based dark palette** (same hue choice in dark mode; `neutral` only, as with
    #11).
13. **Sans on the `.kpress` wrapper, serif only inside `.kpress-prose`:** UI chrome is
    sans, body prose is serif.
14. **No global scrollbar styling** (KPress is an embeddable fragment, not a page).
15. **No `html { overflow-x: hidden }}`** (KPress is a fragment, not a full page).
16. **Modernized font fallback chains** (`system-ui`/`Georgia` named fallbacks).
17. **No Hack Nerd Font** (a desktop icon font, inappropriate for the web).
18. **Responsive image constraints** (`height: auto; max-width: 100%`).
19. **TOC levels 5–6** styled (kash stops at 4) for deep heading hierarchies.
20. **Viewport `overflow: hidden` scroll lock** for the open drawer, instead of kash’s
    `body { position: fixed }`, correct for container-scoped scrolling.
21. **Proactive top-right tooltip flip** decided at selection time rather than a
    deferred bounds check.
22. **`print.css` dual-class selectors** (both `kpress-`-namespaced and legacy kash
    class names) for defensive compatibility.
23. **Tooltip sizing hardcoded** rather than exposed as CSS custom properties (simpler;
    hosts cannot override tooltip dimensions, an accepted trade-off).
24. **`kpress-footnote-nav` / `kpress-footnote-nav-link` classes** instead of reusing
    kash’s `.footnote` class (avoids kash’s `display: none` override hack).

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
| `orig-t3ud` | remove asset sealing for v1; defer to v2 roadmap | open; epic: strips regex-driven HTML/CSS/JS rewriter from v1, keeps package-asset copying, parks sealing on the v2 roadmap (real parser or JS bundler). See `docs/project/specs/active/plan-2026-05-21-kpress-remove-sealing-for-v1.md` |
| `orig-mfvi` | v2 sealing: real parser or JS bundler over the asset graph | open; v2 roadmap: drives HTML/CSS/JS through a real parser or delegates to Vite/Parcel/esbuild/Bun at publish; restores `verify_offline_tree` and air-gapped `Static build sealed` mode |

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

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
