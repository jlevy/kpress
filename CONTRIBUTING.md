# Contributing to KPress

KPress is developed with a package-local quality gate.

Start with the [development guide](docs/development.md) for the supported toolchain and
common commands. Follow the [supply-chain policy](SUPPLY-CHAIN-SECURITY.md) before
installing or upgrading a dependency.

Run these checks from the repository root before submitting changes:

```bash
uv run pytest tests --tb=short -q
uv run python devtools/lint.py --check
```

For documentation-only changes, format the maintained Markdown tree and run the same
check-only gate:

```bash
make format
uv run python devtools/lint.py --check
git diff --check
```

Documentation follows `tbd guidelines common-doc-guidelines` and ends with the exact
guideline footer used in this file.

KPress browser assets are source-first native ESM. Do not add a host build step or a
runtime JavaScript bundler requirement without updating `docs/kpress-design.md`, tests,
and the package lint gate in the same change.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
