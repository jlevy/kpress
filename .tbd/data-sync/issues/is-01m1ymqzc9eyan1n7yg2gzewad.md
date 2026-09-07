---
type: is
id: is-01m1ymqzc9eyan1n7yg2gzewad
title: Ship the composite's faces as subsets to cut the inlined page cost
kind: task
status: open
priority: 2
version: 3
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-07T19:15:27.229Z
updated_at: 2026-09-07T22:31:25.906Z
---
A page that inlines every asset carries a second copy of each face KPress Math Text names: six composite faces, 216 KB of base64 on the squares explainer, every byte a duplicate of a PT Serif or KaTeX blob already inlined under its own family (measured 2026-09-07: 636 KB of fonts in 22 urls, 16 distinct blobs of 420 KB). The composite only needs the Latin letters and digits of each PT Serif face and the Greek range of each KaTeX face; devtools/katex_text_metrics.py already opens the fonts with fontTools, so a generator can write subset woff2 files for the composite slots (about 15 KB per PT Serif slot, a few KB per Greek slot) and katex-text-face.css points at them. Hosted modes pay one small extra download instead of a cache hit; measure both. Expected saving on the squares page: about 170 KB of the 216. With sans math (kpr-7f9z) the sans composite's slots need the same treatment.
