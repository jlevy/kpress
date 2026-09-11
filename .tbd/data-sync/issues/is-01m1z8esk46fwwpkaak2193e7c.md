---
type: is
id: is-01m1z8esk46fwwpkaak2193e7c
title: "PR #58 review R3: the wait's transfer cost is unrecorded"
kind: bug
status: closed
priority: 2
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1z8drasjh3hct7hke23s0kj
created_at: 2026-09-08T00:59:57.918Z
updated_at: 2026-09-08T01:39:28.686Z
closed_at: 2026-09-08T01:39:28.685Z
close_reason: "Fixed on squares/math-paints-once (26d6822, 9b1778a); disposition posted on PR #58."
resolution: null
duplicate_of: null
---
The wait loads all six KaTeX_Main/KaTeX_Math faces and all four composite slots whatever the document draws. Measured by the reviewer on a \\sum...\\int fixture: 5 requests / 117,432 B before, 11 / 252,828 B at head, +6 requests and +135,396 B (+115%); +4 / +76,692 B in math_text_font: katex. KaTeX_Main-Italic (17,288 B) and KaTeX_Main-BoldItalic (17,080 B) are not cache-shared with the composite. Over loopback the render cost is only +11.9ms median. Fix options: (a) await only the two regular faces, (b) keep the set and record the payload change in kpress-design.md, (c) leave it to kpr-hhdc.
