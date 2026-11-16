---
type: is
id: is-01m21mh5q1jkq1xtmtn1na0pcn
title: Inline code sits in too much padding for its background chip
kind: task
status: closed
priority: 2
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T23:09:27.647Z
updated_at: 2026-11-16T23:17:51.557Z
closed_at: 2026-11-16T23:17:51.556Z
close_reason: "Fixed by kpress#72 (af8f3f1): inline code padding is now 0.1em 0.25em."
resolution: null
duplicate_of: null
---
Owner (2026-09-08): the background behind an inline code span carries slightly more padding than it should, so a code word inside a sentence reads as a heavier block than the text around it. Reduce it, keeping the chip legible and keeping the line's rhythm: the padding should not push the background above the line's ascender or below its descender, and a code span at the start or end of a line should not look inset from the measure. Take the horizontal and vertical padding separately, since the vertical is what disturbs the line and the horizontal is what separates the word. Check inline code inside prose, inside a heading, inside a caption and inside a table cell, at the default size and at the small mono rung the tables use, on screen and in print, in both themes; the print stylesheet may set its own. Measure the chip's box against the line box before and after and put the numbers in the commit, and update the goldens.
