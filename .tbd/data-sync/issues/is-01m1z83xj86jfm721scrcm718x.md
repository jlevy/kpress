---
type: is
id: is-01m1z83xj86jfm721scrcm718x
title: Lay out the document logically so RTL reads correctly beyond the marker
kind: task
status: open
priority: 2
version: 1
spec_path: docs/math-text-face.plan.md
labels: []
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T00:54:01.530Z
updated_at: 2026-09-08T00:54:01.530Z
---
PR #56 rewrote the three drawn-marker rules to `inset-inline-start`, so a bulleted marker now sits on the correct side under `dir="rtl"` and the 0.064em ink nudge points toward the text in both directions. `tests/test_playwright_list_marker.py::test_list_markers_follow_the_text_direction` pins that.

The rest of the document still lays out physically, so an RTL document is only half right. The list indents the marker hangs off are the clearest case: `.kpress-prose ul`, `.kpress .concepts ul` and `.kpress-prose ol` in `document.css` set `margin-left: 1.8rem` and `padding-left: 0`, so an RTL list indents from the wrong edge while its marker correctly sits on the right. `.kpress blockquote` sets an asymmetric physical `margin`, and `components.css` carries about ten further physical `margin-left`/`padding-left`/`-right` declarations.

Scope: audit every physical inline-direction property in the document stylesheets, convert the ones that belong to the reading direction to logical equivalents (`margin-inline-start`, `padding-inline-start`, `inset-inline-*`), and leave the ones that are genuinely physical alone with a comment saying so. Print has its own copies in `print.css`, so the audit covers that file too.

Verification needs an RTL case in the real-browser suite beyond the marker one: a rendered document under `dir="rtl"` whose list indent, blockquote rule and marker all sit on the trailing edge. Nothing else in the suite renders RTL today, so this is new coverage rather than an extension.

Raised as K56-R10 in the senior review of PR #56 (comment 5577269395). The marker half is fixed on `squares/font-consistency`; this is the rest, which the reviewer noted is pre-existing.
