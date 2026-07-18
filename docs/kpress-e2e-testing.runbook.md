# KPress End-to-End Testing Runbook

Manual, browser-based end-to-end testing for a **standalone KPress document**: the
interactive and visual behavior that automated tests cannot fully confirm (real
rendering, layout, theming, animation, focus, print).

This is the single home for KPress manual e2e testing.
It does **not** repeat the automated gates (lint, pytest, golden, JS-DOM) or the
CLI/publishing checks.
Those live in [kpress-validation.runbook.md](./kpress-validation.runbook.md).
For KPress **embedded in a host**, use the host application’s own e2e runbook
(maintained in that application’s repo).

Each step is tagged:

- **[Agent]:** an agent can drive and confirm this by serving the page and inspecting
  the DOM, console, network, and computed styles (e.g. via a browser tool or DevTools).
- **[Human]:** needs a person’s eyes: visual appearance, font rendering, animation feel,
  print preview, real PDF.

## Automated Coverage

- **Golden HTML** (`tests/golden/accepted/*/page.html`) pins the rendered markup,
  including the settings menu, footnote, and table structure.
  Run `uv --config-file uv.toml run --frozen pytest tests/test_golden_render.py`.
- **Browserless DOM tests** (`tests/js/*.test.js`, Vitest and happy-dom) pin theme
  switching, gear open/close, TOC scroll and drawer behavior, tooltip positioning,
  code-copy states, video popovers, and tabs.
  Run `npx --no-install vitest run --config tests/js/vitest.config.mjs`.
- **Asset/contract tests** pin the public CSS classes, CSS variables, and required
  selectors.

This runbook is for what those cannot see: that it actually *looks and feels right* in a
real engine.

## Setup

All commands run from the repo root.

The review surface is the **reader showcase** at `tests/e2e/`: one document that
exercises every reader feature, plus a second page for cross-page navigation.
It is *not* a golden fixture (so it can stay rich); the golden fixtures under
`tests/fixtures/documents/` stay minimal for byte-stable comparison.

Render it three ways.
The standalone and production builds use hashed assets; the readable build uses stable
linked names:

```bash
rm -rf /tmp/kpress-e2e && mkdir -p /tmp/kpress-e2e

# 1) Single standalone document. Its complete output directory contains the HTML,
#    package assets, any required KaTeX files, and eligible local document images.
uv --config-file uv.toml run --frozen kpress render \
  tests/e2e/docs/index.md \
  --output /tmp/kpress-e2e/showcase.html --asset-mode hashed

# 2) Readable static site with linked assets. The fixture declares its document images
#    through sources[].static, so figures resolve from the output root.
uv --config-file uv.toml run --frozen kpress build \
  --config tests/e2e/kpress.yml \
  --output-dir /tmp/kpress-e2e/site-readable --asset-mode linked

# 3) Production-style static site with hashed assets and the optional full optimizer.
uv --config-file uv.toml run --frozen kpress doctor --profile optimize --allow-network
uv --config-file uv.toml run --frozen kpress build \
  --config tests/e2e/kpress.yml \
  --output-dir /tmp/kpress-e2e/site-hashed --asset-mode hashed --optimizer full
```

Serve over **HTTP, not `file://`**: KPress JS uses ES module imports, which browsers
block on `file://`. A single rendered document uses *relative* asset URLs, so serve its
directory:

```bash
# Single document: serve /tmp/kpress-e2e, open showcase.html
( cd /tmp/kpress-e2e && python3 -m http.server 8799 )
# → http://127.0.0.1:8799/showcase.html
```

A built **static site uses root-absolute asset URLs** (`/_kpress/assets/...`), so it
must be served **from its own root**, not a parent directory (serving the parent makes
every asset 404 → an unstyled fragment):

```bash
( cd /tmp/kpress-e2e/site-readable && python3 -m http.server 8800 )   # → http://127.0.0.1:8800/
( cd /tmp/kpress-e2e/site-hashed   && python3 -m http.server 8801 )   # → http://127.0.0.1:8801/
```

The showcase’s “Reference” link (`reference.html`) resolves in the two **site** builds.
The standalone render contains the link but does not emit the sibling page, so do not
include that link in the standalone crawl.
The minimal golden fixtures (`rich-components.md`, `semantic-components.md`,
`minimal.md`) remain available if you want a smaller surface.

## First Load

- **[Agent]** Open the page; the console has **no errors** and **no** “no
  `[data-kpress-viewport]` ancestor” warning (the standalone shell marks its own
  viewport).
- **[Agent]** The Network tab shows every CSS/JS/font asset resolving **200** (no 404s).
- **[Human]** The document renders as a centered reading column with serif body text.

## Settings Menu

The only theme control is a gear-icon popover in the top-right; there is **no text
`System | Light | Dark` chooser** anywhere.

- **[Human]** A gear icon sits top-right, legible in both light and dark backgrounds.
- **[Agent]/[Human]** Click the gear → a dropdown opens with three **icon** segments
  (monitor = system, sun = light, moon = dark).
  The segment matching the current theme is **highlighted** (link-colored icon + tint).
- **[Agent]/[Human]** Click each segment → the theme switches immediately and the active
  highlight moves. Click outside the menu or press **Escape** → it closes.
- **[Agent]** Selecting a theme writes `localStorage["kpress.theme"]`; **reload** → the
  choice persists (the pre-paint bootstrap applies it with no flash).
- **[Agent]** `aria-expanded` toggles on `.kpress-settings`; the active segment carries
  `aria-checked="true"`.

## Theme and Dark Mode

- **[Human]** In **dark** mode the **entire window** is dark—not just the reading
  column. (`.kpress-page-main` carries the document background.)
  No light gutters beside the article.
- **[Human]** Body text, headings, links, code blocks, tables, TOC, tooltips, and the
  gear menu are all themed coherently in light and dark.
- **[Agent]/[Human]** With the gear set to **system**, change the OS appearance → the
  page follows without reload.

## Typography

- **[Human]** The document **title** is regular-weight serif, sized a notch below a
  giant hero (not bold, not oversized).
- **[Human]** Body prose is serif; UI chrome (TOC, tables, captions, tooltips,
  footnotes) is sans. Headings follow the type scale.

## Table of Contents

- **[Human]/[Agent]** Desktop: a sticky TOC rail; the active entry highlights as you
  scroll; clicking an entry smooth-scrolls to the heading.
- **[Human]/[Agent]** Clicking a TOC entry (or any in-document section link) **updates
  the URL hash** and pushes a history entry; the address bar is a shareable deep link.
  **Back** returns to the pre-click scroll position; **Forward** returns to the section.
  With OS reduced-motion enabled, the section jump is instant, not animated.
- **[Human]/[Agent]** Clicking the TOC **Contents** (top) link **clears the section hash
  from the URL** and pushes a history entry while the pane scrolls to the top; **Back**
  returns to the position (and hash) from before the top jump.
- **[Human]/[Agent]** Narrow the window → the TOC collapses to a drawer toggle.
  Open it → body scroll **locks** behind it; a backdrop appears; **Escape**,
  outside-click, or the toggle closes it and scroll position is preserved.

## Footnotes

- **[Human]/[Agent]** Footnote reference markers render as **sequential superscript
  numbers** (1, 2, 3 …) that **match the numbers** in the footnotes section at the
  bottom, even when the markdown labels are words (`[^one]`). The anchor still targets
  the label (`#fn-one`). (Markers are pill-styled and sans.)
- **[Agent]/[Human]** Hover or click a footnote ref → a tooltip appears with a **solid**
  background (no bleed-through of text behind it) in **sans**, positioned within the
  viewport.
- **[Human]** The footnotes section at the bottom renders in **sans** (matching the
  tooltip), with its top border and muted color.
- **[Agent]/[Human]** Resize the window with a tooltip open → it dismisses.

## Internal-Link Tooltips

- **[Agent]/[Human]** Hover an internal link (to a heading/figure/table/code) → a
  preview tooltip appears, viewport-aware (never clipped off-screen), with an arrow
  toward the trigger. Touch devices get a tap fallback; **Escape** closes.

## Tables

- **[Human]** Tables render with small-caps headers and zebra rows; numeric cells align.
- **[Human]/[Agent]** A wide table scrolls horizontally on narrow widths; on desktop
  with a TOC it may break out to the full reading width.

## Code Blocks and Copy

- **[Human]** Code blocks are syntax-highlighted (light and dark stylesheets).
- **[Human]/[Agent]** Each code block has a **copy icon** control (not a text “Copy”
  box). Click it → the clipboard receives the code and the control shows a transient
  success state; an error state is reachable if the clipboard API is blocked.

## Video Popovers

- **[Agent]/[Human]** A YouTube link / embed renders as a no-network placeholder.
  Click it → a focus-trapped dialog opens; the TOC hides while it is open and restores
  on close. Maximize/restore works; **Escape** and the close control dismiss it.
- **[Agent]** In the **hashed fixture** build, opening the page makes **no** eager
  network calls; the YouTube embed URL is only constructed on click.

## Tabs, Math, and Diagrams

- **[Human]/[Agent]** Tabbed containers hydrate into an ARIA tablist with keyboard
  support.
- **[Human]** Math renders via KaTeX (when present); documents with no math load no math
  assets. SVG/Mermaid fences render as figures with a readable source fallback.

## Print and PDF

- **[Human]** Print preview (**Cmd/Ctrl+P**): light paper palette; the TOC, gear menu,
  video popovers, and copy controls are suppressed; tables and source blocks are not
  clipped; footnotes simplify; sensible page breaks.
- **[Human]** Optional real PDF (requires the locked `kpress[pdf]` extra and a reviewed
  Chromium download):
  `uv --config-file uv.toml run --frozen playwright install chromium`, then
  `uv --config-file uv.toml run --frozen kpress export <doc>.md --pdf /tmp/out.pdf`.
  Inspect content, fonts, tables, and page breaks.
  Absence of Playwright must give a clear error, never a silent downgrade.

## Static Site Checks

- **[Agent]** Readable and hashed sites load from their **own root**; all assets
  resolve; `/` and `/reference.html` navigation works.
- **[Agent]** This **hashed fixture** makes **no eager external asset loads**. Check the
  *asset* references—`src`/`href` on `<script>`, `<link>`, `<img>`, `<iframe>`—resolve
  locally; the only allowed external URL is the YouTube embed template inside
  `video-popover.js` (a deliberate click-time feature, not a load-time call).
  Author hyperlinks (`<a href="https://…">`) and XML namespaces
  (`xmlns="http://www.w3.org/…"`) are content, not network loads, so a blanket grep for
  `http(s)://` will list them.
  That is expected, not a violation.

## Responsive Layout and Accessibility

- **[Human]/[Agent]** Resize from narrow (mobile) to wide (>1200px): the layout, TOC,
  tooltips, and tables adapt; nothing overflows the window.
- **[Human]/[Agent]** Keyboard-only: every control (gear menu, TOC drawer, tabs, video
  dialog, copy) is reachable and operable; focus rings are visible; **Escape** closes
  overlays; no incoherent focus traps.
- **[Agent]** With `prefers-reduced-motion: reduce`, transitions/animations are
  suppressed.

## Remaining Automation Candidates

When a check below becomes a deterministic test, delete it from the manual list above:

- CLI/diagnostic goldens: `kpress doctor --json`, render diagnostics payloads.
- A headless-Chromium visual/smoke check (opt-in, never required CI) for theme,
  dark-mode-fills-viewport, and tooltip background—the highest-value [Human] items.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
