---
type: is
id: is-01m85g3sdpr5jdc4q35ec0cets
title: "PR #82 N4: a marker followed only by a line ending draws a box; GitHub shows text"
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
created_at: 2026-11-24T00:43:23.437Z
updated_at: 2026-11-24T02:10:31.198Z
started_at: 2026-11-24T00:43:53.397Z
closed_at: 2026-11-24T02:10:31.197Z
close_reason: "Fixed in e7017b9 on PR #82: a marker followed only by spaces, tabs and a line ending is text, as GitHub's gfm API renders it. CI 45306732433 green on 0c0f857."
resolution: null
duplicate_of: null
---
Re-review of 5c60a81 (Low): '- [ ]\n  next line' draws a box; github.com (gfm mode) shows [ ] as text. Match GitHub, test it, and make the design doc's 'as on GitHub' claim accurate.
