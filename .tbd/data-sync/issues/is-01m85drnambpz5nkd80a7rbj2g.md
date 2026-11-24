---
type: is
id: is-01m85drnambpz5nkd80a7rbj2g
title: "PR #82 I3: sanitized mode turns any raw input into a box"
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
created_at: 2026-11-24T00:02:21.649Z
updated_at: 2026-11-24T02:10:23.534Z
started_at: 2026-11-24T00:02:40.195Z
closed_at: 2026-11-24T02:10:23.530Z
close_reason: "Fixed in ccf32f5 on PR #82: a raw <input> whose type is not checkbox (ASCII case-insensitive, trimmed) is removed in sanitized mode and reported as a removed tag. CI 45306732433 green on 0c0f857."
resolution: null
duplicate_of: null
---
In sanitized mode every raw <input>, type=text or password included, becomes the disabled checkbox. Drop any raw input whose type is not checkbox (ASCII case-insensitive, after trimming), missing type included; keep a raw checkbox as the canonical disabled box. Keep diagnostics accurate, byte stability, and the S1-S9 tests' intent; release-note it.
