---
type: is
id: is-01m856x9krsyt7pcf61rwnzq31
title: "Release 0.3.10 with native task-list tokens (PR #82) for Metabrowser's rendered diff"
kind: task
status: open
priority: 2
version: 4
spec_path: TODO.md
refs:
  - kind: pr
    url: https://github.com/jlevy/kpress/pull/82
    at: 2026-11-23T22:02:34.240Z
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-11-23T22:02:33.463Z
updated_at: 2026-11-23T22:18:43.762Z
---
Metabrowser's rendered diff (its bead mb-rm6u) needs KPress's kpress_task_checkbox token and the sanitized checkbox from PR #82 (kpr-1m2b). The user approved on 2026-11-23: once #82 is fully reviewed (kpr-3pph) and every confirmed finding is addressed, merge it and cut a patch release, 0.3.10. Then Metabrowser bumps kpress and draws the boxes (mb-rm6u).
