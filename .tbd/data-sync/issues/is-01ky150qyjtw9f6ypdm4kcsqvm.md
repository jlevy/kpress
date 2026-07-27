---
type: is
id: is-01ky150qyjtw9f6ypdm4kcsqvm
title: Make tooltip Playwright smokes execute in standard CI
kind: bug
status: open
priority: 2
version: 4
spec_path: docs/publishing.md
labels:
  - testing
  - playwright
  - ci
dependencies:
  - type: blocks
    target: is-01kyh1118c3xsmapj9d3bv74az
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
created_at: 2026-07-21T01:35:33.329Z
updated_at: 2026-07-27T05:34:14.313Z
---
All three exact-head CI matrix jobs report 559 passed, 2 skipped. The skipped tests are tests/test_playwright_tooltips.py because they launch only Playwright-managed Chromium, while CI installs no browser and the other browser tests fall back to system Chrome. Add the same Chrome fallback or explicitly install managed Chromium, and make unexpected skips fail the release gate. Both flows pass when run manually with system Chrome.
