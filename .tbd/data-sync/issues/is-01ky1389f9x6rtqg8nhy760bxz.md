---
type: is
id: is-01ky1389f9x6rtqg8nhy760bxz
title: "PR #31 R1: prevent doc-actions overlap on paragraph-first cards"
kind: bug
status: closed
priority: 1
version: 4
labels: []
dependencies: []
parent_id: is-01ky12h9ncf417yfvz67jzps92
created_at: 2026-07-21T01:04:43.493Z
updated_at: 2026-07-21T01:14:30.300Z
closed_at: 2026-07-21T01:14:30.299Z
close_reason: "Fixed and regression-tested in 6ac0b89; merged through PR #31."
---
Review finding R1: the absolute doc-actions cluster overlaps the first paragraph at mobile width when .kpress-long-text has no leading H1 (including show_doc_header=false). Reserve the action row for non-H1-leading card content and add a regression assertion; verify mobile and existing H1 layouts.

## Notes

Resolved in 6ac0b89. Added CSS action-row clearance for non-H1-leading card content, asset-contract regression coverage, and verified the 390px rendered geometry no longer overlaps.
