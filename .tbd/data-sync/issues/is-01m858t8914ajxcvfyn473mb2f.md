---
type: is
id: is-01m858t8914ajxcvfyn473mb2f
title: "PR #82 C4: box token renders a live text field without KPress's rule"
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
created_at: 2026-11-23T22:35:50.939Z
updated_at: 2026-11-23T22:36:12.653Z
started_at: 2026-11-23T22:36:12.641Z
---
Correctness review of PR #82, nit. The kpress_task_checkbox token has tag input and no attrs, so the stock RendererHTML renders a bare <input>, a live text field. Decision: put class, checked (only when ticked), disabled, type on the token so renderToken yields the same bytes as KPress's box, and drop the custom rule if unnecessary; keep the type and meta['checked'].
