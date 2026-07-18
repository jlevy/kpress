---
type: is
id: is-01kxvq1abvwmpz95ejj5akctz6
title: "PR #24 review R3: malformed fragment throws during popstate"
kind: bug
status: closed
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01kxvq0x39trk4mw02bgc0k182
created_at: 2026-07-18T22:54:59.962Z
updated_at: 2026-07-18T23:11:54.601Z
closed_at: 2026-07-18T23:11:54.601Z
close_reason: "Addressed in 650b1f8 on feature/history-navigation; disposition map posted on PR #24; all gates green."
---
history.js:112 unguarded decodeURIComponent('#%' -> URIError). Fix: non-throwing decode helper falling back to raw fragment; malformed-fragment traversal test.
