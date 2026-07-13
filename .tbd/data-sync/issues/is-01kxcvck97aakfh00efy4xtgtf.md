---
type: is
id: is-01kxcvck97aakfh00efy4xtgtf
title: "PR #11 review R1: use explicit release tag for publish gate"
kind: bug
status: closed
priority: 1
version: 3
labels: []
dependencies: []
parent_id: is-01kxcvc8mb76w6szhnm0bkttbd
created_at: 2026-07-13T04:22:27.366Z
updated_at: 2026-07-13T04:31:55.961Z
closed_at: 2026-07-13T04:31:55.960Z
close_reason: Fixed in d9ef18f; review threads replied to and resolved; local and GitHub Actions verification passed.
---
Cursor Bugbot High finding at .github/workflows/publish.yml:46-55 (thread PRRT_kwDOS2H6rc6QRMMC): derive and checkout the release tag explicitly from github.event.release.tag_name so the version gate is tied to the published release payload.
