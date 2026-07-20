# KPress Operations and Host Integration

This reference covers local runtime operations, browser-asset quality gates, acceptance
evidence, accessibility, and the dynamic embedding boundary.
The core architecture, format, CSS, and static-publishing contracts remain in
[KPress Design](kpress-design.md).

## Local Document Workflows

KPress provides local document workflows without hosted-service coupling.

Commands:

```bash
kpress init
kpress convert INPUT --output OUTPUT.md
kpress format INPUT --output-dir DIR
kpress render INPUT.md --output OUTPUT.html
kpress paste --title TITLE --text TEXT
kpress files
kpress export INPUT.md --html OUT.html
kpress clean --config kpress.yml
kpress build --config kpress.yml
kpress build --config kpress.yml --asset-mode hashed --optimizer full --precompress gzip
kpress doctor --config kpress.yml
kpress optimize INPUT --output OUTPUT --backend full
```

Relevant flags:

- the global `--work-root` option appears before the subcommand
- `format`, `render`, and `build` accept `--asset-mode` where they shape package assets
- `export --pdf` adds an optional browser-backed PDF when `kpress[pdf]` and Chromium are
  installed

The workflow layer owns workspace paths, cache semantics, output names, local reports,
paired Markdown/HTML output, and emission of package assets and eligible local media
without rewriting authored media URLs.
Hosted login, upload, accounts, and public service URLs stay outside KPress core.

## Doctor

`kpress doctor` is a runtime-capability readiness probe, not a development quality gate
(it never runs Biome, `tsc --checkJs`, Vitest, Ruff, basedpyright, supply-chain checks,
or formatting; those stay in the repository tooling).
It answers whether the installed package can render, publish, optimize, precompress, or
export PDF on this machine with the dependencies currently present.

`kpress.publish.probe_capability`/`probe_all` and the dataclass `ProbeResult` (status
one of `ok`/`unavailable`/`skipped`/`fail`, optional snake_case `reason`) are the single
source of truth, shared with the `optimizer=full` preflight in
`build_site()`/`build_html()`.

- Default `kpress doctor`: lightweight, no network, discovery only; never fails the
  process.
- `--profile {render,publish,optimize,pdf}`: probe one capability; a requested profile
  that is not `ok` exits non-zero.
- `--config kpress.yml`: config-aware aggregate.
  There is no `dev`/`production` mode; doctor reads the resolved explicit axes and fails
  only when a capability the config actually requires (optimizer `full`, `br`
  precompression, or PDF enabled) is unavailable.
- `--allow-network`: the only gate that bootstraps a cold optimizer cache with the
  shipped lock. It is accepted by `doctor`; build and direct optimizer paths remain
  network-free. Warm-cache and Node/npm presence checks are always no-network.
- `--json`: stable `{kpress_version, platform, python_version, capabilities}` with the
  closed status set.

Capability semantics mirror the runtime contract: `optimizer=none` without Node is OK;
`optimizer=full` without the toolchain, `br` without `brotli`, or PDF without Playwright
are failures only when that path is requested, otherwise reported as unavailable or
skipped.

## Browser Asset Quality Gate

KPress browser JavaScript and CSS are first-class package source.

Required tooling:

- repository supply-chain checks for exact npm pins, lock integrity, release cool-offs,
  and safe publishing workflows
- Biome 2 for JS/CSS/JSON formatting and linting, run from the locked package toolchain
- `tsc --checkJs` for native JavaScript type checking with JSDoc
- Vitest with `happy-dom` for browserless DOM behavior tests
- Ruff and basedpyright for Python
- codespell for docs/source
- CI job `lint`
- lefthook staged-file formatting and validation for KPress Python, JS, CSS, and JSON

Runtime JavaScript is native ESM and requires no build step for dynamic hosts.
Any proposal to introduce TypeScript source must first define a stale-build check and a
generated-output policy.

## Document Acceptance and Regression Harness

Accepted KPress output is the regression contract.
Each scenario compares current output with a reviewed KPress baseline.

Required layers:

- representative source scenarios under `tests/golden/scenarios/`
- accepted KPress golden artifacts under `tests/golden/accepted/`
- normalized DOM structural diffs
- HTML validity checks: duplicate IDs, broken anchors, ARIA references, landmarks,
  sanitizer expectations
- CSS selector coverage and validity checks
- JavaScript checks: Biome, `tsc --checkJs`, browserless Vitest/`happy-dom` behavior
  tests
- manual Playwright-assisted checks for browser-load errors, unhandled promises, missing
  modules, unexpected globals, interactions, console/network state, mobile, dark mode,
  print media, screenshots as review evidence, and PDF probes

The [validation runbook](kpress-validation.runbook.md) defines the automated, agent, and
human acceptance evidence required for document components, browser behavior, and print
output.

## Accessibility

Current KPress output provides:

- document landmarks while preserving the author’s heading order
- accessible settings and TOC controls
- keyboard-operable details, tabs, and popovers
- live-region feedback for transient copy status
- reduced-motion behavior for animated reader controls
- tooltip triggers that degrade cleanly on touch/mobile
- print output that excludes screen-only controls

The reader-feature accessibility contract adds: heading landmarks and skip-friendly
structure, `aria` state on tabs, TOC, and copy controls, focus-visible interactive
elements, and semantic tooltip markup (`<aside role="tooltip">`).

Browserless tests cover deterministic interaction and ARIA state.
The validation runbook covers manual keyboard, light/dark contrast, responsive, and
print review. The broader accessibility audit remains tracked as `kpr-vxy5`.

## Host Integration

The embedding host should call KPress through the dynamic runtime and serve KPress
assets. It should not copy component CSS or JavaScript into host-specific selectors.

Host responsibilities:

- read files and frontmatter
- choose active view and printability
- map host view names to KPress profiles
- serve KPress package assets
- hide host chrome during print
- handle dependency or import failure if the host deliberately makes KPress optional
- keep navigation and shell controls outside KPress fragments

KPress responsibilities:

- render document fragments/pages
- own document CSS and JS
- own document print profile
- declare required assets
- provide diagnostics
- generate static outputs and PDFs when called through publisher APIs

An embedding host app keeps KPress’s vendored PT Serif / Source Sans reader faces by
default, so an embed keeps the KPress reading look rather than the host’s UI fonts.
A host overrides a font per role through the `--kpress-host-font-*` hooks (see the
font-role table under [Theme and Fonts](kpress-design.md#theme-and-fonts)); a host app
can use this for a serif/sans reading-font toggle, which sets
`--kpress-host-font-prose`. Hosts customize colors by setting the public
`--kpress-doc-*` tokens on the document scope.

### Collapsible TOC

For long documents, a host can pre-collapse deep TOC entries so the TOC fits its pane
(full contract: [Collapsible TOC](kpress-design.md#collapsible-toc)):

- **Static publish:** `format.toc_collapse_depth: 1` in `kpress.yml` (and optionally
  `format.toc_expand_on_scroll: false` to disable scroll-follow).
- **Python render:** `RenderOptions(toc_collapse_depth=1)`.
- **Dynamic path:** `KPressRenderRequest(toc_collapse_depth=1)`; an invalid depth fails
  the request with `KPressInvalidRequestError`.

The depth is the **normalized TOC depth**, not the heading tag: in the common
one-H1-title document, `1` keeps the H2 spine, `2` keeps H2-H3. Off (the default)
renders byte-identical markup, so enabling it is a pure opt-in with no goldens drift for
other documents. The client behavior reads the stamped data attributes; a host can
override per page via
`kpress.behaviors.configure("toc", { collapseDepth: 2, expandOnScroll: false })` before
apply (a `collapseDepth` of `0` turns collapse off), and the expand-all control is
server-rendered chrome — no host-injected markup.

### Client Runtime (`window.kpress`)

The client runtime (`static/js/runtime.js`, loaded first in the default JS assets) is
the host-facing JS surface, the same one KPress’s own built-ins use (dogfood rule).
It assembles the `kpress` global from per-module namespaces:

- `kpress.model()`: the parsed `#kpress-page-model` page model (empty in fragments;
  embedding hosts get the same data in the `render_view` payload).
- `kpress.on` / `kpress.off` / `kpress.emit`: events (`kpress:ready` after the runtime
  applies registrations; `widget:change` from widgets).
- `kpress.storage`: `{get, set, use(adapter)}`; localStorage default.
  An embedding host swaps persistence with one call (e.g. a cookie adapter for
  cross-port sharing) and every primitive and widget follows.
- `kpress.theme`: the theme engine (see
  [Theme and Fonts](kpress-design.md#theme-and-fonts)).
- `kpress.menu`: the popover-behavior primitive.
- `kpress.widgets`:
  `{register(id, {mount}), configure(id, config), mount(id, el, config?)}`; mounting is
  explicit in embeds (host picks the element), automatic in the standalone page
  (server-emitted mounts).
- `kpress.behaviors`:
  `{register(id, {bind}), override(id, binding), configure(id, config), rebind(id)}`
  over the server-rendered markup.
  A `bind(root)` may return a **disposer**; the runtime calls it before re-binding on
  `override`/`rebind`, so replacement is real: the old binding’s observers and listeners
  are gone, not shadowed.

Lifecycle: modules register at import (no DOM work, no storage I/O); the runtime applies
all registrations on `DOMContentLoaded` and emits `kpress:ready`. Application is
fault-isolated: a throwing mount, bind, or event listener is logged (`console.error`)
and skipped; it never blocks other registrations or `kpress:ready`. Host scripts
injected via `head_extra_html` run before apply, so a host
`register`/`override`/`configure` (and `storage.use`) replaces a built-in cleanly; later
scripts use `rebind`/`mount`. The exported ES-module parts of built-ins (TOC visibility
policy, tooltip placement, …) are importable through the same import map the assets
already publish, and the stability-pinned subset is `contract.py::PUBLIC_JS_EXPORTS`.

Asset shipping is deliberately simple: the default JS/CSS set is a **fixed reader
bundle**: `widgets: {settings: off}` removes the mount (so nothing renders or runs), not
the asset; there is no per-widget asset selection.
A host widget’s own JS and CSS ship through host channels: a `head_extra_html`
`<script type="module">`/`<link>` plus `sources[].static` passthrough for the files.
That is the supported delivery contract (the static-site example’s `demo/extensions.js`
is the reference).

An embedding host can mount the same settings widget used by a standalone page:
`kpress.widgets.mount("settings", el, {choosers: [...]})` plus
`kpress.storage.use(cookieAdapter)`, and keeps only its font-stack choices via the
`--kpress-host-font-*` vars.
Theme init itself is the registered `theme` behavior (it reads persisted state through
the current storage adapter at apply time and binds the OS listener): an embedding host
that owns theme resolution disables it before apply:
`kpress.behaviors.override("theme", () => {})`, and the engine API (`kpress.theme.set`,
…) stays callable.

In-document hash navigation is covered by the registered `history` behavior: because the
document scrolls in the `[data-kpress-viewport]` pane (which browsers exclude from
native Back/Forward scroll restoration), it stamps the pane offset into session-history
entry state and restores it on `popstate`, falling back to the fragment target (document
top for a fragmentless entry).
The stamp is written only when the entry’s state is `null` or a plain record without a
conflicting non-numeric `kpressScroll` key; any other host state shape (a `Date`, `Map`,
array, class instance, or a host-owned `kpressScroll`) is left exactly as the host
stored it, and traversal for those entries uses the fragment fallback.
A host that swaps documents per view must call the bind’s disposer on unmount (as with
every behavior), and an SPA host that owns history/router state overrides the id before
apply: `kpress.behaviors.override("history", () => {})`.

### Dynamic Render Contract

The host calls `kpress.runtime.render_view(KPressRenderRequest)` and receives a
JSON-ready dict. Fields and semantics:

| `KPressRenderRequest` field | Required | Meaning |
| --- | --- | --- |
| `source_text` | yes | Document text the host has already decoded |
| `source_path` | yes | Relative path inside the host’s worktree; used for diagnostics, metadata, and the source-profile header |
| `kind` | yes | Host-side file kind (`markdown`, `text`, `structured`, etc.); carried in render metadata |
| `view` | yes | Host-side view name (`rendered`, `source`, `tree`, …); normalized via `normalize_print_profile` into a KPress profile |
| `ext` | yes | Lowercase file extension including the dot; carried in render metadata |
| `mtime_hash` | yes | Host-supplied content fingerprint; part of the in-process render-cache key |
| `size` | yes | Byte size of the source; reported when a source-profile preview is truncated |
| `frontmatter` | no | Parsed YAML metadata the host already extracted; KPress treats this as authoritative |
| `frontmatter_error` | no | Host-side YAML parse error string; surfaced as a visible reader banner |
| `profile` | no | Optional explicit KPress profile override; bypasses the view-name mapping |
| `theme_mode` | no | `"system"` (default), `"light"`, or `"dark"`: the user’s theme preference |
| `resolved_theme` | no | `"light"` or `"dark"`: the host’s resolution of `system` for SSR/no-flash bootstrap |
| `host` | no | Free-form host identifier for diagnostics; KPress never special-cases this value |
| `asset_url_prefix` | no | URL prefix the host uses to serve `/kpress-static/...`; defaults to `/kpress-static/` |
| `show_doc_header` | no | Whether a document-profile fragment renders its title header; defaults to `true` |
| `widgets` | no | Widget presence + opaque config map (same shape as `format.widgets`); echoed in the response payload so host-mounted widgets read the same config the standalone page model carries |
| `extra_tags` | no | Additional inert HTML/XML tags admitted by the sanitized render path |
| `extra_attributes` | no | Additional inert attributes admitted only on pass-through tags |

Render response shape:

```jsonc
{
  "type": "kpress-rendered-document",
  "html": "<!-- HTML fragment to inject into the document body -->",
  "profile": "document" | "source" | "table" | "tree" | "plain",
  "printable": true,
  "assets": {
    "schema_version": "kpress-asset-manifest-v2",
    "assets": [
      {
        "id": "css/document.css",
        "kind": "package",
        "path": "css/document.css",
        "mode": "hosted",
        "media_type": "text/css",
        "content_hash": "<sha256-prefix>",
        "output_path": "css/document.css",
        "public_url": "<asset_url_prefix>v<version>/css/document.css",
        "entry_point": true,
        "loading": "stylesheet"
      },
      {
        "id": "js/runtime.js",
        "kind": "package",
        "path": "js/runtime.js",
        "mode": "hosted",
        "media_type": "text/javascript",
        "content_hash": "<sha256-prefix>",
        "output_path": "js/runtime.js",
        "public_url": "<asset_url_prefix>v<version>/js/runtime.js",
        "entry_point": false,
        "loading": "module"
      }
    ],
    "import_map": {}
  },
  "widgets": { "settings": { "choosers": ["theme"] } },  // normalized presence + opaque config
  "model": { "version": 1, "title": "...", "route": "", "profile": "document",
             "headings": [...], "widgets": { ... } },    // same keys as #kpress-page-model
  "diagnostics": []
}
```

The `model` field carries exactly the static page model
(`contract.py::PUBLIC_PAGE_MODEL_KEYS`; `route` is empty, as fragments have no site
route), so a widget reading `kpress.model()`-shaped data works identically when the host
feeds it the payload’s `model`.

The response is JSON-round-trippable.
The host injects `html` into a container, serves every manifest asset, emits tags only
for assets with `entry_point: true`, and honors each entry point’s `loading` value:
`stylesheet`, `module`, or `classic`. If `import_map` is non-empty, its mappings must be
installed before any module entry point.
Dependency-only assets and `resource` entries are served but do not receive direct
browser tags. There is no per-request mutation of global state.

### Asset Serving

KPress package assets live at `/kpress-static/v<version>/<rel_path>`. The host mounts a
route that calls `kpress.runtime.get_static_asset(rel_path)` and returns the resulting
`KPressAsset` (`content`, `media_type`, `etag`, `cache_control`). The runtime
guarantees:

- Path traversal is rejected (paths with `..` or absolute prefixes raise
  `KPressAssetNotFoundError`).
- Versioned URLs (`/kpress-static/v<version>/...`) return
  `cache-control: public, max-age=31536000` (long-lived, but **not** `immutable`);
  unversioned URLs return `no-cache`. The version segment is only a coarse fingerprint,
  so the host can revalidate against the ETag rather than being locked to stale bytes;
  see [Static Asset Caching](kpress-design.md#static-asset-caching) for the rationale.
- `etag` is content-stable; the host can honor `If-None-Match` (the route answers a
  matching conditional request with `304`).

A host that wants to point at a CDN-hosted KPress bundle passes a different
`asset_url_prefix` in `KPressRenderRequest`; KPress URL-builds against that prefix
without any code change.

### `postMessage` Protocol (Embedded Reader → Host)

When the reader runs inside an iframe (or any sandboxed host), `js/host.js` posts the
following messages to the parent window so the host can resize, expand, or close the
embedded surface:

| Message type | Payload | When |
| --- | --- | --- |
| `kpress:ready` | `{ id?, height }` | First paint settled; the host can size the iframe |
| `kpress:resize` | `{ id?, height }` | Reader content size changed (DOM mutation, font swap, viewport change) |
| `kpress:expand` | `{ id?, expanded: bool }` | User toggled the standalone expand control |
| `kpress:close` | `{ id?, reason: “control” | “escape” }` |

The host opts into Escape-to-close behavior; KPress does not assume it.
All messages include the document id when one was provided.

### Theme Mode Plumbing

`theme_mode` is one of `"system" | "light" | "dark"` and represents the user’s
preference. `resolved_theme` (`"light" | "dark"`) is the host’s resolution of `system`
for the initial server render.
KPress uses it to stamp `data-kpress-resolved-theme` on `<html>` for a no-flash first
paint.

After load, `theme.js` listens for the system color-scheme media query and updates the
resolved attribute live; it also persists explicit `theme_mode` choices to the active
`kpress.storage` adapter under `kpress.theme`. The standalone full-page render ships an
accessible settings gear with System, Light, and Dark choices bound to the same
machinery. Embedded hosts with their own theme control set `theme_mode` per request and
can replace the registered `theme` behavior.

### Print Profile Mapping

The host’s `view` (or explicit `profile`) maps to a KPress print profile via
`normalize_print_profile`. The accepted KPress profiles are
`{document, source, table, tree, plain}`. Host aliases that already work:

| Host view | KPress profile |
| --- | --- |
| `rendered`, `doc`, `markdown` | `document` |
| `text`, `code` | `source` |
| any unrecognized name | rejected with `KPressInvalidRequestError` |

The print profile drives `print.css` rules: `document` strips chrome and prepares for
A4/Letter pagination; `source` keeps line numbers and switches to mono; `table` / `tree`
reuse the source profile with structural overrides.
The host hides its own chrome (`.app-header`, `.tab-bar`, `.tree-pane`, `.file-header`)
via its own `@media print` rules.
KPress does not reach outside its `.kpress` container.

### Static Export Seam

For “render this document into a publishable artifact” use cases, the host calls
`kpress.runtime.export_document(KPressExportRequest)` rather than `render_view`. The
current implementation supports the single-page export path.

| `KPressExportRequest` field | Choices | Meaning |
| --- | --- | --- |
| `path` | logical source path | Document identity and base directory for relative assets |
| `source_text` | text or `None` | Host-decoded document text; when omitted, KPress reads `path` as UTF-8 |
| `print_profile` | `document`/`source`/`table`/`tree`/`plain` | Same as the render contract |
| `export_mode` | `page` | Supported output shape. `single-file` fails explicitly; the other declared literals are reserved and do not yet select distinct implementations. |
| `asset_mode` | `linked` (default), `hashed` | Package-asset shape. The declared low-level `inline` mode is not self-contained and is not a supported portable export. |
| `optimize` | bool | Maps to `optimizer=full` when true |
| `destination` | path | Where to write the artifact; KPress derives a default from `path` if omitted |
| `extra_tags` | tag names | Additional pass-through tags admitted by the sanitizer |
| `extra_attributes` | attribute names | Additional inert attributes admitted on pass-through tags |

The dataclass also carries `kind`, `view`, and `theme_mode`; the current single-page
implementation does not use those fields.
PDF export is available through the local `kpress export --pdf` workflow, not through
this runtime request.
A host surfaces the returned build report or a typed publishing error to the user.

### Failure Modes the Host Must Handle

| Exception | Origin | Host response |
| --- | --- | --- |
| `KPressInvalidRequestError` | Malformed request (e.g. unknown print profile) | 400 with the underlying message |
| `KPressRenderError` | Render pipeline raised | 502 with diagnostics |
| `KPressAssetNotFoundError` | Asset path rejected as unsafe or missing | 404 |
| `KPressPublishError` | Static export cannot complete safely, including unsupported modes | Surface as an export failure |
| `KPressMissingOptionalDependencyError` | Requested optimizer or PDF dependency is unavailable | Surface as a setup error; do not silently downgrade |
| `KPressOptimizerError` | The selected optimizer fails | Surface as an export failure with the original diagnostic |

`KPressInvalidRequestError` is a `ValueError` subclass for ergonomic catching, but hosts
should catch it specifically rather than catching all `ValueError`s.

### Embedding Adapter Guidance

An embedding adapter should import `kpress.runtime` as a required dependency, translate
KPress exceptions only at an application boundary that needs application-specific error
types, serve the full asset closure, and keep host chrome outside the KPress fragment.
If an application deliberately makes KPress optional, its availability probe and
fallback are application-owned; KPress itself does not provide a fail-quiet adapter.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
