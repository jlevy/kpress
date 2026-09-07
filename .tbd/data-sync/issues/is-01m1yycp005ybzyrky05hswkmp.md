---
type: is
id: is-01m1yycp005ybzyrky05hswkmp
title: "K53-R5: direct wrapper font preference has inconsistent guards"
kind: bug
status: closed
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01m1yyca1dg146m92xn73ft93r
created_at: 2026-09-07T22:04:02.943Z
updated_at: 2026-09-07T22:32:06.677Z
closed_at: 2026-09-07T22:32:06.672Z
close_reason: "Fixed on squares/page-fixes; see PR #53 commits 92eb56c / a9b43b1 / 3a3a87f"
resolution: null
duplicate_of: null
---
katex-text-face.css excluded [data-kpress-font-set=system] * but not the bare element, while katex-init.js used closest(). PR #53.
