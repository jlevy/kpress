---
type: is
id: is-01kxvq1a5epzqjdt9re50n3gc1
title: "PR #24 review R2: stamping destroys non-plain host history.state"
kind: bug
status: closed
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01kxvq0x39trk4mw02bgc0k182
created_at: 2026-07-18T22:54:59.757Z
updated_at: 2026-07-18T23:11:54.596Z
closed_at: 2026-07-18T23:11:54.596Z
close_reason: "Addressed in 650b1f8 on feature/history-navigation; disposition map posted on PR #24; all gates green."
---
history.js stampedState spreads any object: Date/Map/array host state gets flattened; host-owned kpressScroll overwritten. Fix: augment only null or plain records without a conflicting non-numeric kpressScroll; otherwise leave entry untouched (fragment fallback covers traversal). Validate restored offsets with Number.isFinite. Tests: Date, array, key-collision.
