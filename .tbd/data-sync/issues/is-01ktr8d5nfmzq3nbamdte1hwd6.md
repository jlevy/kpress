---
type: is
id: is-01ktr8d5nfmzq3nbamdte1hwd6
title: Rewrite or prune internal monorepo planning docs before public release
kind: task
status: open
priority: 2
version: 3
labels: []
dependencies: []
created_at: 2026-06-10T07:54:30.958Z
updated_at: 2026-06-10T08:49:31.630Z
---
TODO.md, docs/kpress-completion-plan.md, and the docs/*.runbook.md files carry trading-* bead references and monorepo paths from the original repo. Per EXTRACTION.md, rewrite for a standalone audience or prune before the repo/package goes public. Also: remove the 'Private :: Do Not Upload' classifier in pyproject.toml and finalize SECURITY.md reporting process at first publish (see EXTRACTION.md Release Blockers).

## Notes

2026-06-10: Internal-name scrub landed on extract-kpress-standalone (commit db51e3d): host-app/plugin names (MetaBrowser, TableView) genericized across src/tests/docs; pre-extraction bead IDs renamed trading-* -> orig-* (convention documented at top of TODO.md); monorepo-only spec links converted to plain text; goldens regenerated; vacuous host-import contract test removed; extraction commit message + PR #2 body reworded to drop the monorepo name. Remaining for this bead: optional deeper rewrite/prune of planning docs for a standalone audience, remove Private::Do-Not-Upload classifier, finalize SECURITY.md contact. Note: pre-scrub file contents still exist in intermediate commits of the PR branch; squash-merge PR #2 (and delete the branch) to keep them out of mainline history.
