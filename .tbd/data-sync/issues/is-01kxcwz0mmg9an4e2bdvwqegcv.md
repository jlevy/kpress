---
type: is
id: is-01kxcwz0mmg9an4e2bdvwqegcv
title: "Second review R6: read package version without parsing CLI output"
kind: bug
status: closed
priority: 3
version: 3
labels: []
dependencies: []
parent_id: is-01kxcwyyh3fkjb6h7w64bmkzqb
created_at: 2026-07-13T04:49:59.441Z
updated_at: 2026-07-13T05:09:09.966Z
closed_at: 2026-07-13T05:09:09.966Z
close_reason: Addressed in 7f6f6cb with cold-cache CI follow-up 86e7603; complete disposition posted, all inline threads resolved, and GitHub Actions plus Cursor Bugbot pass.
---
.github/workflows/publish.yml and tests/test_release_workflow.py: verify the release version from kpress.__version__ instead of awk-parsing kpress --version.
