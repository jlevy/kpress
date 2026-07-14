---
type: is
id: is-01ktrcf35sbv7aex5whe2sqrq9
title: Bump actions/setup-node to a Node 24-compatible version in CI
kind: task
status: closed
priority: 3
version: 4
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-06-10T09:05:28.248Z
updated_at: 2026-07-14T20:28:06.896Z
closed_at: 2026-07-14T20:28:06.896Z
close_reason: "Tooling floor, dependency monitoring, Node action upgrade, and same-document tooltip asset closure are implemented; make verify and PR #17 CI are green."
---
GitHub Actions annotation on main CI run 27265470376: actions/setup-node@v4 runs on Node.js 20, which GitHub forces to Node 24 by default starting 2026-06-16 and removes from runners 2026-09-16. Bump the action version in .github/workflows/ci.yml and confirm the lint/test/wheel-smoke jobs still pass.
