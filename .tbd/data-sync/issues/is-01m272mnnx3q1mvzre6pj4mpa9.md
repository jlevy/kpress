---
type: is
id: is-01m272mnnx3q1mvzre6pj4mpa9
title: Make Planetaire request-cost browser assertion deterministic
kind: bug
status: open
priority: 2
version: 1
labels:
  - testing
  - browser-qa
  - typography
dependencies: []
created_at: 2026-09-11T01:52:14.521Z
updated_at: 2026-09-11T01:52:14.521Z
---
PR #72 CI run 34551969329 showed one of three identical Ubuntu jobs intermittently request the otherwise unused Planetaire 700-italic face in tests/test_playwright_mono_face.py; the other two jobs and ten consecutive local Chrome runs passed. Determine whether rapid screen/print media toggling causes a transient font request, preserve the actual used-face and loading-cost contract without weakening it, and make the focused browser measurement deterministic.
