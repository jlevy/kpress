---
type: is
id: is-01kxcwyzj7w02p1yzp1nkqs8b6
title: "Second review R3: dispose and prune detached widget mounts"
kind: bug
status: closed
priority: 3
version: 3
labels: []
dependencies: []
parent_id: is-01kxcwyyh3fkjb6h7w64bmkzqb
created_at: 2026-07-13T04:49:58.342Z
updated_at: 2026-07-13T05:09:09.943Z
closed_at: 2026-07-13T05:09:09.943Z
close_reason: Addressed in 7f6f6cb with cold-cache CI follow-up 86e7603; complete disposition posted, all inline threads resolved, and GitHub Actions plus Cursor Bugbot pass.
---
src/kpress/format/static/js/runtime.js: remove disconnected mounts regardless of data-kpress-widget and run their disposer instead of remounting detached DOM.
