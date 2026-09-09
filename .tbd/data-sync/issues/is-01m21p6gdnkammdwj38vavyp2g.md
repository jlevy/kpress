---
type: is
id: is-01m21p6gdnkammdwj38vavyp2g
title: Retune the mono size ratio from 0.87 to 0.82
kind: task
status: in_progress
priority: 2
version: 3
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T23:38:35.316Z
updated_at: 2026-09-08T23:52:10.919Z
---
`--kpress-font-size-mono` moves from 0.87 to 0.82 of `--kpress-font-size-base`, by the
owner's decision of 2026-09-08: at 0.87 the code read too large beside the prose.

The ratio is a judgement about how code should read beside prose, not a value the ink
forces, and the token comment and the design doc now say so. What the ink does fix is
the consequences, and those were re-derived and then measured in Chromium from the
shipped bytes:

- x-height parity between Planetaire Mono Text (0.560 em) and PT Serif (0.500 em) would
  want 0.500/0.560 = 0.893. At 0.82 code's x-height is 0.459 em, 91.8% of the prose
  x-height beside it -- deliberately below parity. 0.87 sat at 97.4%.
- 45 / (0.82 x 0.602) = 91.16, so 91 columns fit the 45em measure, against 85 at 0.87.
  Measured in Chromium: 91.159 columns against a 720px measure at a 16px root.
- Measured pixels at a 16px root: prose 16.00, code 13.12, x-heights 8.000 and 7.347
  (ratio 0.9184). At an 18px root: prose 18.00, code 14.76, x-heights 9.000 and 8.266.

The whole ramp follows, since small and tiny derive from the mono rung and the print
sheet re-roots the base at 11pt:

- mono-small is 0.738 of base: 11.81px at a 16px root, 13.28px at 18px, 8.12pt in print.
- mono-tiny is 0.697 of base: 11.15px at a 16px root, 12.55px at 18px, 7.67pt in print.
- Table code steps to mono-small: 0.863 of its own cell at mono, 0.777 at mono-small,
  equidistant either side of the ramp's 0.82. That equidistance holds at any ratio,
  since the cell's 0.95 is the midpoint of the 1.0 and 0.9 steps the two rungs carry.

One thing the retune surfaces and does not fix: the tooltip's code rule is 0.9em of the
tooltip's own `small` text, so 0.855 of the base and not on the mono ramp at all. That
sat just under 0.87 and now sits just over 0.82, so code inside a tooltip is marginally
larger relative to the base than the same span in prose. Holding the ramp there would
want 0.863em. Left alone as a separate judgement for the owner.
