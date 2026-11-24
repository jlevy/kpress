---
type: is
id: is-01m85g3k3nh1fq5h2r5rk1pewn
title: "PR #82 N2: two input survival mispredictions cancel in the count check"
kind: bug
status: in_progress
priority: 2
version: 2
spec_path: TODO.md
delegate: claude-code@spud10.local
labels: []
dependencies: []
parent_id: is-01m8577cwgvk6zxwrhatkd8tea
hold: null
hold_until: null
created_at: 2026-11-24T00:43:16.974Z
updated_at: 2026-11-24T00:43:45.110Z
started_at: 2026-11-24T00:43:45.100Z
---
Re-review of 5c60a81 (Low): <svg><mi><input ...></mi></svg><svg><p><input ...></p></svg> reports the first input edited and the second removed, the reverse of what happened, because the count check sums predictions. Make it robust (per position, or fall back to the catch-all).
