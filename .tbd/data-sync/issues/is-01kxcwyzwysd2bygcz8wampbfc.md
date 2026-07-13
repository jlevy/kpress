---
type: is
id: is-01kxcwyzwysd2bygcz8wampbfc
title: "Second review R4: document npm minimum-release-age defense"
kind: bug
status: closed
priority: 3
version: 3
labels: []
dependencies: []
parent_id: is-01kxcwyyh3fkjb6h7w64bmkzqb
created_at: 2026-07-13T04:49:58.685Z
updated_at: 2026-07-13T05:09:09.949Z
closed_at: 2026-07-13T05:09:09.949Z
close_reason: Addressed in 7f6f6cb with cold-cache CI follow-up 86e7603; complete disposition posted, all inline threads resolved, and GitHub Actions plus Cursor Bugbot pass.
---
src/kpress/publish/optimize.py:_npm_env: state the unit, npm 11.10+ requirement, and defense-in-depth role behind the integrity-pinned npm ci lock.
