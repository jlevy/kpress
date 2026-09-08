---
type: is
id: is-01m1z8er5tvmyczyg08b1kfd7n
title: "PR #58 review R2: the 3-second deadline has no test"
kind: bug
status: closed
priority: 2
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1z8drasjh3hct7hke23s0kj
created_at: 2026-09-08T00:59:56.468Z
updated_at: 2026-09-08T01:39:26.361Z
closed_at: 2026-09-08T01:39:26.350Z
close_reason: "Fixed on squares/math-paints-once (26d6822, 9b1778a); disposition posted on PR #58."
resolution: null
duplicate_of: null
---
src/kpress/format/static/katex/katex-init.js startMath: Promise.race([Promise.all(loads), deadline]) is the safety valve that stops a hanging font from meaning no mathematics, and nothing covers it. tests/js/katex-init.test.js settles every load in every case and never produces the pending outcome. Fix: one vitest case with vi.useFakeTimers(), every load left pending, advanceTimersByTimeAsync(3000), assert renderMathInElement called once and every record entry still pending.
