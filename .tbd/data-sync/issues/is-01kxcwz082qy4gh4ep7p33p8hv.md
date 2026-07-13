---
type: is
id: is-01kxcwz082qy4gh4ep7p33p8hv
title: "Second review R5: guard sanitizer policy/audit parity"
kind: bug
status: closed
priority: 3
version: 3
labels: []
dependencies: []
parent_id: is-01kxcwyyh3fkjb6h7w64bmkzqb
created_at: 2026-07-13T04:49:59.041Z
updated_at: 2026-07-13T05:09:09.961Z
closed_at: 2026-07-13T05:09:09.961Z
close_reason: Addressed in 7f6f6cb with cold-cache CI follow-up 86e7603; complete disposition posted, all inline threads resolved, and GitHub Actions plus Cursor Bugbot pass.
---
src/kpress/format/sanitize.py and tests/test_sanitize.py: cross-reference the mirrored audit policy and add an adversarial corpus test requiring specific diagnostics whenever nh3 rewrites input.
