---
type: is
id: is-01m1z8drasjh3hct7hke23s0kj
title: "Address review: PR #58 — mathematics paints once"
kind: task
status: open
priority: 1
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T00:59:23.863Z
updated_at: 2026-09-08T00:59:23.863Z
---
Senior engineering review of PR #58 (jlevy/kpress comment 5577424528, head e82ab0c), verdict approve with seven findings, none blocking. R1/R2: the fix cannot be seen to fail (the paint test is green when the wait times out; the 3s deadline has no test). R3: the wait more than doubles the font payload of a plain math page and the number is unrecorded. R4/R5: kpress-design.md claims more than the code delivers and its math-assets note describes pre-fix behaviour. R6/R7: kpressMathFaceWait's stability and the by-name KaTeX path's host assumption are implicit. Children carry one finding each.
