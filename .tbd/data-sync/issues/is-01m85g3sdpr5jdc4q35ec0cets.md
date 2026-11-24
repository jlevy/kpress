---
type: is
id: is-01m85g3sdpr5jdc4q35ec0cets
title: "PR #82 N4: a marker followed only by a line ending draws a box; GitHub shows text"
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
created_at: 2026-11-24T00:43:23.437Z
updated_at: 2026-11-24T00:43:53.400Z
started_at: 2026-11-24T00:43:53.397Z
---
Re-review of 5c60a81 (Low): '- [ ]\n  next line' draws a box; github.com (gfm mode) shows [ ] as text. Match GitHub, test it, and make the design doc's 'as on GitHub' claim accurate.
