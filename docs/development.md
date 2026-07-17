# Development

## Prerequisites

Install a supported Python and uv 0.11.26 or newer as described in
[Installation](installation.md).
Development pins Node.js 24.18.0 and requires npm 11.10.0 or newer within npm 11, as
declared in `package.json`. Both nvm (`nvm use`) and fnm (`fnm use`) read the repository
pins in `.nvmrc` and `.node-version`. The repository gates use the exact versions in
`package.json` and `package-lock.json` for Biome, TypeScript `checkJs`, and browserless
Vitest coverage over the native ESM assets shipped in the wheel.

Fork and clone [jlevy/kpress](https://github.com/jlevy/kpress).
Run all commands below from the repository root.

## Common Workflows

The `Makefile` owns the local and GitHub Actions workflows.

```shell
# Synchronize the Python and JavaScript environments from the repository locks.
make install

# Install the git hooks (lefthook; see lefthook.yml). Pre-commit hooks
# auto-format staged Python (ruff), JS/CSS/JSON (Biome), Markdown (flowmark),
# and fix spelling; pre-push runs the read-only lint and test gates.
make hooks-install

# Install, format, lint, and test.
make

# Auto-format maintained Python, JavaScript, CSS, JSON, and Markdown.
make format

# Build the source distribution and wheel.
make build

# Run the quality gate and apply supported fixes.
make lint

# Run the read-only quality gate used by CI.
make lint-check

# Run Python and browserless DOM tests.
make test

# Audit the frozen Python and npm dependency graphs.
make audit

# Run the complete read-only release gate: install, lint, tests, audits, and builds.
make verify

# Delete local build artifacts and installed environments.
make clean
```

Focused equivalents used while diagnosing an individual gate:

```shell
make install
uv --config-file uv.toml run --frozen pytest tests --tb=short -q
npx --no-install vitest run --config tests/js/vitest.config.mjs
make audit
make build
```

Install the repository hooks after the first environment sync:

```shell
make hooks-install
```

The pre-commit hook formats staged Python, JavaScript, CSS, JSON, and Markdown, then
checks spelling. The pre-push hook runs the read-only lint and test gates.

## Dependency Changes

Read [Supply-Chain Security](../SUPPLY-CHAIN-SECURITY.md) before changing a dependency.
Every change must have a concrete reason, respect the 14-day cool-off unless a
documented exception applies, preserve exact lockfile resolution, disable install
scripts by default, and include a review of the lockfile diff and vulnerability-audit
results.

`uv.toml` applies the repository-wide uv version and cool-off policy.
`package.json`, `.npmrc`, and the npm lock enforce the corresponding Node, npm,
install-script, and release-age policy.
`devtools/check_supply_chain.py` checks the few cross-file safety rules that package
managers and standard linters do not enforce.

`make upgrade` exists for a deliberate, reviewed re-resolution.
Do not run it as routine maintenance or use an unpinned `@latest` or zero-install
command.

## Documentation

Documentation follows `tbd guidelines common-doc-guidelines`. Keep the
[documentation index](README.md) current, describe the present implementation, avoid
duplicating contract lists owned by `kpress.contract`, and retain the exact footer at
the end of every maintained Markdown document.

Run `make format` after editing maintained source or documentation.
For a focused documentation pass, `make format-markdown` applies the pinned Flowmark
formatter and respects `.flowmarkignore`; excluded fixtures and example content remain
byte-stable.

## IDE Setup

If you use VSCode or a fork like Cursor or Windsurf, you can install the following
extensions:

- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [Based Pyright](https://marketplace.visualstudio.com/items?itemName=detachhead.basedpyright)
  for type checking. Note that this extension works with non-Microsoft VSCode forks like
  Cursor.

## Publishing Releases

See [Publishing KPress Releases](publishing.md) for the trusted PyPI workflow.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
