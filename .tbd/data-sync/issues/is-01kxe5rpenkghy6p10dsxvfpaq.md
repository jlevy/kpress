---
type: is
id: is-01kxe5rpenkghy6p10dsxvfpaq
title: Verify PyPI Trusted Publisher configuration
kind: task
status: closed
priority: 2
version: 3
labels: []
dependencies: []
created_at: 2026-07-13T16:43:04.020Z
updated_at: 2026-07-13T16:43:09.582Z
closed_at: 2026-07-13T16:43:09.581Z
close_reason: OIDC publisher fields verified; one optional hardening recommendation reported.
---
Confirm the pending PyPI publisher identity matches the KPress GitHub release workflow and identify any environment-name hardening needed.

## Notes

Verified against origin/main 1551560 and current PyPI docs: project kpress, owner jlevy, repo kpress, and workflow publish.yml match. Workflow declares environment: pypi; PyPI Environment Any will work, but setting it to pypi is strongly recommended for tighter identity matching. Workflow has release-only trigger and job-level id-token: write.
