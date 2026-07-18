---
type: is
id: is-01kxvq19yfsxq6pq6fqkqgjeaz
title: "PR #24 review R1: Contents link bypasses native history"
kind: bug
status: closed
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01kxvq0x39trk4mw02bgc0k182
created_at: 2026-07-18T22:54:59.533Z
updated_at: 2026-07-18T23:11:54.585Z
closed_at: 2026-07-18T23:11:54.584Z
close_reason: "Addressed in 650b1f8 on feature/history-navigation; disposition map posted on PR #24; all gates green."
---
toc.js:181 [data-kpress-toc-top] still preventDefaults and scrolls manually: URL keeps stale hash, no entry pushed. Fix: native navigation for the top link (bare-# supported in the history stamp path; pane-top fallback for fragmentless entries); keep drawer bookkeeping. Regression test.
