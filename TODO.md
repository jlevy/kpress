# KPress Backlog and Status

This is KPress’s public implementation ledger.
It answers two separate questions:

1. **Capability status:** What works today, and how is it verified?
2. **Backlog status:** What remains, in what order, and which tbd bead owns it?

The code and contract tests are authoritative for shipped behavior.
tbd is authoritative for issue status and dependencies.
This file is the maintained view across both.
Update all three together when a public capability changes.

Last reconciled: 2026-07-18.

## Release Status

KPress `0.2.2` is published on PyPI as the current public alpha.
It preserves the complete typed host asset and fragment contract from `0.2.0`, fixes
tooltip asset selection for same-document links, lets hosts export already-decoded
source text without losing logical-path asset resolution, and retains the raised release
tooling floor. KPress `0.1.0` remains the first public alpha.
All P1 release and stabilization gates are closed.
Alpha status is conveyed by package metadata and release notes, not by a version suffix.

Completed release gates:

| Gate | Bead | Result |
| --- | --- | --- |
| Host asset contract and external install | `kpr-f8oz` | Closed; PR #16 shipped the typed asset manifest, public materializer, explicit asset policies, and pinned fragment hooks. GitHub release `v0.2.0` published through PyPI Trusted Publishing, and the exact registry package passed clean CLI and capability smokes. |
| Trusted publication and external install | `kpr-1kfq` | Closed; GitHub release `v0.1.0` published through PyPI Trusted Publishing, and the registry package passed the documented CLI, clean-project, and bundled-example smokes. |
| Public planning and docs hygiene | `kpr-nyc1` | Closed; the public ledger, docs, source, tests, and fixtures are checked for private paths, project names, and tracker IDs. |
| Platform claim | `kpr-wx2a` | Closed; metadata and docs state the verified macOS/Linux POSIX boundary, while native Windows remains tracked. |
| CLI and export truth | `kpr-q9bg` | Closed; fictional conversion/export surfaces are removed, and PDF uses Playwright/Chromium or fails clearly. |
| Deterministic full optimizer | `kpr-4cds` | Closed; a reviewed lock ships, cold-cache bootstrap uses `npm ci`, doctor’s network flag is real, and preflight precedes output mutation. |
| Vendored-asset licensing | `kpr-6xq2` | Closed; complete Lucide/Feather, KaTeX, PT Serif, and Source Sans 3 texts ship in the wheel. |

Completed maintenance gates:

| Gate | Bead | Result |
| --- | --- | --- |
| Dependency vulnerability monitoring | `kpr-nev3` | GitHub dependency alerts and automated security fixes are enabled; the release gate audits the frozen Python and npm dependency graphs. |
| Node runner readiness | `kpr-gkj6` | CI uses the full-SHA-pinned Node setup action with the current Node 24.18 and npm 11 tooling floor; `.nvmrc` and `.node-version` keep nvm and fnm on that same runtime. |
| Host-decoded document export | `kpr-csoa` | `KPressExportRequest.source_text` lets embedding hosts export decoded content while `path` remains the logical identity and relative-asset base. |

## Capability Matrix

“Automated” means a current test or quality gate exercises the capability.
“Browser and print” records real-browser evidence separately; browserless DOM tests do
not count as visual acceptance.

| Area | Implementation | Automated evidence | Browser and print evidence | Remaining beads |
| --- | --- | --- | --- | --- |
| Markdown and document model | Implemented for GFM tables/tasks, nested structures, footnotes, code, math markers, raw-HTML postures, stable headings, frontmatter, and sidematter | Parser, sanitizer, document-contract, reader-parity, and golden suites | Representative long-form pages have been exercised; the full provider/edge corpus is not visually accepted | `kpr-1zxy`, `kpr-qmii` |
| HTML safety and custom tags | Exact extra-tag and inert-attribute admission is implemented; dangerous tags, event handlers, inline style, and unsafe URLs fail closed or are stripped with itemized diagnostics | Config, sanitizer, public-contract, and dynamic/static parity tests | No separate visual gate is required for the safety floor | `kpr-ej80` for optional declared prefix patterns |
| Page shell and design system | Standalone page, themes, palettes, reading fonts, TOC, content card, semantic styles, and public CSS-variable/class contracts are implemented | Golden, CSS-contract, font, content-card, and publish-workflow tests | Light/dark, desktop/narrow, settings, structural content, and tooltip smoke have evidence; the complete matrix remains open | `kpr-qmii`, `kpr-vxy5` |
| Client runtime | Widget and behavior registries, configuration, mount/remount, teardown, fault isolation, settings, TOC, tooltips, history-aware hash navigation (native TOC hash entries plus viewport scroll restoration on Back/Forward, `kpr-als7`), tables, code copy, tabs, video popovers, overlay, and viewport helpers are implemented | Browserless Vitest suites plus focused Python contract tests and a real Playwright tooltip smoke | Full keyboard, touch, reduced-motion, popover, and print interaction acceptance remains open | `kpr-qmii`, `kpr-vxy5`, `kpr-jqx2` |
| Extension surfaces | Typed Python config, ordered build pipeline stages, tree/page transforms, chrome slots, widget configuration, public JS exports, CSS variables, and generic integration guidance are implemented and pinned | Public-contract, pipeline, runtime, examples, and clean-room wheel tests | Representative host integration works; opaque page data and a simpler CSS-var layer are not shipped | `kpr-4qxl`, `kpr-ef65`, `kpr-hh97` |
| Static publishing | Multi-source discovery, deterministic routes, static assets, linked/hashed modes, manifests, sitemap/robots/redirects, precompression, cache invalidation, and fail-loud diagnostics are implemented | Publish, route, manifest, cache, equivalence, golden, and clean-room example suites | External clean-room builds pass; deployed cache-busting policy and a KPress-owned collection/navigation layer remain | `kpr-5ar3`, `kpr-w993` |
| Optimizer | `none` and optional `full` stages work; a reviewed npm lock ships, cold-cache bootstrap uses `npm ci`, and preflight runs before output mutation | Optimizer, pipeline, manifest, doctor network-semantics, cold/offline/error, and preflight tests | Warm and cold cache paths are verified on the supported platforms | — |
| CLI and local workflows | `init`, `convert`, `format`, `render`, `paste`, `files`, `export`, `clean`, `build`, `optimize`, and `doctor` have tested supported paths; unsupported source conversion is explicit | CLI, workflow, clean-room, and wheel smoke tests | HTML paths are verified; PDF delegates to the real browser-print pipeline | `kpr-qmii` for full visual acceptance |
| Print and PDF | Print CSS and a Playwright/Chromium browser-PDF backend exist; no placeholder PDF path is exposed | Print-contract, missing-dependency, and browser-backend unit tests | Full print-preview/PDF artifact acceptance remains open | `kpr-qmii` |
| Packaging and documentation | Typed wheel/sdist, complete bundled-asset licenses, three examples, external quickstart, security policy, release notes, public backlog, and trusted-publish workflow exist | Lint/public-hygiene over source and tests, Common Doc footer checks, locked-graph vulnerability audits, build inspection, clean-room wheel, README flow, CLI, library, and example smokes | PyPI Trusted Publishing and external `kpress==0.2.2` version, help, doctor, and minimal static-site build are verified | — |
| Platforms and maintenance | Python 3.12–3.14 on Linux/macOS is the declared and verified implementation boundary; dependency alerts, automated security fixes, and current Node runner support are enabled | CI covers supported Python versions on Ubuntu; local macOS gates pass | Native Windows support is not verified or claimed | `kpr-isp2` |

## Prioritized Backlog

### Active Feature Plan

- `kpr-4q0a`: implement
  [interactive footnote popovers](docs/interactive-footnote-popovers.plan.md) with
  distinct transient and pinned states, native anchor fallback, complete ESM closure,
  and real-browser evidence; phase epics are `kpr-pw7v`, `kpr-ipqy`, and `kpr-x23v`
- `kpr-vuaw`: implement the [collapsible TOC](docs/toc-collapse.plan.md) — entries below
  a configurable depth start collapsed, an expand/collapse-all toggle sits beside the
  Contents header, and the active section auto-expands via the scroll-spy

### P1: Release Gates

No P1 release gates remain open.

### P2: Stabilization After the First Alpha

- `kpr-qmii`: complete the real-browser and print acceptance matrix
- `kpr-1zxy`: expand representative document and provider fixtures
- `kpr-vxy5`: audit accessibility and keyboard behavior
- `kpr-jqx2`: expose host-neutral ready and lifecycle events
- `kpr-4qxl`: add an opaque per-page extension-data seam
- `kpr-5ar3`: add a supported cache-busted asset URL policy
- `kpr-w993`: design the multi-page collection and navigation layer
- `kpr-hh97`: migrate remaining render markup into live strict templates

### P3: Deferred Evolution

- `kpr-lrfg`: add optional
  [content-size indicators](docs/content-size-indicators.plan.md) (document and
  top-section word counts plus reading time) behind a flexdoc `metrics` extra
- `kpr-isp2`: restore and verify native Windows support
- `kpr-xsog`: design verified offline assets and truly self-contained output
- `kpr-ef65`: evaluate schema-checked simple CSS-variable configuration
- `kpr-ej80`: add declared plugin-prefix admission without weakening sanitization
- `kpr-e48f`: support optional icon sprite overrides without weakening the built-in icon
  contract
- `kpr-gjm8`: design one uniform per-document frontmatter override policy for format
  settings, instead of one-off keys added feature by feature
- `kpr-6nvi`: rename the `video-popover.js` asset to match its current inline-embed
  behavior

## Maintenance Rules

- Every active backlog line must name one real open or in-progress `kpr-*` bead.
- Closed beads leave the active lists; shipped capability remains in the matrix.
- A capability is “implemented” only when code, public contract, docs, and automated
  tests agree.
- Browserless DOM tests establish behavior, not visual acceptance.
  Record actual desktop, narrow, dark, print, console, and network evidence under the
  browser bead.
- New deferrals require a bead before the code or docs call them deferred.
- Keep private repository names, machine paths, and non-public tracker IDs out of this
  repository. Historical detail belongs in Git, not this current-status ledger.

Useful public orientation: [README](README.md), [documentation index](docs/README.md),
[design and public contracts](docs/kpress-design.md),
[validation runbook](docs/kpress-validation.runbook.md), and
[current release notes](docs/releases/0.2.2.md).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
