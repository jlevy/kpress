---
type: is
id: is-01m85g3hgpdp4z934wkdezherj
title: "PR #82 N1: a button removed inside SVG is reported as edited, which hides the catch-all"
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
created_at: 2026-11-24T00:43:15.344Z
updated_at: 2026-11-24T00:43:40.586Z
started_at: 2026-11-24T00:43:40.497Z
---
Re-review of 5c60a81 (Low, regression vs main): <svg><button>go</button></svg> sanitizes to <svg></svg> with only "Set attribute 'type' to 'button' on <button>."; the new button diagnostic suppresses the catch-all. Report the removal.
