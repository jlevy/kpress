---
type: is
id: is-01m858sqpbtcarwp4gbra0bspg
title: "PR #82 S6: an unexplained <input> rewrite is unreported beside another diagnostic"
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
created_at: 2026-11-23T22:35:33.962Z
updated_at: 2026-11-23T22:36:07.433Z
started_at: 2026-11-23T22:36:07.432Z
---
Security review of PR #82, nit. The catch-all html_sanitized diagnostic (sanitize.py:481-485) fires only when there are no other diagnostics, so an input change the audit cannot explain goes unreported beside an unrelated diagnostic.
