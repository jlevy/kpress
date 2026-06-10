---
type: is
id: is-01ktr8d5nfmzq3nbamdte1hwd6
title: Rewrite or prune internal monorepo planning docs before public release
kind: task
status: open
priority: 2
version: 2
labels: []
dependencies: []
created_at: 2026-06-10T07:54:30.958Z
updated_at: 2026-06-10T08:36:53.313Z
---
TODO.md, docs/kpress-completion-plan.md, and the docs/*.runbook.md files carry trading-* bead references and monorepo paths from the original repo. Per EXTRACTION.md, rewrite for a standalone audience or prune before the repo/package goes public. Also: remove the 'Private :: Do Not Upload' classifier in pyproject.toml and finalize SECURITY.md reporting process at first publish (see EXTRACTION.md Release Blockers).

## Notes

Doc review pass 2026-06-10 made a first cut at this: README.md rewritten as a concise orientation doc with a doc map; footers normalized to common-doc-guidelines.md; AGENTS.md placeholders filled; broken ../../ monorepo links fixed in kpress-design.md, kpress-reader-features.md, kpress-icons.md, and the e2e runbook; stale packages/kpress paths fixed in kpress-design.md, TODO.md, and docs/kpress-completion-plan.md; kpress.yml config example moved from README into docs/kpress-static-publish.runbook.md. REMAINING for this bead: TODO.md (~46 trading-* bead refs, monorepo spec links, MetaBrowser/TableView narrative), docs/kpress-completion-plan.md (~100 trading-* refs, monorepo links), and kpress-design.md's 'Implementation Beads' + 'Current Implementation Status' ledger sections (~98 trading-* refs; the doc itself says it should not carry status) all still need a standalone-audience rewrite. SECURITY.md placeholder reporting process still stands (see EXTRACTION.md release blockers).
