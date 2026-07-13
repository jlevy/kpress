---
type: is
id: is-01ktrcf35sbv7aex5whe2sqrq9
title: Bump actions/setup-node to a Node 24-compatible version in CI
kind: task
status: open
priority: 3
version: 3
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-06-10T09:05:28.248Z
updated_at: 2026-07-13T03:02:14.368Z
---
GitHub Actions annotation on main CI run 27265470376: actions/setup-node@v4 runs on Node.js 20, which GitHub forces to Node 24 by default starting 2026-06-16 and removes from runners 2026-09-16. Bump the action version in .github/workflows/ci.yml and confirm the lint/test/wheel-smoke jobs still pass.
