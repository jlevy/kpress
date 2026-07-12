---
type: is
id: is-01ktr8d5nfmzq3nbamdte1hwd6
title: Rewrite or prune internal monorepo planning docs before public release
kind: task
status: open
priority: 1
version: 5
labels: []
dependencies: []
created_at: 2026-06-10T07:54:30.958Z
updated_at: 2026-07-12T23:34:30.039Z
---
TODO.md, docs/kpress-completion-plan.md, and the docs/*.runbook.md files carry trading-* bead references and monorepo paths from the original repo. Per EXTRACTION.md, rewrite for a standalone audience or prune before the repo/package goes public. Also: remove the 'Private :: Do Not Upload' classifier in pyproject.toml and finalize SECURITY.md reporting process at first publish (see EXTRACTION.md Release Blockers).

## Notes

Release audit 2026-07-12: still blocks first publish. pyproject.toml carries Private :: Do Not Upload; SECURITY.md still has placeholder private-channel reporting; TODO/completion/design docs retain stale pre-extraction status and advertise nonexistent CLI commands. Before removing the upload block, also decide whether publish.yml workflow_dispatch may publish an untagged dynamic dev version, confirm the pending PyPI trusted publisher, and use an alpha tag such as v0.1.0a1.
