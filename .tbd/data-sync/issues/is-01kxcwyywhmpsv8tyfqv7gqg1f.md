---
type: is
id: is-01kxcwyywhmpsv8tyfqv7gqg1f
title: "Second review R1: require explicit network permission for optimizer bootstrap"
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01kxcwyyh3fkjb6h7w64bmkzqb
created_at: 2026-07-13T04:49:57.648Z
updated_at: 2026-07-13T05:09:09.919Z
closed_at: 2026-07-13T05:09:09.917Z
close_reason: Addressed in 7f6f6cb with cold-cache CI follow-up 86e7603; complete disposition posted, all inline threads resolved, and GitHub Actions plus Cursor Bugbot pass.
---
docs/kpress-design.md:1905 and src/kpress/publish/capability.py:69-79: make doctor --allow-network the only cold-cache bootstrap path; builds and FullOptimizer must fail without a warm reviewed cache.
