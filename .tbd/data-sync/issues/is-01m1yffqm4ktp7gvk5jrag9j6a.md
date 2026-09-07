---
type: is
id: is-01m1yffqm4ktp7gvk5jrag9j6a
title: Tests, goldens and docs for the math text face
kind: task
status: closed
priority: 2
version: 4
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies:
  - type: blocks
    target: is-01m1yffqyysqevrgj22mvy6keg
  - type: blocks
    target: is-01m1yffr98j2cdpmvtq8thqp1q
parent_id: is-01m1yfesy4xsgdvn6wttcwmfhj
created_at: 2026-09-07T17:43:34.275Z
updated_at: 2026-09-07T19:10:32.526Z
closed_at: 2026-09-07T19:10:32.526Z
close_reason: "Landed in jlevy/kpress#53 (commits 06301dd, 1d82940, 98594f2, 6cd820e): metrics generator and asset, KPress Math Text composite and init hook, option and contract, tests, goldens and docs."
resolution: null
duplicate_of: null
---
Unit tests for the option and CSS contract; metrics spot checks; vitest for the init hook; Playwright digit-advance (0.533 vs 0.5) and numerator-in-box checks; golden refresh for stylesheet sizes and hashes; kpress-design.md Theme and Fonts subsection; host integration doc hooks (faces and metrics contract for another reading face, and the note for hosts that inline assets).
