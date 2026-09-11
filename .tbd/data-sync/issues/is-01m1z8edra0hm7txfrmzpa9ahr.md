---
type: is
id: is-01m1z8edra0hm7txfrmzpa9ahr
title: "Paint-once wait: the ceiling must not fall below the block period, and block hides whole runs"
kind: task
status: closed
priority: 2
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T00:59:45.786Z
updated_at: 2026-09-08T09:44:31.352Z
closed_at: 2026-09-08T09:44:31.351Z
close_reason: "Superseded by merged PR #59 (a265d553) and completed by #60 (7b20ae702acf37020e6132265c8faa0ba74e4465). Every supported render remains hidden until its actual glyph faces are ready; required-face errors/timeouts retain native MathML or reject for a host fallback, and absent composites use matching stock metrics. Visibility therefore no longer depends on releasing a formula after a guessed CSS block period. Delayed native/construct, failure, no-JS, and host regressions run in strict Chromium CI; the bounded wait remains tested."
resolution: null
duplicate_of: null
---
From the PR #58 review's probe (addendum comment on the PR, 2026-09-08). FACE_WAIT_MS (3000 ms) equals Chrome's font-display: block period; the render lands visible only because fonts.load() starts the block clock before startMath() registers its timer. A ceiling of 1200 ms rendered inside the block period and lost 90 to 96 percent of a formula's ink. Make the invariant explicit (comment and a test that the ceiling is at least the block period, or derive the wait from the block period), and reconsider block on the composite: during the block period Chrome blanks the whole run in the family, including the parentheses and operators no composite face claims (0/27632 ink against 3412/27632 in KaTeX_Main alone), so any path where the wait does not run shows a bare fraction bar for up to 3 s. Also: the metrics-failure opt-out stamp is delayed up to 3 s behind the wait; the PAINTING ONCE comment's data-URI sentence describes a mode kpress cannot emit (only a host that inlines assets has data-URI faces). If the address round for #58 takes these, close this bead with the commit.
