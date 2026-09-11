---
type: is
id: is-01m1zsamjqhrkmtdsp9h2s16va
title: A hero heading is sans words with serif mathematics
kind: task
status: open
priority: 3
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T05:54:47.499Z
updated_at: 2026-09-08T05:54:47.499Z
---
Found while fixing K57-R6 on #57, and outside it. `.kpress .hero h1` in components.css sets
the sans family directly, but `.hero` is not in `SANS_CONTEXT` in katex-init.js, so a formula
in a hero heading is drawn from the serif composite and laid out from the serif tables under
sans words: the same disagreement K57-R6 fixed for the five semantic containers, pointing the
other way.

Not obviously a one-word fix, which is why it is a bead rather than a line. Headings are left
out of `SANS_CONTEXT` deliberately: a heading sits a weight step away from the words around
it, and a metric table built at 400 describes neither `h3`'s 550 nor `h4`'s 540. A hero `h1`
is 380, which is nearer 400 than any of them, so the argument that keeps other headings out is
weaker here -- but it is the same argument, and whether a hero heading should carry sans
mathematics at 380 against a 400 table is a call about how visible the residual is, not a bug
report. Measure it before changing it.
