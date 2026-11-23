---
type: is
id: is-01m858t6e4s0jw74jfk1dxag0n
title: "PR #82 C1: a task marker defined as a link loses its link"
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
created_at: 2026-11-23T22:35:49.059Z
updated_at: 2026-11-23T23:42:55.776Z
started_at: 2026-11-23T22:36:11.366Z
closed_at: 2026-11-23T23:42:55.775Z
close_reason: "fixed in af8c914: link-defined marker stays the link with no box (github.com); test test_task_marker_that_a_document_defines_as_a_link_is_the_link; notes in b12f720. Note: main drew the box and kept the link"
resolution: null
duplicate_of: null
---
Correctness review of PR #82 (head 92ef5ad), should-fix. markdown.py:409-420 turns '- [x] Done' with '[x]: https://example.com' into a box and drops the link; comment at 410-411 says GitHub reads the marker before links. github.com does not: the comment renderer (gh api -X POST /markdown -f mode=gfm) and the file view render the link with no box. Decision: match github.com and main, leave a link-defined marker as the link. Fix test (tests/test_reader_markdown_parity.py:462-468), comment, design doc, release notes (docs/releases/0.3.10.md:23-24), and PR body.
