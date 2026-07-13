---
type: is
id: is-01kxe7jb6j0hy8kmxbmb75mde4
title: "PR #13 review R2: restore optimizer determinism rationale"
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01kxe7j0pb94ny5by7jq9e8tzg
created_at: 2026-07-13T17:14:33.041Z
updated_at: 2026-07-13T17:21:33.460Z
closed_at: 2026-07-13T17:21:33.460Z
close_reason: Fixed in fe13b97; local and GitHub CI are green
---
Formal review R2 (Low), tests/test_golden_readable_vs_hashed.py:1. Restore the module-level explanation that optimizer=none avoids a Node dependency and that accepted mode differences are pinned in trees.yaml categories.
