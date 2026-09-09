---
type: is
id: is-01m21p95r4n6f914aqtacdwrhy
title: Patch Vitest advisory GHSA-82fw-gwwq-j7x9
kind: bug
status: closed
priority: 2
version: 2
labels: []
dependencies: []
created_at: 2026-09-08T23:40:02.691Z
updated_at: 2026-09-09T00:07:39.824Z
closed_at: 2026-09-09T00:07:39.815Z
close_reason: Exact Vitest 4.1.11 fix committed as 349923d24f27521157a9632ee5e032742adf7772 and merged through PR52 at149a0c1f. npm audit reports zero vulnerabilities; frozen install and246 DOM tests pass.
resolution: null
duplicate_of: null
---
Update exact Vitest and its seven @vitest companion packages from 4.1.9 to 4.1.11. Fixed release was published 2026-08-18 and clears the 14-day policy. Preserve unrelated resolved versions; verify frozen npm ci, zero-advisory npm audit, complete DOM tests and supply-chain controls. Share this narrow dependency commit with documentation PR52.
