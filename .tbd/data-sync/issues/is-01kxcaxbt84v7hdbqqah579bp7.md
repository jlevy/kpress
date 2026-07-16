---
type: is
id: is-01kxcaxbt84v7hdbqqah579bp7
title: Enable dependency vulnerability monitoring for the public repository
kind: task
status: closed
priority: 2
version: 5
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-12T23:34:30.983Z
updated_at: 2026-07-16T16:42:08.701Z
closed_at: 2026-07-16T16:42:08.701Z
close_reason: Implemented and validated the complete KPress tooling-floor convergence; all acceptance evidence is recorded in bead notes.
---
The release audit found npm audit clean, but GitHub's Dependabot alerts API reports that Dependabot alerts are disabled for this repository, and there is no Python vulnerability-audit gate in CI. Enable repository dependency alerts and add a lockfile-aware Python audit process appropriate to the supply-chain policy before or immediately with public release.

## Notes

GitHub vulnerability-alerts API now returns 204 (enabled). The release gate includes npm audit and uv's frozen lock audit; both passed with zero findings on 2026-07-16.
