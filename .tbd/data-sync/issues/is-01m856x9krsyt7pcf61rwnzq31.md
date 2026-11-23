---
type: is
id: is-01m856x9krsyt7pcf61rwnzq31
title: "Release 0.3.10 with native task-list tokens (PR #82) for Metabrowser's rendered diff"
kind: task
status: open
priority: 2
version: 2
spec_path: TODO.md
refs:
  - kind: pr
    url: https://github.com/jlevy/kpress/pull/82
    at: 2026-11-23T22:02:34.240Z
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-11-23T22:02:33.463Z
updated_at: 2026-11-23T22:02:34.241Z
---
Metabrowser's rendered diff (its bead mb-rm6u) needs KPress's kpress_task_checkbox token and the sanitized checkbox from PR #82 (kpr-1m2b). Merge #82, release 0.3.10, then Metabrowser bumps kpress and drops its task-list refusal. Merge and release wait for the user's go.
