---
type: is
id: is-01ktr8d5nfmzq3nbamdte1hwd6
title: Rewrite or prune internal monorepo planning docs before public release
kind: task
status: open
priority: 2
version: 4
labels: []
dependencies: []
created_at: 2026-06-10T07:54:30.958Z
updated_at: 2026-06-10T08:51:27.525Z
---
TODO.md, docs/kpress-completion-plan.md, and the docs/*.runbook.md files carry trading-* bead references and monorepo paths from the original repo. Per EXTRACTION.md, rewrite for a standalone audience or prune before the repo/package goes public. Also: remove the 'Private :: Do Not Upload' classifier in pyproject.toml and finalize SECURITY.md reporting process at first publish (see EXTRACTION.md Release Blockers).

## Notes

Monorepo reference scrub landed on PR #2: trading-* bead IDs renamed to orig-*, metabrowser references rewritten as generic host-app wording across code comments, CSS/JS, docs, and goldens; remaining packages/kpress doc paths fixed. Still open for first publish: remove 'Private :: Do Not Upload' classifier and finalize SECURITY.md reporting process (see EXTRACTION.md Release Blockers).
