---
type: is
id: is-01m858ssk38zdvn4n7zt1kczrx
title: "PR #82 S9: missing sanitized-input tests"
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
created_at: 2026-11-23T22:35:35.904Z
updated_at: 2026-11-23T22:36:10.103Z
started_at: 2026-11-23T22:36:10.100Z
---
Security review of PR #82, tests. Cover: inputs lacking both type and disabled; duplicate attributes (first wins); uppercase names and type variants; name, formaction, on*, style, autofocus on an input; extra_tags/extra_attributes cannot widen an input; a raw input through parse_markdown(..., trust_mode='sanitized').
