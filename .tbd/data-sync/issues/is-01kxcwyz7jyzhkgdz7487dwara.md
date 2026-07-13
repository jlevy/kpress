---
type: is
id: is-01kxcwyz7jyzhkgdz7487dwara
title: "Second review R2: preserve settings interaction during presentation changes"
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01kxcwyyh3fkjb6h7w64bmkzqb
created_at: 2026-07-13T04:49:58.001Z
updated_at: 2026-07-13T05:09:09.937Z
closed_at: 2026-07-13T05:09:09.937Z
close_reason: Addressed in 7f6f6cb with cold-cache CI follow-up 86e7603; complete disposition posted, all inline threads resolved, and GitHub Actions plus Cursor Bugbot pass.
---
src/kpress/format/static/js/runtime.js and settings-widget.js: theme/palette presentation reapply must preserve the active settings menu and focus, with a reentrancy guard.
