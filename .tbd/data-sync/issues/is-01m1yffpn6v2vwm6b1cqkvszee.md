---
type: is
id: is-01m1yffpn6v2vwm6b1cqkvszee
title: Metrics generator devtool and katex-text-metrics.js asset
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
created_at: 2026-09-07T17:43:33.285Z
updated_at: 2026-09-07T19:10:32.505Z
closed_at: 2026-09-07T19:10:32.503Z
close_reason: "Landed in jlevy/kpress#53 (commits 06301dd, 1d82940, 98594f2, 6cd820e): metrics generator and asset, KPress Math Text composite and init hook, option and contract, tests, goldens and docs."
resolution: null
duplicate_of: null
---
devtools/katex_text_metrics.py: read katex.min.js base tables and the reading-face woff2 files, rewrite the swapped code points (digits and Latin letters) with depth, height, italic overhang and width, keep skew; write static/katex/katex-text-metrics.js defining globalThis.kpressKatexTextMetrics; --check for freshness wired into make lint; fontTools in the dev group (pinned past the cool-off).
