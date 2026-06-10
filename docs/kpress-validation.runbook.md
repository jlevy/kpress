---
title: KPress End-to-End Validation
description: Comprehensive validation runbook for KPress automated checks, agent-operated smoke checks, and final human visual and functional acceptance.
---
# KPress End-to-End Validation

Use this runbook after changing KPress rendering, assets, CLI workflows, publishing,
host integration, or the KPress plan/design docs.

Each part can run independently.
For a full validation pass, run Parts 1-4, complete the agent review in Part 5, then ask
the human operator to complete Part 6.

Run modes:

- **Single part:** run only the section that matches the changed surface.
- **Automated pass:** run Parts 1-4 in order.
- **Full acceptance pass:** run Parts 1-4, perform the agent review in Part 5, and then
  hand the exact generated outputs to the human operator for Part 6.

## Prerequisites

- Run from the repository root.
- Use `uv` for every Python command.
- KPress validation does not require Docker images, GitHub job containers, or a
  repository Playwright dependency.
  Keep browser automation as an optional operator aid unless a later spec explicitly
  changes that boundary.
- Package resolution must respect the two-week supply-chain cool-off
  (SUPPLY-CHAIN-SECURITY.md): `UV_EXCLUDE_NEWER` gates Python resolution (set in CI;
  export locally when re-resolving), `.npmrc` sets npm’s `min-release-age=14` with exact
  pins in `package.json`, and both lockfiles are committed and installed frozen.
  Current KPress npm pins are `@biomejs/biome@2.4.14`, `typescript@6.0.3`,
  `vitest@4.1.5`, and `happy-dom@20.9.0`.
- Keep generated scratch output outside the repo unless you are intentionally updating
  golden fixtures.
- If a command below returns non-zero where a non-zero status is expected, the command
  block says so explicitly.

Set a scratch root once if you are running more than one section:

```bash
export REPO_ROOT="$(git rev-parse --show-toplevel)"
export KPRESS_VALIDATION_ROOT="${TMPDIR:-/tmp}/kpress-validation-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$KPRESS_VALIDATION_ROOT"
```

## Part 0 — Runtime Readiness (`kpress doctor`)

Before anything else, probe whether this machine can run the surfaces you are about to
validate. This is a runtime probe, not a dev quality gate.

```bash
uv run kpress doctor
uv run kpress doctor --config "$KPRESS_VALIDATION_ROOT/site/kpress.yml" --json
```

`doctor` never hits the network by default and never fails on bare discovery;
`--profile`/`--config` runs exit non-zero only when a requested or config-required
capability (optimizer `full`, `br`, PDF) is unavailable.

## Part 1 — Automated Package Gates

These are the required package gates for ordinary KPress changes.

```bash
uv run pytest tests --tb=short -q
uv run python devtools/lint.py --check
uv run python devtools/js_dom_tests.py
git diff --check
```

Expected result:

- KPress tests pass.
- KPress lint passes, including Ruff, Ruff format check, basedpyright, codespell, npm
  supply-chain policy, Biome, `tsc --checkJs`, and browserless DOM tests.
- Browserless DOM tests cover native ESM reader behavior for theme, TOC, tooltips,
  tables, code-copy, video popovers, and tabs.
- `git diff --check` has no whitespace errors.

When JavaScript, CSS, or JSON needs automated formatting, run the package-owned Biome
fix pass intentionally and review its diff:

```bash
uv run python devtools/biome.py check --write src tests biome.json
git diff -- src tests biome.json
```

Focused JavaScript validation:

```bash
uv run python devtools/tsc_check.py
uv run python devtools/js_dom_tests.py
```

When validating a pull request, also run the PR CI gate after pushing:

```bash
gh pr checks <pr-number> --watch
```

Expected PR checks:

- `lint` (full quality gate including the JS checks)
- `test` (one job per supported Python version)
- `wheel-smoke` (build the wheel, install into a clean venv, exercise the CLI)

Before committing, stage only the intended files and let the repo hook run normally.
To run the same staged-file hook explicitly:

```bash
npx lefthook run pre-commit
```

Review and re-stage any hook-written Markdown or spelling fixes before committing.

## Part 2 — Host Adapter Boundary Gates

Run these when changing KPress runtime APIs, package assets, print metadata, static
export seams, or host adapter behavior.

The embedding host maintains its own KPress adapter tests (for example, export-seam,
render-route, asset-loading, plugin-SDK, and print-contract tests).
Run the host’s focused KPress test suite from the host project:

```bash
# Example: run the host project's KPress-focused tests.
# Adjust the project name and test paths for your embedding host.
uv run --project <host-project> pytest \
  <host-project>/tests/test_kpress_export_seam.py \
  <host-project>/tests/test_kpress_render_route.py \
  <host-project>/tests/test_kpress_asset_loading_js.py \
  <host-project>/tests/test_kpress_print_contract.py \
  --tb=short -q
```

Expected result:

- Focused KPress/host adapter tests pass.
- The host adapter still imports only the KPress runtime path during ordinary dynamic
  rendering.
- The adapter does not import KPress publisher, PDF, optimizer, subprocess, browser, or
  Node-related modules unless a static export path explicitly calls them.

## Part 3 — Golden Fixtures

Run this when rendered HTML, packaged assets, static output, manifest shape, or accepted
fixtures may have changed.

First check whether existing goldens still match:

```bash
uv run pytest \
  tests/test_golden_render.py \
  tests/test_golden_publish.py \
  --tb=short -q
```

If the change intentionally alters output, regenerate the package-owned goldens:

```bash
KPRESS_UPDATE_GOLDENS=1 uv run pytest \
  tests/test_golden_render.py \
  tests/test_golden_publish.py \
  --tb=short -q
```

Then review the generated artifact diff:

```bash
git diff -- tests/golden/accepted
```

Accept golden changes only when the diff is expected.
Review at least:

- document structure and semantic classes
- asset order and asset URLs
- manifest `schema_version`
- content hashes and hashed filenames
- diagnostics JSON
- print-surface markup
- absence of host-shell selectors in KPress output

## Part 4 — CLI and Static Publishing Smoke

This part exercises the public CLI workflows and static publisher in a disposable tree.
It can run independently of the golden update flow.

> **Note on asset sealing in v1.** `kpress build` does not seal document-local or
> external asset refs in v1. Document-local refs (`./image.png`) and external CDN URLs
> (`https://cdn…/foo.js`) are emitted into the rendered HTML verbatim; the deploy layer
> (CDN, S3, Netlify, etc.)
> owns those files and runtime fetches.
> The `public-sealed` directory names below describe the *hashed + gzipped package-asset
> shape* (production layout), not a sealed asset graph.
> See `kpress-design.md` § “Asset sealing: deferred for v1” and
> `docs/project/specs/active/plan-2026-05-21-kpress-remove-sealing-for-v1.md` for the v2
> roadmap.

Create inputs:

```bash
export KPRESS_VALIDATION_ROOT="${KPRESS_VALIDATION_ROOT:-${TMPDIR:-/tmp}/kpress-validation-$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$KPRESS_VALIDATION_ROOT"

cp tests/fixtures/documents/rich-components.md \
  "$KPRESS_VALIDATION_ROOT/rich-components.md"
cp -R tests/fixtures/sites/basic "$KPRESS_VALIDATION_ROOT/site"
```

Run local document workflows:

```bash
uv run kpress \
  --work-root "$KPRESS_VALIDATION_ROOT/.kpress" \
  init --config "$KPRESS_VALIDATION_ROOT/kpress.yml"

uv run kpress \
  --work-root "$KPRESS_VALIDATION_ROOT/.kpress" \
  format "$KPRESS_VALIDATION_ROOT/rich-components.md" \
  --output-dir "$KPRESS_VALIDATION_ROOT/formatted"

uv run kpress \
  --work-root "$KPRESS_VALIDATION_ROOT/.kpress" \
  export "$KPRESS_VALIDATION_ROOT/rich-components.md" \
  --html "$KPRESS_VALIDATION_ROOT/export/rich-components.html" \
  --pdf "$KPRESS_VALIDATION_ROOT/export/rich-components.pdf"
```

Run static publishing in both modes:

```bash
uv run kpress build \
  --config "$KPRESS_VALIDATION_ROOT/site/kpress.yml" \
  --output-dir "$KPRESS_VALIDATION_ROOT/site/public-readable"

uv run kpress build \
  --config "$KPRESS_VALIDATION_ROOT/site/kpress.yml" \
  --asset-mode hashed \
  --output-dir "$KPRESS_VALIDATION_ROOT/site/public-sealed" \
  --precompress gzip
```

### Brotli precompression — opt-in extra

`gzip` precompression is in the stdlib and runs in every install.
`br` (Brotli) is gated behind the `kpress[optimize]` extra so the base wheel stays lean.
The default `uv sync` does NOT install it, which is why the unit test
`tests/test_optimize.py::test_precompress_brotli_records_compression_method` skips (CI
installs `--all-extras`, so its `test` jobs exercise it).
Re-run with the extra locally to exercise the path:

```bash
uv sync --extra optimize
uv run pytest \
  tests/test_optimize.py::test_precompress_brotli_records_compression_method \
  --tb=short -q
```

End-to-end brotli build smoke (the extra must already be installed):

```bash
uv run kpress build \
  --config "$KPRESS_VALIDATION_ROOT/site/kpress.yml" \
  --asset-mode hashed \
  --output-dir "$KPRESS_VALIDATION_ROOT/site/public-sealed-br" \
  --precompress gzip --precompress br
# Expect: `.br` sidecars beside `.html`/`.css`/`.js` and the build
# manifest's `precompress` field includes both methods.
```

Confirm the missing-extra path is honest — without `kpress[optimize]` installed,
requesting `br` must fail with exit code `2` and a clear diagnostic, not produce partial
output:

```bash
# Run this from a venv that does NOT have the optimize extra.
if uv run kpress build \
  --config "$KPRESS_VALIDATION_ROOT/site/kpress.yml" \
  --output-dir "$KPRESS_VALIDATION_ROOT/site/public-sealed-br-fail" \
  --precompress br; then
  echo "expected brotli to report missing kpress[optimize] extra"
  exit 1
else
  test "$?" -eq 2
fi
```

Run optimizer and expected missing-extra checks:

```bash
uv run kpress optimize \
  "$KPRESS_VALIDATION_ROOT/export/rich-components.html" \
  --output "$KPRESS_VALIDATION_ROOT/export/rich-components.min.html" \
  --backend full
```

Clipboard and DOCX extras are intentionally absent in the base package.
These commands should return exit code `2` with clear JSON diagnostics:

```bash
if uv run kpress \
  --work-root "$KPRESS_VALIDATION_ROOT/.kpress" \
  paste --title ClipboardSmoke; then
  echo "expected paste to report missing clipboard extra"
  exit 1
else
  test "$?" -eq 2
fi

if uv run kpress \
  --work-root "$KPRESS_VALIDATION_ROOT/.kpress" \
  export "$KPRESS_VALIDATION_ROOT/rich-components.md" \
  --docx "$KPRESS_VALIDATION_ROOT/export/rich-components.docx"; then
  echo "expected export to report missing office extra"
  exit 1
else
  test "$?" -eq 2
fi
```

Expected output files:

```text
$KPRESS_VALIDATION_ROOT/formatted/rich-components.md
$KPRESS_VALIDATION_ROOT/formatted/rich-components.html
$KPRESS_VALIDATION_ROOT/export/rich-components.html
$KPRESS_VALIDATION_ROOT/export/rich-components.pdf
$KPRESS_VALIDATION_ROOT/export/rich-components.min.html
$KPRESS_VALIDATION_ROOT/site/public-readable/index.html
$KPRESS_VALIDATION_ROOT/site/public-readable/_kpress/kpress-manifest.json
$KPRESS_VALIDATION_ROOT/site/public-sealed/index.html
$KPRESS_VALIDATION_ROOT/site/public-sealed/_kpress/kpress-manifest.json
```

Inspect the production manifest:

```bash
sed -n '1,220p' \
  "$KPRESS_VALIDATION_ROOT/site/public-sealed/_kpress/kpress-manifest.json"
```

Confirm:

- `schema_version` is present
- `asset_mode` is `hashed`
- package assets use hashed filenames
- routes include `/` and `/about.html`
- gzip sidecars exist for HTML/CSS/JS/JSON outputs when precompression is configured

## Part 5 — Agent-Operated Manual Review

An agent should run these checks before asking for human visual acceptance.
They are not a substitute for the human checks in Part 6.

### Contract Review

Review the current contract against implementation and docs:

```bash
git diff -- \
  src/kpress/contract.py \
  kpress-design.md \
  docs/project/specs/active/plan-2026-05-16-kpress-package-and-publisher.md
```

Confirm:

- public Python exports in `kpress.contract` match `__all__`
- public CSS classes are present in CSS, templates, or renderer output
- public CSS variables are declared in packaged CSS
- template variables are present in packaged templates
- asset/build manifest keys match the current schema constants
- KPress docs describe the current direct contract instead of compatibility shims

### Static Output Review

Review generated readable and sealed trees:

```bash
find "$KPRESS_VALIDATION_ROOT/site/public-readable" -maxdepth 4 -type f | sort
find "$KPRESS_VALIDATION_ROOT/site/public-sealed" -maxdepth 4 -type f | sort
```

Confirm:

- readable output is uncompressed with linked asset names
- sealed output uses hashed package assets
- sealed output can be opened without unexpected remote network dependencies
- manifests are deterministic and readable
- no host navigation or shell chrome appears in KPress static output

### Local Browser Smoke

Multi-file builds (`linked`, `hashed`, `sealed`) are server-rooted: their asset
references and ES module scripts only resolve over HTTP, never `file://`. Choose the
viewer by build shape, not an ad-hoc server:

- **Multi-file output (developer `linked` / production `hashed`+`sealed`):** review
  through the host-app harness, which is the contracted dynamic KPress surface
  (`/api/kpress/render` plus the `test_kpress_*` suite).
  A focused standalone static server is intentionally not part of this runbook unless a
  concrete need appears; see the lever model in [kpress-design.md](../kpress-design.md)
  ("Combinations under evaluation").
- **Single self-contained file:** only an `inline` build with classic (non-module)
  reader JS opens over `file://`; that combination is deferred (tracked work), so do not
  validate single-doc output via `file://` until it lands.

Do not hand-roll `python -m http.server` as the review path.
If a transient static server is unavoidable for a one-off check, treat it as scratch,
never as the documented procedure.

When reviewing multi-file output through the host harness, confirm:

- the home page renders
- `/about.html` renders
- CSS and JS assets load without 404s
- browser console has no KPress runtime errors
- TOC disclosure opens and closes, and clicking a TOC link marks the active entry
- footnote and internal-link tooltips open and close with Escape
- numeric table cells align as numeric cells
- code-copy controls report success or a recoverable error
- tabs switch by click and keyboard arrows
- the document remains readable at desktop and narrow viewport widths
- print preview shows document content without navigation chrome

Stop the host harness after the check.

Optional Playwright-assisted workflow:

- Use an existing local Playwright install, the Codex browser, or another browser driver
  to walk the checklist above.
- Do not add Playwright to KPress package dependencies for this manual smoke.
- Do not make these browser steps required PR CI unless the KPress testing plan is
  explicitly revised.
- Save screenshots or console/network notes as review evidence when they explain a
  decision or failure.

### Host Embedding Smoke

Start the embedding host against the KPress fixture site.
The exact command depends on the host application:

```bash
# Example: start the host's dev server pointed at the KPress fixture site.
# Adjust the project name and command for your embedding host.
uv run --project <host-project> <host-command> serve \
  tests/fixtures/sites/basic \
  --path docs/index.md \
  --no-open
```

Open the printed URL. Confirm:

- the Markdown document view uses KPress-rendered markup
- KPress assets load from the host’s configured static asset path
- the print icon appears only for printable views
- Command+P prints the document surface, not the file tree or header
- source view remains printable with the source print profile
- no KPress-unavailable fallback warning appears when KPress is installed

Stop the host server after the check.

## Part 6 — Human Visual and Functional Acceptance

The human operator should complete this part before a feature-complete KPress reader or
publishing milestone is considered accepted.

Use generated KPress static output, host-embedded document views, or both.

### Desktop Document View

- Prose width is comfortable and centered.
- Headings, lists, blockquotes, code, tables, footnotes, and details are readable.
- The TOC appears only when expected.
- Internal anchors and footnote links navigate correctly.
- Tooltips/popovers do not overlap critical content.
- No host navigation chrome appears inside the KPress document.

### Mobile and Narrow View

- No text or controls overflow the viewport.
- Tables scroll or flatten in a controlled way.
- TOC controls remain usable.
- Tooltips/popovers are dismissible.
- Source views wrap or scroll predictably.

### Theme Behavior

- `system`, `light`, and `dark` modes render readable text and links.
- Theme changes do not resize or shift document layout unexpectedly.
- Print output stays on a light paper palette even when screen mode is dark.

### Static Publishing

- Readable output is easy to inspect.
- Sealed output uses hashed assets and includes a manifest.
- Sealed output works from a local static server.
- No unexpected remote network requests are made in sealed/offline review.
- Sitemap, robots, and route outputs match the intended site shape.

### Print and PDF

- Command+P hides file trees, app headers, tabs, copy buttons, hover UI, and inactive
  views.
- Page margins, headings, lists, code blocks, tables, footnotes, images, math, and
  diagrams are readable.
- Source PDFs include truncation warnings when source previews are truncated.
- Generated PDF artifacts open and contain expected document text.
- Browser-backed PDFs are optional and require `kpress[pdf]` plus a local Chromium
  install: `uv run --extra pdf playwright install chromium`. The required CI path covers
  the adapter with fake Playwright tests; real Chromium PDF output is manual acceptance
  evidence.

### Host Integration

- Markdown document view uses KPress output.
- Source view uses the correct print profile.
- KPress unavailable mode shows a clear fallback warning and does not break the host.
- Embedded documents handle `kpress:ready`, `kpress:resize`, `kpress:expand`, and
  `kpress:close` `postMessage` events from `js/host.js` without leaking host concerns
  back into KPress.
- Static export seams still delegate to KPress rather than duplicating publisher logic.

## Failure Handling

If validation fails:

1. Capture the failing command or browser action.
2. Save the relevant output path, manifest excerpt, screenshot, browser console excerpt,
   or print preview observation.
3. File or update a KPress bead with the failing area and reproduction steps.
4. Do not update goldens unless the changed output has been reviewed and accepted.

Useful bead labels:

- `kpress`
- `validation`
- `parity`
- `publisher`
- `host-integration`
- `accessibility`

## Whole-Pass Checklist

- [ ] Part 1 automated package gates passed
- [ ] Part 2 host adapter boundary gates passed when relevant
- [ ] Part 3 golden fixtures checked or intentionally updated
- [ ] Part 4 CLI/static publishing smoke passed
- [ ] Part 4 Brotli opt-in extra path verified (with `kpress[optimize]` installed:
  brotli unit test no longer skips and the `--precompress br` build emits `.br`
  sidecars; without the extra: `--precompress br` exits 2 with a clear missing-extra
  diagnostic)
- [ ] Part 5 agent manual review completed
- [ ] Part 6 human visual and functional acceptance completed
- [ ] Any failures were filed as beads with reproduction details

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
