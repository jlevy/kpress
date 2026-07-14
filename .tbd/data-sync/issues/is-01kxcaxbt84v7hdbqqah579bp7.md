---
type: is
id: is-01kxcaxbt84v7hdbqqah579bp7
title: Enable dependency vulnerability monitoring for the public repository
kind: task
status: closed
priority: 2
version: 4
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-12T23:34:30.983Z
updated_at: 2026-07-14T20:28:06.902Z
closed_at: 2026-07-14T20:28:06.902Z
close_reason: "Tooling floor, dependency monitoring, Node action upgrade, and same-document tooltip asset closure are implemented; make verify and PR #17 CI are green."
---
The release audit found npm audit clean, but GitHub's Dependabot alerts API reports that Dependabot alerts are disabled for this repository, and there is no Python vulnerability-audit gate in CI. Enable repository dependency alerts and add a lockfile-aware Python audit process appropriate to the supply-chain policy before or immediately with public release.
