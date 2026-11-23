---
type: is
id: is-01m858tamaadhdnxc21301psxf
title: "PR #82 C5: whitespace other than a space inside the brackets is not a task marker"
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
created_at: 2026-11-23T22:35:53.350Z
updated_at: 2026-11-23T22:36:13.382Z
started_at: 2026-11-23T22:36:13.382Z
---
Correctness review of PR #82, nit, not a regression. markdown.py:92-94 accepts only a space between the brackets; the GFM rule is a whitespace character or the letter x, and GitHub boxes '- [\t] With a tab'. Follow the GFM definition of whitespace character; add tests and a release-note line.
