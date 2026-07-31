---
type: is
id: is-01kyv0jnjje3stc0byghpz40v2
title: "tooltips.js: copy resolved theme onto portaled overlays"
kind: feature
status: open
priority: 3
version: 2
spec_path: docs/project/specs/active/plan-2026-07-31-declarative-embedding.md
labels: []
dependencies: []
created_at: 2026-07-31T02:38:13.073Z
updated_at: 2026-07-31T03:14:43.295Z
---
Follow-up per PR #40 review finding 3 ('better' option): tooltips portal to document.body and escape non-:root theme scopes. Have tooltips.js copy data-kpress-resolved-theme from the anchor's nearest themed scope onto the portaled element at creation/show so the element form wins and wrapper-scoped hosts get themed overlays without stamping :root.
