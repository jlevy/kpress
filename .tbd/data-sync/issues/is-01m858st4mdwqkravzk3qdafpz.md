---
type: is
id: is-01m858st4mdwqkravzk3qdafpz
title: "PR #82 S10: footnote html is not sanitized; body_html trust undocumented"
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
created_at: 2026-11-23T22:35:36.467Z
updated_at: 2026-11-23T22:36:11.006Z
started_at: 2026-11-23T22:36:11.005Z
---
Security review of PR #82, informational, predates the PR. In sanitized mode DocumentTree.footnotes[i].html (markdown.py:1177-1178) is not sanitized: [^1]: <input type="text" name="q"> and <script>alert(1)</script> survives there while tree.html is clean. DocumentInput.body_html (render.py:245-246) is emitted as written; decide whether it is host-supplied trusted HTML and document it, or sanitize it.
