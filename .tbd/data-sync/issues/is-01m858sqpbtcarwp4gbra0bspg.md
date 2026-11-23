---
type: is
id: is-01m858sqpbtcarwp4gbra0bspg
title: "PR #82 S6: an unexplained <input> rewrite is unreported beside another diagnostic"
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
created_at: 2026-11-23T22:35:33.962Z
updated_at: 2026-11-23T23:42:49.959Z
started_at: 2026-11-23T22:36:07.432Z
closed_at: 2026-11-23T23:42:49.956Z
close_reason: "fixed in 69a8b7f: the catch-all compares input events whenever no input diagnostic explains an input change, beside other diagnostics; test test_an_unexplained_input_change_is_reported_beside_other_diagnostics"
resolution: null
duplicate_of: null
---
Security review of PR #82, nit. The catch-all html_sanitized diagnostic (sanitize.py:481-485) fires only when there are no other diagnostics, so an input change the audit cannot explain goes unreported beside an unrelated diagnostic.
