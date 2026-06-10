---
title: KPress Completion Plan
description: Dependency-ordered map of all remaining work to bring KPress to verified end-to-end completion, including the manual browser acceptance process.
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

**`orig-pufr` (production asset graph and CDN sealing)** — CLOSED.

**`orig-gsre` (production optimizer and precompressed output)** — CLOSED.

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

**`orig-kf28` (genericize host references in KPress docs)** — CLOSED.

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
