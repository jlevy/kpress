---
type: is
id: is-01kxnva4454kh5hfea9w9v4da3
title: Make Python and npm workflows hermetic and lock-safe
kind: task
status: in_progress
priority: 2
version: 4
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-16T16:14:16.197Z
updated_at: 2026-07-16T16:40:17.767Z
---
Ensure Make, hooks, CI, and documented commands isolate repository uv policy, run frozen/locked dependency graphs, and neutralize incompatible ambient npm configuration.

## Notes

Make now passes the checked-in uv.toml explicitly, validates uv.lock with sync --locked, uses frozen runners, and neutralizes conflicting ambient npm variables. Hooks, CI, contributor docs, validation docs, and package-policy tests enforce the same contract.
