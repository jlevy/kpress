---
type: is
id: is-01m85g3whxgnjnze3dzz2ez4gq
title: "PR #82 N5: correct the 0.3.10 release notes"
kind: task
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
created_at: 2026-11-24T00:43:26.642Z
updated_at: 2026-11-24T00:43:57.904Z
started_at: 2026-11-24T00:43:57.889Z
---
Re-review of 5c60a81 (Low): 'only name and value were stripped' is wrong (main also stripped placeholder, autofocus, list, pattern, on*, formaction, and kept type, form, src, id); a plain footnote also changes NBSP to &nbsp; and &#x0003C; to &lt; in MathML; add that every raw <button> lacking type=button now emits an html_sanitized_attribute warning.
