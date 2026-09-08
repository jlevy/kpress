---
type: is
id: is-01m1z8edra0hm7txfrmzpa9ahr
title: "Paint-once wait: the ceiling must not fall below the block period, and block hides whole runs"
kind: task
status: open
priority: 2
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T00:59:45.786Z
updated_at: 2026-09-08T00:59:45.786Z
---
From the PR #58 review's probe (addendum comment on the PR, 2026-09-08). FACE_WAIT_MS (3000 ms) equals Chrome's font-display: block period; the render lands visible only because fonts.load() starts the block clock before startMath() registers its timer. A ceiling of 1200 ms rendered inside the block period and lost 90 to 96 percent of a formula's ink. Make the invariant explicit (comment and a test that the ceiling is at least the block period, or derive the wait from the block period), and reconsider block on the composite: during the block period Chrome blanks the whole run in the family, including the parentheses and operators no composite face claims (0/27632 ink against 3412/27632 in KaTeX_Main alone), so any path where the wait does not run shows a bare fraction bar for up to 3 s. Also: the metrics-failure opt-out stamp is delayed up to 3 s behind the wait; the PAINTING ONCE comment's data-URI sentence describes a mode kpress cannot emit (only a host that inlines assets has data-URI faces). If the address round for #58 takes these, close this bead with the commit.
