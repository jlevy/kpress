---
type: is
id: is-01ktr8d5nfmzq3nbamdte1hwd6
title: Rewrite or prune internal monorepo planning docs before public release
kind: task
status: in_progress
priority: 1
version: 10
spec_path: TODO.md
labels: []
dependencies:
  - type: blocks
    target: is-01kxcppx52sr5t9s438qwamc62
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-06-10T07:54:30.958Z
updated_at: 2026-07-13T03:02:14.844Z
---
TODO.md, docs/kpress-completion-plan.md, and the docs/*.runbook.md files carry trading-* bead references and monorepo paths from the original repo. Per EXTRACTION.md, rewrite for a standalone audience or prune before the repo/package goes public. Also: remove the 'Private :: Do Not Upload' classifier in pyproject.toml and finalize SECURITY.md reporting process at first publish (see EXTRACTION.md Release Blockers).

## Notes

Restoring TODO.md as a standalone public two-dimensional backlog. The stale private orig-* ledger is being replaced with verified kpr-* beads and current capability status; docs/kpress-completion-plan.md remains pruned only where TODO.md absorbs its still-relevant tracking role.
