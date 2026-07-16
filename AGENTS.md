# Project Instructions for AI Agents

This file provides instructions and context for AI coding agents working on this
project.

## Supply-Chain Security (read before installing anything)

Before adding, upgrading, or running any dependency—including zero-install runners
(`npx`, `uvx`, `pnpm dlx`, `bunx`)—follow
[`SUPPLY-CHAIN-SECURITY.md`](SUPPLY-CHAIN-SECURITY.md).

- **14-day cool-off** on all third-party packages; pin exact versions; never `@latest`.
- **First-party exemption:** packages we publish from `github.com/jlevy/*` (tbd,
  flowmark-rs, repren, pprose) skip the cool-off but are still pinned to exact versions.
- Full policy: `tbd guidelines supply-chain-hardening`.

<!-- BEGIN TBD INTEGRATION format=f06 surface=agents-md -->
## tbd

This repository uses **tbd** for git-native issue tracking (beads), spec-driven
planning, and on-demand engineering guidelines.
As the agent, you operate tbd on the user’s behalf: translate their requests into tbd
actions rather than telling them to run commands.

- Run `tbd prime` to load current project state and the full tbd workflow.
- Run `tbd skill` for the complete reusable tbd skill instructions.
- Run `tbd shortcut --list` and `tbd guidelines --list` for on-demand resources.
- Track all work as beads: `tbd create`, `tbd ready`, `tbd close`, and `tbd sync`.

<!-- END TBD INTEGRATION -->

## Build and Test

```bash
make install     # install the frozen Python and npm dependency graphs
make lint-check  # full read-only lint and package-policy gate
make test        # Python and browserless DOM tests
make verify      # complete release gate, including audits and artifact inspection
```

The lint gate runs Ruff, basedpyright, codespell, Biome 2, TypeScript `checkJs`,
browserless DOM tests for the ESM helpers, and the extraction safety checks
(`devtools/public_hygiene.py`). The complete gate also audits the locked Python and npm
graphs, builds both distributions, rejects repository-only content, and performs an
isolated wheel smoke test.

## Architecture Overview

KPress is a Python library and CLI that renders Markdown into readable HTML documents
and publishes them as static sites.
[README.md](README.md) is the orientation map; [kpress-design.md](docs/kpress-design.md)
is the architecture and public-contract reference.

## Conventions & Patterns

- **Rendering truth:** `page.html.jinja` is the one live packaged template and owns the
  standalone page shell.
  Its public variables are pinned in `contract.PUBLIC_TEMPLATE_VARIABLES` and it renders
  through the strict environment in
  [`format/templating.py`](src/kpress/format/templating.py).
  Fragment and component markup currently lives in `format/render.py` and
  `format/markdown.py`; keep changes local to the existing owner.
  Moving that markup into templates is a separate migration and must switch code and
  tests in the same patch—never add an unused template.
- The public surface (Python names, CSS classes/variables, template variables, data
  attributes, manifest markers) is pinned in `kpress.contract` and enforced by tests.
  Change it only with contract, docs, tests, and goldens updated in the same patch,
  never via compatibility shims.
- Browser assets are source-first native ESM with no build step; do not add a bundler or
  host build requirement (see [CONTRIBUTING.md](CONTRIBUTING.md)).
- Docs follow `tbd guidelines common-doc-guidelines` and carry its footer comment.

<!-- BEGIN FLOWMARK INTEGRATION format=f02 surface=agents-md -->
## flowmark

Auto-format Markdown with `flowmark` for clean, semantic git diffs.

- Run `flowmark --auto <files>` on Markdown you create or edit.
- Run `flowmark --docs` for full usage and `flowmark --skill` for the skill.
- If `flowmark` is not on `PATH`, use a pinned `uvx` runner (never `@latest`).
- Fast Rust port (recommended): `uvx --from flowmark-rs==0.3.2 flowmark`.
- Python build (library / newest patch): `uvx --from flowmark==0.7.2 flowmark`.

<!-- END FLOWMARK INTEGRATION -->

<!-- BEGIN PPROSE INTEGRATION format=f01 -->
## Practical Prose (pprose)

Practical Prose: an evaluation toolkit and editorial workflows for practical documents.
Use when the user asks to improve, audit, score, or compare practical documents.

Discover the tool from the CLI itself: `pprose --help` for commands, `pprose about` for
the project narrative, and `pprose skill --list` / `pprose shortcut --list` /
`pprose guidelines --list` / `pprose runbook --list` for on-demand workflows, playbooks,
style guides, and procedures.

Run pprose as `pprose <command>` if on PATH, else `uvx pprose@0.1.0 <command>`
(zero-install via uv).

<!-- END PPROSE INTEGRATION -->

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
