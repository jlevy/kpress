---
type: is
id: is-01m1ymqzc9eyan1n7yg2gzewad
title: Ship the composite's faces as subsets to cut the inlined page cost
kind: task
status: open
priority: 3
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
created_at: 2026-09-07T19:15:27.229Z
updated_at: 2026-09-07T19:15:27.229Z
---
A page that inlines every asset carries a second copy of each face KPress Math Text names (three PT Serif copies and three scaled Greek copies of KaTeX faces, about 216 KB of base64; the squares explainer grew from 1,177 KB to 1,441 KB). The composite only needs the 62 Latin glyphs of each PT Serif face and the Greek range of each KaTeX face; devtools/katex_text_metrics.py already opens the fonts with fontTools, so it can write subset woff2 files for the composite and the stylesheet can point at them. Hosted modes pay one small extra download instead of a cache hit; measure both before choosing.
