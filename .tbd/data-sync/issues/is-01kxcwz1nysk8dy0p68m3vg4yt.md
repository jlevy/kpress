---
type: is
id: is-01kxcwz1nysk8dy0p68m3vg4yt
title: "Second review B1: scan both public skill trees"
kind: bug
status: closed
priority: 3
version: 3
labels: []
dependencies: []
parent_id: is-01kxcwyyh3fkjb6h7w64bmkzqb
created_at: 2026-07-13T04:50:00.509Z
updated_at: 2026-07-13T05:09:09.984Z
closed_at: 2026-07-13T05:09:09.984Z
close_reason: Addressed in 7f6f6cb with cold-cache CI follow-up 86e7603; complete disposition posted, all inline threads resolved, and GitHub Actions plus Cursor Bugbot pass.
---
devtools/public_hygiene.py:42 and tests/test_public_hygiene.py: include .claude alongside .agents in the default public hygiene scan.
