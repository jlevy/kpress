---
type: is
id: is-01m1yffq9s7xz2p0temphqz1zq
title: math_text_font option, attribute stamping, asset wiring, init hook
kind: task
status: closed
priority: 2
version: 3
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies:
  - type: blocks
    target: is-01m1yffqm4ktp7gvk5jrag9j6a
parent_id: is-01m1yfesy4xsgdvn6wttcwmfhj
created_at: 2026-09-07T17:43:33.944Z
updated_at: 2026-09-07T19:10:32.520Z
closed_at: 2026-09-07T19:10:32.520Z
close_reason: "Landed in jlevy/kpress#53 (commits 06301dd, 1d82940, 98594f2, 6cd820e): metrics generator and asset, KPress Math Text composite and init hook, option and contract, tests, goldens and docs."
resolution: null
duplicate_of: null
---
RenderOptions.math_text_font (prose|katex, default prose), document options, page.html.jinja data-kpress-math-text, public contract; add katex-text-metrics.js to KATEX_JS_ASSETS before katex-init.js; katex-init.js applies katex.__setFontMetrics per face before renderMathInElement when the attribute is prose and the font mode is not system.
