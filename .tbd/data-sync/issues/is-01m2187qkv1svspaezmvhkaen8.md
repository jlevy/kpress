---
type: is
id: is-01m2187qkv1svspaezmvhkaen8
title: Diagnose PR62 mono browser test loading an unexpected bold-italic face
kind: bug
status: open
priority: 2
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T19:34:35.379Z
updated_at: 2026-09-08T19:34:35.379Z
---
KPress PR #62 merged as 9ea0877eccac08e64d483fc84460631322a9cdbc. Its post-merge CI run https://github.com/jlevy/kpress/actions/runs/34266495329 fails only the newly added test_code_is_set_in_the_shipped_mono_face_on_screen_and_in_print at tests/test_playwright_mono_face.py:184. The test expects regular, italic, and bold requests for its Python fixture, but the browser additionally requests planetaire-mono-text-latin-700-italic.woff2. The rendered custom-family and PostScript-name assertions passed; determine whether the extra request comes from a real reachable style or the browser/test lifecycle, then preserve a meaningful request-closure regression. Do not weaken the count without establishing why that fourth face is reached.

Scope: follow-up to the shipped kpr-v731/kpr-hqrr mono feature. The same browser job passed all 26 math-loading, 6 serif-math-face, 3 sans-math-face, and 6 PDF-font tests (42 passed, 1 failed overall). All Python matrix, lint and distribution jobs passed. The diff from 6e173fac962dba3f5413a0f531cbe9c3147c8947 contains PR62 mono changes and no math runtime changes. Squares remains intentionally pinned to 6e173fa, whose post-merge run https://github.com/jlevy/kpress/actions/runs/34266055524 is fully green. No source or pin changes were made for this finding.

Acceptance: classify the unexpected request with browser evidence, fix the implementation or assertion at the responsible boundary, and obtain a green strict browser job at the corrected head. This finding is independent of the ongoing Squares math startup/geometry repair.
