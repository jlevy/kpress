---
type: is
id: is-01m1z743jtmn911ekdsga2pevj
title: "After sans math and paint-once both land: the wait covers KPress Math Text Sans and its faces block"
kind: task
status: closed
priority: 2
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T00:36:39.113Z
updated_at: 2026-09-08T06:37:13.466Z
closed_at: 2026-09-08T06:37:13.466Z
close_reason: "Done on kpress#57 before it merged (05ce8fb): the wait covers KPress Math Text Sans and its faces block"
resolution: null
duplicate_of: null
---
Found by the merge of main into squares/sans-math (fb9df70) with a read-only trial merge of #58: the two branches merge cleanly in katex-init.js but disagree semantically. (1) #58's TEXT_FACE_FONTS waits only on KPress Math Text at 400 and 700; the sans composite KPress Math Text Sans pins 400 and 650 and is not in the wait, so caption, footnote and table mathematics would still paint in the fallback and repaint. Add its four shorthands (normal and italic at 400 and 650), keyed on the same mode detection katex-init uses for the table set, and extend the Playwright paint-once test to a sans context. (2) #58 sets font-display: block on the eight serif composite faces; the eight sans screen faces still say swap, and #58's assertion covers only the serif family; flip them and assert both families. Also resolve the one textual conflict, tests/js/katex-init.test.js, where both sides append cases. Do this on whichever of the two branches lands second, before it merges.
