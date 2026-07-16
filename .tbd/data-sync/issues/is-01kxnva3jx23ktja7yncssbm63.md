---
type: is
id: is-01kxnva3jx23ktja7yncssbm63
title: Pin and enforce the Node toolchain across local and CI workflows
kind: task
status: in_progress
priority: 2
version: 4
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-16T16:14:15.645Z
updated_at: 2026-07-16T16:40:17.158Z
---
Add .nvmrc and .node-version at Node 24.18.0, enforce exact parity in package policy, and document nvm/fnm-compatible setup.

## Notes

Implemented exact Node 24.18.0 pins in .nvmrc and .node-version; package policy enforces parity with package.json and all workflows. Both fnm use and nvm use selected v24.18.0; make install passed under the pinned fnm runtime.
