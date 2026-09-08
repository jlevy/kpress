---
type: is
id: is-01m1zsckx8fma5tbwjf3ksyedj
title: Decide whether the Greek scale factors should be derived below a one-unit rounding gap
kind: task
status: open
priority: 3
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T05:55:52.346Z
updated_at: 2026-09-08T05:55:52.346Z
---
Raised while fixing K57-R8 on #57. `OS2_INK_TOLERANCE` in devtools/katex_text_metrics.py is
now 0.003, which is what the review prescribed and what the defect it described requires: it
separates Source Sans's four- and seven-unit `sCapHeight` lie (the declaration is a
weight-invariant 660 while the drawn `H` falls 656 at 400 and 653 at 650) from real agreement.
At 0.003 exactly two shipped factors move, both in the sans composite: Main-Regular 96.6% ->
96%, Main-Bold 96.2% -> 95.2%. The serif set is byte-identical.

The review also predicted sans Math-Italic 110.2% -> 110.0% and serif Math-Italic 115.0% ->
114.7%. Re-measurement says those need a tolerance BELOW 0.001, and the thing that trips there
is different in kind: `KaTeX_Math-Italic` declares `sxHeight` 441 against a 442-unit drawn `x`,
a one-unit disagreement at 1000 upem. That is font-build rounding, not a font declaring a
height it never draws.

So the open question is whether the generator should measure ink unconditionally rather than
prefer a declaration that agrees to within a unit. Arguments both ways: measuring ink always is
simpler and has no threshold to justify; preferring the declaration is more stable against a
rebuilt font whose outlines shift by a unit. Cost of deciding "always ink": it moves the SERIF
composite's shipped Math-Italic table, which has been out in released pages, so it is a change
to shipped behaviour rather than to something new. That is why it was kept out of #57.
