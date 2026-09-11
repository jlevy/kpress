---
type: is
id: is-01m1zs31any75ehnn70qb2rvh7
title: Ship the sans math half only to pages that have sans math
kind: task
status: open
priority: 3
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T05:50:38.320Z
updated_at: 2026-09-08T05:50:38.320Z
---
From the senior review of #57 (K57-R11). The sans half ships on every page with math,
whether or not that page has math in a sans role: +8,271 bytes gzip, of which almost all is
the metrics table (comment-stripped, the CSS delta is +488 gzip). It is a first-visit cost
only; a warm multi-page cache pays nothing.

Three things block making it lazy, and all three are the same shape -- the sans half has no
identity of its own anywhere in the pipeline:

1. the metrics asset is one file with `sans` nested inside it;
2. the renderer carries only `has_math` (format/markdown.py -> format/model.py -> render.py),
   so nothing downstream knows a page has math in a sans role;
3. `applyTextMetrics` in katex-init.js hard-requires both sets and turns the whole face off
   if the sans one is missing, which is correct today and would have to become conditional.

The fix is `has_sans_math` beside `has_math`, and the sans table and @font-face block split
into their own files behind it. Worth doing when a page budget starts to matter; not before.
