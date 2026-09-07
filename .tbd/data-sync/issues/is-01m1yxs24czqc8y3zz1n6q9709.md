---
type: is
id: is-01m1yxs24czqc8y3zz1n6q9709
title: "Quotation marks from PT Serif: retire the LocalPunct borrowing of Georgia"
kind: task
status: in_progress
priority: 2
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-07T21:53:20.010Z
updated_at: 2026-09-07T22:54:53.475Z
---
style-tokens.css declares LocalPunct as local("Georgia") over U+0022, U+0027 and U+2018-201D and leads the prose stack with it, so every quotation mark and apostrophe on screen comes from the reader's Georgia when they have it, at Georgia's metrics, and from PT Serif when they do not. The squares shell already drops it in print for exactly that reason. Owner's rule (2026-09-07): no system fonts in documents. Remove LocalPunct from the default prose stack so PT Serif sets its own quotes; keep the borrowing available only as an explicit host hook if a host wants it, and document why it was there (Georgia's quotes were preferred) so the choice is not lost. Screenshot the change in the goldens' prose fixture before and after. Then squares removes its print-only prose override.
