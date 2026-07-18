---
type: is
id: is-01kxvha08xjxc6ffwxkmsnets1
title: "PR #22 review R1: refresh stale print publish goldens"
kind: bug
status: closed
priority: 1
version: 3
labels: []
dependencies: []
parent_id: is-01kxvh9mjg6gbk75kkcq4psdd7
created_at: 2026-07-18T21:14:53.084Z
updated_at: 2026-07-18T21:22:00.267Z
closed_at: 2026-07-18T21:22:00.266Z
close_reason: Fixed in 0e637b9; full local gates and all required GitHub CI checks passed.
---
Formal review R1. CI fails in tests/test_golden_publish.py and tests/test_golden_readable_vs_hashed.py because merged print.css changes are absent from accepted output trees.
