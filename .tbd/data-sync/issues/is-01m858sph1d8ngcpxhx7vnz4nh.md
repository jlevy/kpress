---
type: is
id: is-01m858sph1d8ngcpxhx7vnz4nh
title: "PR #82 S3: sanitized mode passes <link rel=stylesheet>"
kind: bug
status: in_progress
priority: 1
version: 2
spec_path: TODO.md
delegate: claude-code@spud10.local
labels: []
dependencies: []
parent_id: is-01m8577cwgvk6zxwrhatkd8tea
hold: null
hold_until: null
created_at: 2026-11-23T22:35:32.768Z
updated_at: 2026-11-23T22:36:05.229Z
started_at: 2026-11-23T22:36:05.219Z
---
Security review of PR #82, should-fix, predates the PR. link is in _ALLOWED_TAGS (sanitize.py:34) with href and rel global, so <link rel="stylesheet" href="https://evil.test/x.css"> passes unchanged, though FORBIDDEN_EXTRA_TAGS (sanitize.py:197) lists link and the threat model says resource loading and style injection are stripped.
