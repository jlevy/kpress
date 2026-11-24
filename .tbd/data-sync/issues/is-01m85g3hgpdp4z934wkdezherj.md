---
type: is
id: is-01m85g3hgpdp4z934wkdezherj
title: "PR #82 N1: a button removed inside SVG is reported as edited, which hides the catch-all"
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
created_at: 2026-11-24T00:43:15.344Z
updated_at: 2026-11-24T02:10:29.017Z
started_at: 2026-11-24T00:43:40.497Z
closed_at: 2026-11-24T02:10:29.011Z
close_reason: "Fixed in 507a22f on PR #82: a button that does not survive parsing is reported as removed, and predicted survivors are confirmed against nh3's output, else the catch-all. CI 45306732433 green on 0c0f857."
resolution: null
duplicate_of: null
---
Re-review of 5c60a81 (Low, regression vs main): <svg><button>go</button></svg> sanitizes to <svg></svg> with only "Set attribute 'type' to 'button' on <button>."; the new button diagnostic suppresses the catch-all. Report the removal.
