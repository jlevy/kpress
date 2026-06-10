# KPress TODOs

This file is the package-local implementation status ledger for KPress.
The plan specs remain the detailed source of truth; this file keeps the current package
state readable without scanning every design document.

Last reviewed: 2026-06-05 (spec/TODO consolidation tracked as `trading-x1sb`). The
2026-06-05 pass folded the open-source packaging-readiness assessment + static-publish
(SSG) workflow analysis into the umbrella spec — see
[Open-Source Packaging Readiness](../../docs/project/specs/active/plan-2026-05-16-kpress-package-and-publisher.md#open-source-packaging-readiness)
and the SSG/deploy-sync decision (`trading-en4h`). Verdict: the dependency graph and the
MetaBrowser↔KPress contract are clean and test-enforced (past the “too intermingled”
risk); remaining is reader parity, the host-contract finalization (`trading-0xa1`), and
final release metadata (`trading-ljov`). Channel decided 2026-06-05: **PyPI** (npm is
out of scope).

**2026-06-06 — kpress goes first (epic `trading-iwz6`).** kpress is pulled out first as
a standalone, highly reusable, clean document renderer with **zero TableView
dependency**, consumable by static-site builders, MetaBrowser, and any TableView user.
The “pull-out / OSS-ready” sign-off is gate bead `trading-z5lf` (depends on parity
`trading-08y5`, the single-renderer cutover `trading-r3g8`, host contract
`trading-0xa1`, release metadata `trading-ljov`, the new reuse/enrichment contract
`trading-m5ao`, and design-system consolidation `trading-evta`). New seam: kpress emits
a renderer-agnostic table enrichment contract (`data-col` + a tiny YAML-frontmatter
binding, `trading-m5ao`) that downstream layers decorate; kpress never imports a
decorator and never knows TableView exists.
TableView is layered **above** kpress as a MetaBrowser plugin (`trading-ebsr`, v2),
never the reverse. Direction validated by spike `trading-0b6g`.

## Cleanup & Consolidation (top priorities)

Trailing tech debt and spec confusion to retire, highest-leverage first.

1. **Keep reader-parity ledgers collapsed.** `kpress-reader-features.md` is the durable
   feature catalog; this TODO keeps only routing and top-level blockers; the active
   umbrella spec points here instead of carrying another feature-status table.
2. **Document the KPress relationship to prior TextPress/Kash reader behavior in one
   place.** KPress is adapted from prior TextPress/Kash reader behavior; see §
   Source-Port References below.
   It is easy to be confused about which is canonical and whether the upstream is still
   maintained. Add a short “Provenance & relationship to TextPress/Kash” note to
   `kpress-design.md`: kpress is the canonical reader for this monorepo; the
   TextPress/Kash files are the source-port origin, not a live dependency; the
   host-neutral TOC work (2026-06-01) moved kpress *past* a straight port (container
   queries + a `data-kpress-viewport` integration seam the upstream doesn’t have).
3. **Finish reader parity → enable the metabrowser single-renderer cutover.** The
   remaining open work is manual reader-parity acceptance (visual/PDF review) and font
   sealing. Closing it unblocks deleting metabrowser’s `marked` fallback renderer
   (metabrowser TODO item 2) and promoting kpress to a hard dependency.
4. **Generalize the `data-kpress-viewport` seam to the other window-coupled behaviors.**
   The 2026-06-01 TOC work introduced a shared `ScrollContext` + viewport seam so the
   TOC is host-neutral.
   The overlay/resize/tooltip/video-popover viewport seam landed under `trading-2gjm`
   (closed): `viewport.js` is packaged as a transitive ESM asset and the floating UI
   shares viewport context.
   The footnote/internal-link tooltip wiring on host-injected fragments — a concrete
   instance of the same drift — is fixed under `trading-16rg` (commit `c41c611a2`,
   MutationObserver + idempotent wiring; pending final visual confirmation in
   MetaBrowser). Confirm `overlay.js`/`tooltips.js`/ `video-popover.js` are fully
   migrated before deleting the host fallback.
   Original fast-follow context:
   [plan-2026-06-01-kpress-reusable-toc-and-scroll-context.md](../../docs/project/specs/done/plan-2026-06-01-kpress-reusable-toc-and-scroll-context.md),
   now in `done/`.

**Design-system consolidation (active 2026-06-04).** KPress is the batteries-included
design layer for document visualization.
The gear settings menu, body-level overlay token-scoping, and footnote/title/font fixes
landed in `b2cd4ec4d`; icons moved to a documented Lucide set
([`kpress-icons.md`](kpress-icons.md)) and now live as one SVG sprite
(`format/static/icons/icons.svg`) referenced via `<use>` from both server and client —
no SVG geometry in Python or JS. The code-copy/video-close affordances are icon-ized.
Remaining design-system work — the standalone single-scroll-context fix, numbered
footnote superscripts, and MetaBrowser icon/button alignment — is tracked in
[plan-2026-06-04-kpress-metabrowser-design-system-consolidation.md](../../docs/project/specs/active/plan-2026-06-04-kpress-metabrowser-design-system-consolidation.md).
Manual browser e2e validation is codified in
[docs/kpress-e2e-testing.runbook.md](docs/kpress-e2e-testing.runbook.md).

**Spec consolidation done (2026-06-04):**

- `plan-2026-06-01-kpress-visual-polish.md` → **moved to `done/`** (all 6 reconciliation
  phases + the departures-registry codification shipped in `5e4f429a1` / `3685c99c9`;
  CSS pinned by `test_visual_parity_css_contract_pins_kash_reconciliation`).
- `evidence/parity-audit-2026-06-01-kpress-vs-kash.md` → **moved to `done/evidence/`**
  (historical audit artifact for the visual-polish spec; no live tracking role).

**Spec consolidation done in earlier pass (2026-06-01):**

- `plan-2026-05-18-kpress-mvp-stability-and-doctor.md` (doctor + MVP closeout) and
  `plan-2026-06-01-kpress-reusable-toc-and-scroll-context.md` (host-neutral TOC) →
  **moved to `done/`** (shipped).
- `plan-2026-05-21-kpress-remove-sealing-for-v1.md` → **moved to `done/`** (sealing
  removed for v1; v2 roadmap captured in `kpress-design.md`).
- `plan-2026-05-21-kpress-seal-decomposition.md` → **archived** (it was an intermediate
  refactor, superseded by the removal above; self-declared obsolete).
- `plan-2026-05-16-kpress-package-and-publisher.md` stays the **active umbrella** and
  now points to the reader catalog, parity matrix, readiness cleanup spec, and tbd beads
  instead of duplicating the live parity ledger.

## Source Documents

| Document | Role | Current status |
| --- | --- | --- |
| [`kpress-design.md`](kpress-design.md) | Architecture and public contract (no status ledger) | Current; status ledger moved out |
| [`kpress-reader-features.md`](kpress-reader-features.md) | Long-lived reader feature catalog (no status) | Current |
| [`kpress-icons.md`](kpress-icons.md) | Icon set contract + origins (Lucide) | Current |
| [`docs/kpress-e2e-testing.runbook.md`](docs/kpress-e2e-testing.runbook.md) | Manual browser e2e validation runbook | Current |
| [`../../docs/project/specs/active/plan-2026-06-04-kpress-metabrowser-design-system-consolidation.md`](../../docs/project/specs/active/plan-2026-06-04-kpress-metabrowser-design-system-consolidation.md) | KPress + MetaBrowser design-system consolidation plan | Active |
| [`../../docs/project/specs/done/plan-2026-05-18-kpress-mvp-stability-and-doctor.md`](../../docs/project/specs/done/plan-2026-05-18-kpress-mvp-stability-and-doctor.md) | MVP stability + doctor plan | **Done** (moved to `done/` 2026-06-01); the reader-parity ledger it carried is now historical — see this TODO’s Cleanup item 1 for the single live source |
| [`../../docs/project/specs/active/plan-2026-05-16-kpress-package-and-publisher.md`](../../docs/project/specs/active/plan-2026-05-16-kpress-package-and-publisher.md) | Main package/static publisher plan (active umbrella) | Active; foundation + doctor + sealing-removal + host-neutral TOC shipped; full reader parity (manual visual/PDF acceptance) + the metabrowser single-renderer cutover remain open |
| [`../../docs/project/research/research-2026-05-15-static-document-publishing-packaging.md`](../../docs/project/research/research-2026-05-15-static-document-publishing-packaging.md) | Static publishing and optimizer research | Complete research brief; informs the open optimizer/sealing work |
| [`../../docs/project/research/research-2026-05-05-small-web-app-packaging.md`](../../docs/project/research/research-2026-05-05-small-web-app-packaging.md) | JavaScript/TypeScript/browser-tooling research | Updated for source-first ESM, optional TypeScript emit, and KPress-style static publishing |

## Source-Port References

KPress reader parity work is a source adaptation from Kash/TextPress, not a clean-room
rewrite. This package-local TODO keeps the reference areas neutral so KPress can be
extracted cleanly; internal migration evidence with machine-local paths belongs in
monorepo evidence docs, not package docs.

| Reference area | KPress use |
| --- | --- |
| Prior page shell templates | page shell, social metadata shape, theme/font baseline, Tailwind-removal inventory |
| Prior standalone document templates | standalone document layout and metadata expectations |
| Prior base reader styles | PT Serif/Source Sans reader tokens, base typography, responsive page sizing |
| Prior content styles | prose, semantic content, table, code, media, and annotation styling |
| Prior TOC component styles and scripts | desktop/mobile TOC styling, backdrop behavior, open/close, active-link, and scroll behavior |
| Prior tooltip component styles and scripts | footnote/internal-link tooltip visual and interaction baseline |
| Prior video popover styles and scripts | video popover layout, YouTube link interception, and popover behavior |
| Prior tabbed-page template | tabbed content behavior and Tailwind utility inventory |
| Prior webpage renderer | page-rendering API and template assembly behavior |
| Prior TextPress local workflows | format, render, and document-output workflow expectations |

## Current State

PR #111 plus the current review cleanup implements the first end-to-end KPress package
slice. It is a usable foundation, not the complete document client and not the final
production publisher.

Implemented now:

- `packages/kpress/` package location, import boundary, typed public surfaces, package
  resources, and public contract tests
- dynamic render/runtime path for host-neutral fragments and package static assets
- first host adapter path for KPress-backed document rendering and printable view
  metadata
- initial Markdown/source rendering, `nh3` sanitizer, fragment/page templates, theme
  hooks, package CSS, native ESM JavaScript helpers, and deterministic placeholder PDF
  artifact with an explicit unavailable browser backend
- KPress-owned external link policy for rendered Markdown/HTML: absolute HTTP(S) links
  get `target="_blank"` plus `rel="noopener noreferrer"`, while anchors, relative
  document links, and `mailto:` links keep their original behavior
- publisher config loading, source discovery, route derivation, static page output,
  manifests, site files, package/local asset handling, offline verification, explicit
  independent asset/optimizer/strict/precompression axes (no dev/production mode), and
  explicit opt-in gzip/Brotli precompression
- lower-level external URL sealing primitive when a caller supplies a fetcher
- explicit `none`/`full` optimizer model (`none` is the default and needs no Node;
  `full` runs `html-minifier-next` via npx) wired into `build_site()`
- CLI/workflow smoke paths for `init`, `convert`, `format`, `render`, `paste`, `files`,
  `export`, `build`, and `optimize`
- package-owned quality gate: ruff, basedpyright, codespell, repo package supply-chain
  policy, Biome 2, `tsc --checkJs`, and browserless Vitest/happy-dom DOM tests
- staged-file KPress hooks for Python plus JavaScript/CSS/JSON formatting and browser
  asset validation
- source-adapted first pass for Kash/TextPress reader tokens, typography, semantic
  content styles, TOC CSS/JS behavior, tab/video styling, YouTube link popovers,
  standalone page metadata, and packaged PT Serif/Source Sans reader fonts
- `markdown-it-py` plus `mdit-py-plugins` based Markdown normalization with GFM
  tables/task lists, stable duplicate heading IDs, footnotes/backrefs, fence-safe
  footnote/math parsing, trust-mode sanitizer coverage, Pygments code highlighting,
  shipped light/dark token CSS, plain heading metadata, Kash-style single-H1 TOC
  filtering, broken-anchor diagnostics, parser-based table wrapping/static numeric
  hooks, and explicit math/diagram marker modes
- structured URL sealing and offline verification for HTML element attributes, `srcset`,
  inline style URLs, and CSS `url(...)` references, with canonical/social absolute URLs
  excluded from offline verification
- PR-review cleanup fixes for sanitized-local escaping, adversarial sanitizer bypasses,
  multi-source routes, trailing-slash output routes, single-read export behavior,
  `build_html()` manifest ownership, and pre-paint theme bootstrap
- integrated production asset sealing for approved external/CDN assets in
  `build_site()`: allowlist enforcement, cache reuse, max-byte limits, retry/refetch
  controls, media-type checks, HTML/CSS graph rewrites, remote-URL-free sealed
  manifests, and strict offline verification
- package asset modes for linked, hashed, and package CSS/JS inline output; copied
  package CSS/JS are optimized before hashing when the `full` optimizer is selected
  (independently of asset mode), while package fonts remain copied as static assets
- browserless DOM coverage for theme initialization, TOC disclosure/active-link state,
  footnote/internal-link tooltips, responsive table wrapping plus numeric-cell hooks,
  code-copy success/error/reset, video popover open/close, and tab click/keyboard access
- initial KPress goldens, static output tests, cache/asset/manifest tests, CLI tests,
  PDF tests, optimizer tests, reader-parity structural tests, and Tailwind-migration
  inventory tests

Not implemented yet:

- **Math rendering — code-side migrated to the simplified `off`/lazy-`auto` contract
  with vendored sealed KaTeX 0.16.45 as the only active renderer; MathML is the
  semantic/accessibility output, not a separate public backend.** No reference system
  (TextPress/Kash or the legacy host reader) renders math, so this is net-new work
  rather than source-port parity.
  Manual browser/PDF visual review remains in acceptance beads.
  See `docs/project/reviews/review-2026-05-17-kpress-feature-parity-matrix.md`.
- final TextPress/Kash document-client parity audit and visual acceptance across every
  reader component
- remaining GFM/Markdown edge parity, images/figures/captions/local assets, production
  diagram renderers, rich media, and semantic content fixtures/rendering coverage
- actual-browser parity confirmation for TOC, footnotes, internal-link tooltips, tables,
  code-copy controls, tabs, video popovers, mobile layout, dark mode, and print
- Playwright-assisted manual browser review playbook for real-browser interaction,
  console/network, mobile, dark-mode, print, and visual acceptance checks
- browser-backed PDF generation
- external asset hardening beyond the current integrated slice: integrity/pinned URL
  policy, response-metadata cache invalidation, JS/import-map graph discovery, and
  manual no-network browser review
- truly self-contained single-file output (one HTML, no siblings, opens over `file://`)
  is **deferred** — the artifact-size dynamics make it a poor default.
  For “share a rendered doc by link”, prefer Static build prod deployed to a CDN.
  Concise revisit notes (effort tiers, recommended lever shape) live in
  `kpress-design.md` under “Self-contained single file: deferred”.
  Tracked by `trading-547y`.
- full production publishing maturity: route edge cases, redirect generation, cache
  invalidation proofs, external asset policies, and readable-vs-sealed review goldens

## Capability Matrix

| Capability | State | Notes / next work |
| --- | --- | --- |
| Package skeleton and imports | Done | `kpress`, `kpress.format`, `kpress.runtime`, `kpress.publish`, and `kpress.workflow` exist; dynamic render path avoids importing publisher/optimizer-heavy code. |
| Public contract | Done for current slice | `kpress.contract` lists current Python names, CSS classes, CSS variables, template variables, and manifest schema markers. Update contract, docs, tests, and goldens together for changes. |
| Format runtime | Partial | `render_fragment`, `render_page`, runtime request models, render cache, and package asset lookup exist. Full document component parity remains open. |
| Host integration | Partial | Dynamic KPress-backed document rendering, printable view metadata, and a host-neutral `postMessage` protocol for ready/resize/expand/close exist. Remaining work is full asset-set consumption, browser/PDF QA, static export command/endpoint, and real embedded-host review. |
| Markdown and source rendering | Partial | `markdown-it-py`, `mdit-py-plugins`, `nh3` sanitizer tests, Pygments code highlighting, shipped light/dark token CSS, fence-safe footnote/math behavior, missing/unused footnote diagnostics, math/diagram markers, structural reader-parity tests, and goldens exist. Remaining work is edge-case image/media/semantic parity, real provider rendering, source-profile visual review, and visual acceptance. |
| CSS and document JavaScript | Partial | Kash/TextPress reader tokens, semantic CSS, pre-paint theme bootstrap, TOC behavior, YouTube video popovers, tabs, and core package helpers are source-adapted into native CSS/ESM and pass Biome/`tsc --checkJs` plus browserless DOM tests. TOC code-side parity now covers disclosure, scroll lock/restore, scrollbar compensation, iOS overscroll guards, smooth heading scroll, active-link tracking, and progressive toggle visibility. Video code-side parity now covers no-network placeholders for raw YouTube embeds in rendered/static HTML. Actual-browser visual/interaction confirmation remains open. |
| Tailwind migration | Partial | Tailwind runtime is not in KPress output; active utility inventory and no-runtime tests exist. Visual equivalence and every source-template behavior still need acceptance. |
| Static publisher | Partial | Config, discovery, routes, output tree, manifests, site files, explicit asset/strict/optimizer/precompression axes, integrated external sealing, package CSS/JS inline mode, optimizer wiring, goldens, full-corpus dynamic-vs-sealed equivalence harness, and readable-vs-sealed output-tree goldens exist. Route/metadata/cache/browser-review maturity remains open. |
| Package/local asset handling | Partial | Package assets and PT Serif/Source Sans font files are copied/hashed/manifested; package CSS/JS can be linked, hashed, optimized, or inlined. Document-local refs (`./image.png` etc.) are emitted into the rendered HTML verbatim in v1 — the deploy layer places the file. Document-local asset *copying* returns with the v2 sealing roadmap. |
| External/CDN asset sealing | **Deferred to v2** | Sealing the document-local and external-URL asset graph (fetch + integrity-pin + HTML/CSS/JS URL rewrite + offline-tree verify) is on the v2 roadmap. v1 leaves document-local and external refs in the rendered HTML verbatim; the deploy layer (CDN, S3, static-host platform) owns delivery and caching. Regex-driven Python rewriting over arbitrary HTML/CSS/JS was the wrong abstraction — v2 returns via a real parser or a JS bundler (Vite/Parcel/esbuild/Bun). See `kpress-design.md` § “Asset sealing: deferred for v1” and the v1-removal plan at `docs/project/specs/active/plan-2026-05-21-kpress-remove-sealing-for-v1.md`. |
| Inline asset mode | Partial; full single-file deferred | Package CSS/JS inline mode is implemented and manifested; package fonts remain copied with static-safe URLs. Local/external CSS/JS are still sealed to files rather than inlined. Truly self-contained single-file output is deferred — for “share by link” use cases, point at a CDN-hosted asset bundle and publish via Static build prod. Revisit plan and effort tiers in `kpress-design.md` under “Self-contained single file: deferred”; tracked by `trading-547y`. |
| Optimizer and compression | Done for current contract; preflight open | Two explicit modes only: `none` (default, zero-dep, content unchanged, no Node needed) and `full` (`html-minifier-next@6.2.3` installed via locked `npm ci` cache at `~/.cache/kpress/npm/`; file-locked for parallel builds; hard error if absent; no fallback; no built-in pseudo-minifier). Precompression is explicit, off by default, orthogonal: `gzip` (stdlib) and/or `br` (`kpress[optimize]`). Manifests record `optimizer_backend`, `original_size`, `compression`, `source_path` per file plus build-level metadata. Locked dependency layer is done (`trading-zc7g`); remaining hardening is build-start preflight before output writes (`trading-owjr`). |
| Local workflows | Partial | CLI/API paths exist. TextPress-compatible golden tests for paired outputs, reports, `--show`, `--rerun`, `--refetch`, and missing extras need more coverage. |
| PDF | Partial | Deterministic minimal PDF output remains available for smoke tests. Optional `backend="browser"` now runs a Playwright print pipeline through the `kpress[pdf]` extra, uses the rendered KPress page/print CSS, and is covered by fake-adapter contract tests. Real Chromium installation, fixture PDFs, cache/report metadata, and manual visual/PDF acceptance review remain open. |
| Quality gates | Partial | KPress pytest and `devtools/lint.py --check` cover Python, docs, package policy, Biome 2, `tsc --checkJs`, and browserless DOM tests. Focused host adapter regression (run in the host repo) passes. Real-browser acceptance is a manual Playwright-assisted playbook, not a required CI dependency. |
| Accessibility | Partial | Code-side reduced-motion handling, copy-button live status, and video dialog focus trap/restore are covered by asset-contract and browserless DOM tests. Remaining work is broader keyboard/ARIA/contrast review for theme, TOC, details, tooltips, tabs, print controls, host embedding, and manual browser acceptance. |

## tminify Precedent

The `tminify` approach worked for Kash/TextPress-style single-page reports, but it was
narrower than the KPress production publisher target.

What `tminify` did:

- read one already-rendered HTML file;
- detect a Tailwind Play CDN script such as
  `https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4`;
- compile Tailwind locally with `npx @tailwindcss/cli`, using the input HTML as source
  for class detection;
- extract inline `<style>` blocks, feed them to Tailwind, then replace the Tailwind CDN
  script with one inline `<style>` containing compiled CSS;
- run `html-minifier-terser` over the resulting HTML, including inline CSS and inline
  JavaScript;
- install/cache npm dependencies inside the Python package area so callers did not
  maintain a project-level `package.json`.

What `tminify` did not do:

- fetch arbitrary CDN JavaScript, CSS, fonts, or images;
- rewrite external `<script src>`, `<link href>`, `<img src>`, font URLs, or import-map
  dependencies into sealed local files;
- maintain an external asset cache with retry, content-type, size, allowlist, or
  provenance policies;
- optimize a multi-file static site tree with separate hashed assets.

The KPress production target is broader:

- keep dynamic viewing zero-build and readable;
- let static publishing fetch/seal approved CDN assets into hashed local files;
- optionally inline CSS/JS for single-file artifacts;
- minify rendered HTML plus package/local CSS and JavaScript;
- precompress deployable outputs;
- record all of this in manifests and prove no unexpected network dependencies remain.

The target publishing contract is functional equivalence:

- dynamic mode can use readable package assets and pinned remote CDN assets;
- production publish mode resolves the same declared asset graph into a fully sealed,
  pre-built tree;
- the sealed tree should be performance-optimized, hash-addressed, minified where safe,
  precompressed, and free of unexpected network dependencies;
- the sealed output must preserve the same document behavior as dynamic zero-build mode,
  with differences limited to URL shape, minification, hashing, compression, and
  explicitly documented optional optimizations.

So the right lesson from `tminify` is not that CDN sealing is already solved.
The lesson is that a Python-owned publishing wrapper can make a no-build development
path production-ready for a narrow rendered-HTML artifact.
KPress should reuse that ergonomic shape, but still needs the broader static-site asset
policy and tests.

## Asset Sealing Tool Candidates

There are general-purpose tools that fetch and inline assets, but none is a direct
drop-in for the KPress production publisher contract.
The useful split is:

- **Web archivers** fetch a rendered or static page and produce one self-contained HTML
  artifact. These prove the fetch-and-inline mechanics are real.
- **Bundlers** inline assets they already own in a build graph.
  These prove optimized single-file output and manifest-style build workflows, but they
  usually expect a Node/Vite/Webpack project.
- **Fetch/cache utilities** solve remote caching but do not rewrite HTML by themselves.

Candidate references:

| Tool | What to borrow | Why not adopt as the KPress core as-is |
| --- | --- | --- |
| Monolith | Rust CLI/library that saves a complete web page as one HTML file with CSS, image, and JavaScript assets embedded. Good reference for one-shot single-file artifacts. | Archive-oriented output, limited KPress manifest/policy control, and not designed around package/local/hashed asset modes. |
| Obelisk | Go package/CLI that embeds resources and downloads assets concurrently; it inlines external scripts/styles rather than base64 data URLs for those assets. Good algorithm reference. | Older project and archive-oriented API; KPress still needs Python package integration, manifests, and policy gates. |
| SingleFile CLI | Browser-backed single-file page capture. Useful for manual QA or snapshot experiments when JavaScript-rendered pages matter. | Heavy browser dependency and rendered-page snapshot semantics; not a deterministic source/publish pipeline for KPress core. |
| posthtml-inline-assets | PostHTML plugin that can replace linked styles/scripts/images with inline HTML. Useful Node-side transform reference. | Older and narrower; not enough policy, cache, manifest, or static-site output control. |
| AssetGraph | Asset/relation graph model for websites, including inline assets as first-class graph nodes. Useful conceptual model for dependency discovery and rewrites. | Broad JavaScript graph framework; likely more machinery than KPress needs unless we choose a Node-backed optimizer layer. |
| `@11ty/eleventy-fetch` | Remote asset fetch/cache utility for JSON, HTML, images, video, web fonts, CSS, and other assets. Good reference for cache ergonomics. | It fetches and caches but does not parse/rewrite KPress HTML or emit KPress manifests. |
| `html-bundler-webpack-plugin` | HTML-entry build that can inline JS, CSS, fonts, images, SVG, and other assets. Good reference for optimized single-file output from source assets. | Pulls KPress toward a Webpack project and build graph rather than a Python-owned static publisher. |
| `vite-plugin-singlefile` | Vite plugin that inlines JavaScript and CSS into final `dist/index.html`. Good reference if KPress ever adds an optional Vite/esbuild-style optimized asset mode. | Assumes a Vite build; not useful for zero-build dynamic runtime or arbitrary rendered KPress pages without adding a full JS build lifecycle. |

Preferred KPress direction:

- Keep the core publisher Python-owned.
- Replace regex-only URL rewriting with a structured HTML rewrite pass.
- Add a policy-driven fetch/cache layer for approved external assets.
- Rewrite fetched external assets either to hashed local files or inline content,
  depending on asset mode.
- Record source URL, hash, media type, cache metadata, rewrite mode, and diagnostics in
  KPress manifests.
- Keep archive-style single-file output as an explicit mode, not the default hosted
  static-site output.

## Finish Roadmap

The remaining work is implementation and acceptance work, not open-ended research.
The specs, research docs, package contract, and this TODO now describe the intended
scope. Tool choices can still be refined while implementing, but no known design blocker
prevents starting the finish work.

Execute the finish work in this order:

1. **Guard the package quality gate.** Add KPress-specific staged-file checks for
   JavaScript, CSS, JSON, and docs so local edits use the same Biome, `tsc --checkJs`,
   pytest, ruff, basedpyright, and Markdown hygiene expected by CI. Exit criteria:
   staged KPress asset/doc edits run the right narrow checks and the documented
   `packages/kpress/devtools/lint.py --check` remains the package-wide gate.
   Current status: implemented for staged Python, JavaScript, CSS, JSON, docs spelling,
   npm package policy, and browserless JavaScript DOM tests.
2. **Harden the production asset graph.** The current integrated slice is implemented:
   `build_site()` can fetch/cache allowlisted external assets, rewrite HTML/CSS asset
   graphs, emit sealed manifests without remote URLs, and fail strict production output
   on unexpected remote references.
   Remaining work is integrity/pinned URL policy, response-metadata cache invalidation,
   JS/import-map graph discovery, richer diagnostics, and optional local/external inline
   output.
3. **Harden optimizer and compression integration.** The `full` optimizer now uses a
   locked dependency layer (`trading-zc7g`): `html-minifier-next@6.2.3` is installed via
   `npm ci` into `~/.cache/kpress/npm/`, file-locked for parallel builds, and run from
   the cache’s `node_modules/.bin/`. `none` (default) publishes content unchanged and
   does not need Node. Missing npm/npx raises a clear missing-extra error with no silent
   fallback. Remaining hardening is build-start preflight before output writes
   (`trading-owjr`). Precompression is explicit, off by default, and orthogonal.
   Manifests record per-file and build-level optimizer/compression metadata.
4. **Extend dynamic-vs-sealed equivalence.** Full-corpus browserless equivalence harness
   and readable-vs-sealed output-tree goldens now cover the document fixture corpus.
   Remaining work is manual browser review observations for console/network state,
   component interactions, computed styles, mobile, dark mode, and print profile.
5. **Complete static publisher maturity.** Harden route resolution, redirects,
   sitemap/robots/canonical metadata, shared frontmatter-format provenance, and cache
   invalidation across source, render, package-asset, external-response, optimizer, and
   PDF inputs. Exit criteria: static site output has deterministic routes, complete
   metadata, clear duplicate/reserved-path diagnostics, and cache invalidation proofs.
6. **Port the full document runtime.** Source-port the TextPress/Kash document template,
   CSS, and browser behavior into KPress-owned assets: Markdown/GFM parity, typography,
   themes, fonts, TOC, tooltips, footnotes, tables, code-copy, tabs, rich media, math,
   diagrams, mobile, dark mode, and print.
   Exit criteria: KPress owns the reader behavior and no longer depends on Tailwind
   runtime or source-project implementation details.
7. **Build the acceptance playbook.** Add fixture corpus, normalized DOM checks,
   HTML/CSS validity, duplicate/broken-link checks, sanitizer checks, selector coverage,
   and a manual Playwright-assisted browser checklist for interaction, mobile, dark
   mode, print, console/network, and visual review.
   Exit criteria: automated checks cover deterministic structure and package quality;
   real-browser acceptance is recorded as human-reviewed playbook evidence.
8. **Finalize host readiness.** Document and test the host integration contract, static
   export seam, print profile mapping, theme mapping, accessibility expectations, mobile
   behavior, and manual review checklist.
   Exit criteria: the embedding host remains a thin adapter and KPress can publish the
   same document surface dynamically, statically, and as PDF.

## Prioritized Open Work

### P0: Status and Contract Hygiene

- [x] Keep `packages/kpress/TODO.md` as the plain implementation-status ledger.
- [x] Synchronize `packages/kpress/TODO.md`, `kpress-design.md`, the active plan specs,
  and JavaScript tooling research for the 2026-05-17 package-policy and browserless DOM
  test update.
- [x] Re-check `packages/kpress/TODO.md`, `kpress-design.md`, the active plan specs, and
  relevant research docs whenever KPress implementation status changes.
- [x] Add KPress-specific staged-file lefthook entries for JS/CSS/JSON so the local
  workflow matches the documented quality gate.
- [x] Close the PR #111 review defects in code and tests: `nh3` sanitizer replacement,
  sanitized-local HTML preservation, fence-safe footnote/math parsing, structured asset
  sealing/offline checks, pre-paint theme bootstrap, richer browserless interaction
  coverage, strict `basedpyright`, multi-source/static-output fixes, optional-extra
  declarations, and explicit browser-PDF missing implementation.

### P1: Production Publishing Clarity

- [x] Implement the first integrated external/CDN asset policy for `build_site()`:
  allowlist enforcement, cache keys, retries/refetch, media-type checks, size limits,
  failure diagnostics, CSS graph rewriting, and manifest provenance/redaction.
- [x] Wire external/CDN fetching into `build_site()` only for configured static
  publishing modes; dynamic host rendering must not fetch or inline remote assets as a
  side effect.
- [x] Implement package CSS/JS `inline` asset mode, including manifest entries and tests
  proving linked, hashed, and inline package modes.
- [x] Minify package/local/external CSS and JavaScript files in the integrated
  production static build path with the `full` optimizer (`html-minifier-next`).
- [x] Harden sealed external assets with pinned URL/integrity policy, response-metadata
  cache invalidation, JS/import-map graph discovery, broader diagnostics, and non-HTML
  asset rewrite fixtures.
- Truly self-contained single-file output (one HTML, no siblings, opens over `file://`)
  is **deferred**. Artifact-size dynamics — reader fonts alone add ~250 KB after base64;
  KaTeX adds ~700 KB; document images push into MB quickly — make inline a poor default
  for most documents. For “share a rendered doc by link”, prefer Static build prod
  deployed to a CDN-hosted asset bundle.
  Revisit plan with effort tiers is in `kpress-design.md` under “Self-contained single
  file: deferred”; classic-JS reader lever tracked by `trading-547y`.
- [ ] Add a no-network production review step to the manual Playwright playbook.
- [x] Add a browserless dynamic-vs-sealed equivalence smoke test for the document
  surface.
- [x] Extend dynamic-vs-sealed equivalence tests across the full reader fixture corpus
  and record browser console/network, interaction, and print observations through the
  manual playbook.
- [x] Add readable-vs-sealed output-tree goldens that show readable output versus the
  content-hashed sealed output profile, with explicit (opt-in) precompression sidecars.
  Minification is the separate, Node-gated `full` optimizer, not a default.
- [x] Optimizer is explicit `none`/`full`: `none` (default, no Node) publishes content
  unchanged; `full` installs `html-minifier-next@6.2.3` into a locked
  `~/.cache/kpress/npm/` cache via `npm ci`, file-locked for parallel builds, and
  hard-errors when unavailable.
  No built-in pseudo-minifier and no silent fallback.
  Manifests record `optimizer_backend`, `original_size`, `compression`, and
  `source_path` per file, plus build-level `optimizer_backend` and `precompress` fields.
- [x] Finish Brotli optional-extra packaging and tests for the current precompression
  path.

### P1: Static Publisher Maturity

- [x] Harden route resolution: index routes, trailing-slash rules, case normalization,
  reserved paths (`_kpress/`, `sitemap.xml`, `robots.txt`, `_redirects`), and
  duplicate-route diagnostics through `publish/routes.py::plan_site_routes`.
  Frontmatter-driven `public_path`/`public_slug`/page IDs remain, pending the shared
  `frontmatter-format` parser decision.
- [ ] Add publisher fixtures proving the shared `frontmatter-format` precedence and
  provenance contract survives discovery, routing, rendering, and manifests; this also
  unblocks frontmatter-driven `public_path`/`public_slug` route overrides.
- [x] Complete sitemap, robots, canonical/base URL, `lastmod` (deterministic
  `site.build_date`), redirect (`_redirects`) output, and XML escaping in
  `publish/site_files.py`.
- [x] Add cache invalidation proofs: `tests/test_publish_cache_invalidation.py` proves
  content-addressed output is a deterministic function of inputs (identical inputs
  reproduce identical hashes; source, optimize, and asset-mode changes invalidate
  output). External response-metadata / `--refetch` invalidation is covered by
  `tests/test_seal_hardening.py`. PDF-profile cache invalidation remains with the PDF
  fixture work (`trading-zwc2`/`trading-14v1`).

### P2: Document Runtime Parity

Detailed reader parity is now tracked by `trading-xgzj` and its child beads.
The older broad parity beads remain open as grouping beads and are blocked by the
feature-level beads below.
The feature parity matrix in
`docs/project/reviews/review-2026-05-17-kpress-feature-parity-matrix.md` is now the
controlling checklist for reader parity.
Every matrix gap is mapped to a matrix-specific bead below, and the final parity audit
bead `trading-08y5` depends on all of them.

| Reader feature | Bead | Coarse owner |
| --- | --- | --- |
| GFM Markdown block/inline document tree | `trading-97c1` | `trading-8is3` |
| Raw HTML trust and sanitizer matrix | `trading-1rc7` | `trading-8is3` |
| Images, figures, captions, and local media assets | `trading-oxs3` | `trading-8is3`, `trading-5dmd` |
| Code fences, source profiles, and syntax highlighting | `trading-c5xy` | `trading-8is3`, `trading-d6g2` |
| Math `off`/lazy-`auto` KaTeX design | `trading-g0ra` | `trading-8is3`, `trading-5dmd` |
| Diagram rendering providers | `trading-lir6` | `trading-8is3`, `trading-5dmd` |
| Typography, document CSS, and themes | `trading-vdbu` | `trading-131h` |
| Print CSS and print profiles | `trading-boxw` | `trading-131h`, `trading-n7ok` |
| Desktop TOC behavior | `trading-i4rj` | `trading-d6g2` |
| Mobile TOC drawer behavior | `trading-o59o` | `trading-d6g2` |
| Footnote hover and touch tooltips | `trading-1u4r` | `trading-d6g2`, `trading-0xa1` |
| Internal-link preview tooltips | `trading-2z84` | `trading-d6g2`, `trading-0xa1` |
| Responsive tables and numeric-cell hooks | `trading-09i3` | `trading-8is3`, `trading-d6g2` |
| Code-copy controls | `trading-vy98` | `trading-d6g2` |
| Video popovers and embedded media policy | `trading-m83y` | `trading-d6g2`, `trading-selz` |
| Tabbed content components | `trading-wv4m` | `trading-d6g2`, `trading-selz`, `trading-0xa1` |
| Semantic content components | `trading-3l2o` | `trading-selz` |
| Fonts and packaged reader assets | `trading-mzp0` | `trading-5dmd` |
| Canonical fixture corpus and accepted goldens | `trading-4mdl` | `trading-q72a` |
| Manual browser acceptance playbook | `trading-azna` | `trading-q72a` |
| Browser-backed PDF generation and fixtures | `trading-zwc2` | `trading-n7ok`, `trading-q72a` |
| Accessibility and host-readiness checks | `trading-t2rf` | `trading-0xa1` |
| Final reader parity audit and closure gate | `trading-08y5` | `trading-xgzj` |

The matrix-specific bead list lives in tbd and in the parity-matrix review.
Do not copy the full status table back into this TODO; keep this section to routing,
acceptance rules, and current top-level blockers.

- [ ] Port TextPress/Kash page templates and component partials into KPress templates.
- [ ] Complete GFM Markdown parity: tables, footnotes, task lists, nested lists,
  blockquotes, autolinks, images, strikethrough, hard/soft breaks, duplicate heading
  IDs, trusted raw HTML, and sanitizer modes.
  Footnote refs/backrefs, print simplification, and missing/unused diagnostics are
  code-side covered.
- [ ] Port typography, color tokens, light/dark/system themes, mobile behavior, print
  CSS, TOC styles, tooltip styles, YouTube/video popover styles, tabbed content, source
  view styling, and semantic content styles.
- [ ] Port TOC behavior: heading thresholds, generated IDs, desktop sticky rail, mobile
  drawer, active heading, scroll behavior, and print suppression.
- [ ] Port footnote/internal-link tooltip behavior: hover/touch behavior, truncation,
  expansion, positioning, Escape close, and previews for headings, figures, tables, code
  blocks, details, and nearby paragraphs.
  Code-side tooltip timing, positioning hooks, footnote diagnostics, and print
  simplification are covered; manual browser acceptance remains.
- [ ] Port table behavior, numeric-cell hooks, code-copy controls, image URL rewriting,
  sidematter/frontmatter components, details styling, thumbnails, and rich media.
- [ ] Add remaining diagram provider hooks for SVG/image passthrough and Mermaid, and
  migrate math to the simplified `off`/lazy-`auto` KaTeX design.
- [ ] Add sealed font fixtures for PT Serif, Source Sans 3, mono, punctuation fallback,
  dynamic CDN mode, static readable mode, and static sealed offline mode.

### P2: Acceptance Playbook

- [ ] Build the accepted KPress fixture corpus for prose, source, tables, frontmatter,
  TOC, footnotes, tooltips, math, diagrams, images, fonts, dark mode, mobile, print, and
  semantic content components.
- [ ] Add normalized DOM diffs, HTML validity checks, duplicate-ID checks, broken-anchor
  checks, sanitizer checks, CSS selector coverage, CSS validity, and required-variable
  checks.
- [ ] Add a manual Playwright-assisted browser checklist for theme, TOC, tooltips,
  tables, code copy, tabs, video popovers, details, mobile layout, and print-media
  review.
- [ ] Record manual observations for typography, line heights, colors, widths, table
  overflow, sticky/fixed behavior, hidden/display state, and print profile.
- [ ] Capture optional review screenshots for desktop, mobile, dark mode, and print
  media as evidence, not as required automated regression baselines.
- [ ] Add real-browser PDF fixtures for page breaks, wide tables, source files,
  footnotes, images, diagrams, math, custom fonts, and print-only controls.

### P3: Host Readiness

- [ ] Document the final host integration contract: request fields, `postMessage`
  handling, fallback behavior, asset serving, print profile mapping, theme mapping, and
  static export seam.
- [ ] Add accessibility checks for theme controls, TOC controls, details, tooltip
  triggers, tabs, popovers, document navigation, and print controls.
- [ ] Add manual review notes for desktop, mobile, dark mode, print preview, PDF, and
  no-network static output before declaring KPress document runtime parity.

## Validation Commands

Run these from the repository root:

```bash
uv run --project packages/kpress pytest packages/kpress/tests --tb=short -q
uv run --project packages/kpress python packages/kpress/devtools/lint.py --check
git diff --check
```

Current validated state (2026-06-05 consolidation pass):

- `uv run --project packages/kpress pytest packages/kpress/tests --tb=short -q`: 356
  passed, 1 skipped.
- `uv run --project metabrowser pytest metabrowser/tests --tb=short -q`: 661 passed.
- host adapter regression (the MetaBrowser KPress render route + version tests):
  passing.
- `git diff --check`: passed.

<!-- This document follows std-doc-guidelines.md.
Review guidelines before editing.
-->
