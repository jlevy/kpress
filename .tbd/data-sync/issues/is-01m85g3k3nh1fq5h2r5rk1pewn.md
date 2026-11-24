---
type: is
id: is-01m85g3k3nh1fq5h2r5rk1pewn
title: "PR #82 N2: two input survival mispredictions cancel in the count check"
kind: bug
status: closed
priority: 2
version: 3
spec_path: TODO.md
delegate: claude-code@spud10.local
labels: []
dependencies: []
parent_id: is-01m8577cwgvk6zxwrhatkd8tea
hold: null
hold_until: null
created_at: 2026-11-24T00:43:16.974Z
updated_at: 2026-11-24T02:10:27.988Z
started_at: 2026-11-24T00:43:45.100Z
closed_at: 2026-11-24T02:10:27.985Z
close_reason: "Fixed in f47f5a6 on PR #82: the audit predicts each kept input's form and confirms the survivors against nh3's output in order and form, and follows html5ever out of foreign content. CI 45306732433 green on 0c0f857."
resolution: null
duplicate_of: null
---
Re-review of 5c60a81 (Low): <svg><mi><input ...></mi></svg><svg><p><input ...></p></svg> reports the first input edited and the second removed, the reverse of what happened, because the count check sums predictions. Make it robust (per position, or fall back to the catch-all).
