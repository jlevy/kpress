---
type: is
id: is-01kxcvck96qb5km7rkb2wmqdqz
title: "PR #11 review R2: diagnose release version mismatch"
kind: bug
status: closed
priority: 3
version: 3
labels: []
dependencies: []
parent_id: is-01kxcvc8mb76w6szhnm0bkttbd
created_at: 2026-07-13T04:22:27.364Z
updated_at: 2026-07-13T04:31:55.988Z
closed_at: 2026-07-13T04:31:55.988Z
close_reason: Fixed in d9ef18f; review threads replied to and resolved; local and GitHub Actions verification passed.
---
Cursor Bugbot Low finding at .github/workflows/publish.yml:54-55 (thread PRRT_kwDOS2H6rc6QRMME): print expected and actual package versions before failing the publish verification step.
