---
type: is
id: is-01m858sq9jz9tr5frczcc82x4e
title: "PR #82 S5: audit reports attribute edits for an <input> that did not survive"
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
created_at: 2026-11-23T22:35:33.553Z
updated_at: 2026-11-23T22:36:06.830Z
started_at: 2026-11-23T22:36:06.829Z
---
Security review of PR #82, nit. sanitize.py:378-396: <svg><input type="text" form="x"></svg> sanitizes to <svg></svg> but the audit reports Removed attribute 'form' and Set attribute ... on <input>; <noscript><input ...></noscript> becomes literal text with the same attribute diagnostics. Report the removal (or nothing).
