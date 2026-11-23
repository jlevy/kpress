---
type: is
id: is-01m858tamaadhdnxc21301psxf
title: "PR #82 C5: whitespace other than a space inside the brackets is not a task marker"
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
created_at: 2026-11-23T22:35:53.350Z
updated_at: 2026-11-23T23:43:02.630Z
started_at: 2026-11-23T22:36:13.382Z
closed_at: 2026-11-23T23:43:02.627Z
close_reason: "fixed in af8c914: any GFM whitespace character between the brackets is an open box, checked from x/X; test test_any_whitespace_character_inside_the_brackets_is_an_open_box; notes in b12f720"
resolution: null
duplicate_of: null
---
Correctness review of PR #82, nit, not a regression. markdown.py:92-94 accepts only a space between the brackets; the GFM rule is a whitespace character or the letter x, and GitHub boxes '- [\t] With a tab'. Follow the GFM definition of whitespace character; add tests and a release-note line.
