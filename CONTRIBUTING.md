# Contributing to KPress

KPress is developed with a package-local quality gate.

Run these checks from the repository root before submitting changes:

```bash
uv run pytest tests --tb=short -q
uv run python devtools/lint.py --check
```

For documentation-only changes, also run:

```bash
uv run codespell
git diff --check
```

KPress browser assets are source-first native ESM. Do not add a host build step or a
runtime JavaScript bundler requirement without updating `kpress-design.md`, tests, and
the package lint gate in the same change.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
