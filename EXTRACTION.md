# KPress Extraction Checklist

KPress was extracted from its original monorepo into this standalone repository
(github.com/jlevy/kpress) in June 2026. This checklist defines the public package
boundary; `devtools/extraction_check.py` enforces the safety rules below as part of the
lint gate.

## Public Package Inventory

The package includes:

- `src/kpress/`
- `docs/`
- `README.md`
- `TODO.md`
- `kpress-design.md`
- `kpress-icons.md`
- `kpress-reader-features.md`
- `CONTRIBUTING.md`
- `LICENSE`
- `NOTICE.md`
- `SECURITY.md`
- `EXTRACTION.md`
- `pyproject.toml`
- package-local tests and devtools that are needed to preserve the package quality gate

## Internal-Only Material

Do not ship internal planning or evidence docs as public docs unless they are first
rewritten for a standalone audience.

## Release Blockers

Before public distribution:

- Remove the `Private :: Do Not Upload` classifier from `pyproject.toml`.
- Replace the placeholder reporting process in `SECURITY.md` with the public one.
- Rewrite or prune internal planning docs (`TODO.md` bead references,
  `docs/kpress-completion-plan.md`, runbook bead references) for a standalone audience.
- Re-run `uv run python devtools/lint.py --check`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
