---
type: is
id: is-01kxnva4454kh5hfea9w9v4da3
title: Make Python and npm workflows hermetic and lock-safe
kind: task
status: closed
priority: 2
version: 5
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-16T16:14:16.197Z
updated_at: 2026-07-16T16:42:08.627Z
closed_at: 2026-07-16T16:42:08.627Z
close_reason: Implemented and validated the complete KPress tooling-floor convergence; all acceptance evidence is recorded in bead notes.
---
Ensure Make, hooks, CI, and documented commands isolate repository uv policy, run frozen/locked dependency graphs, and neutralize incompatible ambient npm configuration.

## Notes

Make now passes the checked-in uv.toml explicitly, validates uv.lock with sync --locked, uses frozen runners, and neutralizes conflicting ambient npm variables. Hooks, CI, contributor docs, validation docs, and package-policy tests enforce the same contract.
