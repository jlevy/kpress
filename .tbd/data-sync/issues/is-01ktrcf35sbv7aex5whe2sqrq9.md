---
type: is
id: is-01ktrcf35sbv7aex5whe2sqrq9
title: Bump actions/setup-node to a Node 24-compatible version in CI
kind: task
status: closed
priority: 3
version: 5
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-06-10T09:05:28.248Z
updated_at: 2026-07-16T16:42:08.694Z
closed_at: 2026-07-16T16:42:08.694Z
close_reason: Implemented and validated the complete KPress tooling-floor convergence; all acceptance evidence is recorded in bead notes.
---
GitHub Actions annotation on main CI run 27265470376: actions/setup-node@v4 runs on Node.js 20, which GitHub forces to Node 24 by default starting 2026-06-16 and removes from runners 2026-09-16. Bump the action version in .github/workflows/ci.yml and confirm the lint/test/wheel-smoke jobs still pass.

## Notes

Confirmed the existing full-SHA actions/setup-node v6.4.0 workflow pin runs Node 24.18.0. Package policy now also enforces matching local nvm/fnm pins and workflow runtime parity.
