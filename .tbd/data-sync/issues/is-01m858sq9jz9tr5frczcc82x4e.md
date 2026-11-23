---
type: is
id: is-01m858sq9jz9tr5frczcc82x4e
title: "PR #82 S5: audit reports attribute edits for an <input> that did not survive"
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
created_at: 2026-11-23T22:35:33.553Z
updated_at: 2026-11-23T23:42:48.018Z
started_at: 2026-11-23T22:36:06.829Z
closed_at: 2026-11-23T23:42:48.017Z
close_reason: fixed in 69a8b7f (survival model checked against the output's input count; noscript read as text), 3b0c9fc (linear-time context tracking) and 5c60a81 (an input inside an attribute value is not counted); tests test_an_input_that_does_not_survive_is_reported_as_removed, test_the_audit_tracks_only_the_elements_that_decide_an_input
resolution: null
duplicate_of: null
---
Security review of PR #82, nit. sanitize.py:378-396: <svg><input type="text" form="x"></svg> sanitizes to <svg></svg> but the audit reports Removed attribute 'form' and Set attribute ... on <input>; <noscript><input ...></noscript> becomes literal text with the same attribute diagnostics. Report the removal (or nothing).
