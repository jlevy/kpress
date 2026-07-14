# Development

## Prerequisites

Install a supported Python and uv 0.11.21 or newer as described in
[Installation](installation.md).
Development also requires Node.js 24.18.x and npm 11.10.x or newer within the major
versions permitted by `package.json`. The lint gate uses the exact versions in
`package.json` and `package-lock.json` for Biome, TypeScript `checkJs`, and browserless
Vitest tests over the native ESM assets shipped in the wheel.

Fork and clone [jlevy/kpress](https://github.com/jlevy/kpress).
Run all commands below from the repository root.

## Common Workflows

The `Makefile` owns the local and GitHub Actions workflows.

```shell
# Synchronize the Python and JavaScript environments from the repository locks.
make install

# Install the git hooks (lefthook; see lefthook.yml). Pre-commit hooks
# auto-format staged Python (ruff), JS/CSS/JSON (Biome), Markdown (flowmark),
# and fix spelling; pre-push runs the tests and the extraction safety check.
make hooks-install

# Install, format, lint, and test.
make

# Auto-format maintained Markdown.
make format

# Build the source distribution and wheel.
make build

# Run the quality gate and apply supported fixes.
make lint

# Run the read-only quality gate used by CI.
make lint-check

# Run Python tests.
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
UV_CONFIG_FILE=uv.toml uv sync --all-extras --all-groups --frozen
npm ci
uv run pytest tests --tb=short -q
uv run python devtools/lint.py --check
make audit
make build
```

Install the repository hooks after the first environment sync:

```shell
make hooks-install
```

The pre-commit hook formats staged Python, JavaScript, CSS, JSON, and Markdown, then
checks spelling. The pre-push hook runs tests and extraction-safety checks.

## Dependency Changes

Read [Supply-Chain Security](../SUPPLY-CHAIN-SECURITY.md) before changing a dependency.
Every change must have a concrete reason, respect the 14-day cool-off unless a
documented exception applies, preserve exact lockfile resolution, disable install
scripts by default, and include a review of the lockfile diff and vulnerability-audit
results.

`uv.toml` applies the repository-wide uv version and cool-off policy.
`package.json`, `.npmrc`, and the npm lock enforce the corresponding Node, npm,
install-script, and release-age policy.
`devtools/npm_policy.py` prevents CI or release workflows from bypassing those controls.

`make upgrade` exists for a deliberate, reviewed re-resolution.
Do not run it as routine maintenance or use an unpinned `@latest` or zero-install
command.

## Documentation

Documentation follows `tbd guidelines common-doc-guidelines`. Keep the
[documentation index](README.md) current, describe the present implementation, avoid
duplicating contract lists owned by `kpress.contract`, and retain the exact footer at
the end of every maintained Markdown document.

Run `make format` after editing Markdown.
It applies the pinned flowmark formatter to the maintained tree and respects
`.flowmarkignore`; files intentionally excluded as fixtures or example content remain
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
