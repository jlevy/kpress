---
type: is
id: is-01m1z8ehh5ts1p412r0nnw7qbh
title: "PR #58 review R1: the paint test passes when the wait times out"
kind: bug
status: open
priority: 2
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1z8drasjh3hct7hke23s0kj
created_at: 2026-09-08T00:59:49.665Z
updated_at: 2026-09-08T00:59:49.665Z
---
tests/test_playwright_math_text_face.py test_math_paints_once_in_its_final_faces: all three assertions are relative to firstKatex, and nothing bounds firstKatex or looks at whether the wait settled. Reviewer reproduced: with KaTeX_Main italic 700 hanging, firstKatex goes 160.8ms -> 3125.9ms and every leg still passes, wait record {loaded: 9, pending: 1}. The branch already hit this shape once (KaTeX_Main normal 700 never loaded on the Linux runner, commit 65d2539). Fix: assert no pending entry and firstKatex < 2000 in both modes.
