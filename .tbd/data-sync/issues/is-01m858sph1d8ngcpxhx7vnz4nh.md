---
type: is
id: is-01m858sph1d8ngcpxhx7vnz4nh
title: "PR #82 S3: sanitized mode passes <link rel=stylesheet>"
kind: bug
status: closed
priority: 1
version: 3
spec_path: TODO.md
delegate: claude-code@spud10.local
labels: []
dependencies: []
parent_id: is-01m8577cwgvk6zxwrhatkd8tea
hold: null
hold_until: null
created_at: 2026-11-23T22:35:32.768Z
updated_at: 2026-11-23T23:42:43.708Z
started_at: 2026-11-23T22:36:05.219Z
closed_at: 2026-11-23T23:42:43.706Z
close_reason: "fixed in 08a2258: link removed from _ALLOWED_TAGS; KPress writes link only in the page head; verified in headless Chromium 148 (stylesheet fetched and applied before, no request after); tests test_a_link_element_never_loads_a_resource, test_a_link_element_cannot_be_admitted_as_an_extra_tag"
resolution: null
duplicate_of: null
---
Security review of PR #82, should-fix, predates the PR. link is in _ALLOWED_TAGS (sanitize.py:34) with href and rel global, so <link rel="stylesheet" href="https://evil.test/x.css"> passes unchanged, though FORBIDDEN_EXTRA_TAGS (sanitize.py:197) lists link and the threat model says resource loading and style injection are stripped.
