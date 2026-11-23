---
type: is
id: is-01m858srcgvc03w06hsq110pgt
title: "PR #82 S7: raw <input> keeps any class and any checked value"
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
created_at: 2026-11-23T22:35:34.670Z
updated_at: 2026-11-23T23:42:51.508Z
started_at: 2026-11-23T22:36:07.988Z
closed_at: 2026-11-23T23:42:51.505Z
close_reason: "fixed in 69a8b7f: class kept only as task-list-item-checkbox alone, checked normalized to checked=checked; tests in test_any_other_input_becomes_a_disabled_checkbox and test_a_box_written_in_any_order_or_case_is_byte_for_byte_kpress_box"
resolution: null
duplicate_of: null
---
Security review of PR #82, nit. A raw input keeps any class (e.g. kpress-video-backdrop kpress-visible), so a forged input can take KPress layout classes; checked keeps its value. Restrict class to exactly task-list-item-checkbox and normalize checked so the output is byte-identical to KPress's own box.
