---
type: is
id: is-01m1z8ex4e2dy5d2jmqkpytaxx
title: "PR #58 review R6: kpressMathFaceWait is documented but not pinned"
kind: bug
status: open
priority: 3
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1z8drasjh3hct7hke23s0kj
created_at: 2026-09-08T01:00:01.547Z
updated_at: 2026-09-08T01:00:01.547Z
---
docs/kpress-design.md L1280-1285 documents globalThis.kpressMathFaceWait field by field in a doc hosts read, and tests/test_playwright_math_text_face.py asserts its shape, but it is not in kpress.contract and nothing says it is unstable, so a reader cannot tell a debug hook from a seam. Fix: one clause saying it is a debug hook outside the pinned public surface whose shape may change, or add it to contract.py.
