---
type: is
id: is-01kxcaxbt84v7hdbqqah579bp7
title: Enable dependency vulnerability monitoring for the public repository
kind: task
status: open
priority: 2
version: 1
labels: []
dependencies: []
created_at: 2026-07-12T23:34:30.983Z
updated_at: 2026-07-12T23:34:30.983Z
---
The release audit found npm audit clean, but GitHub's Dependabot alerts API reports that Dependabot alerts are disabled for this repository, and there is no Python vulnerability-audit gate in CI. Enable repository dependency alerts and add a lockfile-aware Python audit process appropriate to the supply-chain policy before or immediately with public release.
