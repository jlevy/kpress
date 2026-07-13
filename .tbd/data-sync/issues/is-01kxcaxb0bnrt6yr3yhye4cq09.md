---
type: is
id: is-01kxcaxb0bnrt6yr3yhye4cq09
title: Restore Windows portability or correct the platform claim
kind: bug
status: open
priority: 1
version: 4
spec_path: TODO.md
labels: []
dependencies:
  - type: blocks
    target: is-01kxcppx52sr5t9s438qwamc62
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-12T23:34:30.154Z
updated_at: 2026-07-13T03:02:15.028Z
---
src/kpress/publish/optimize.py imports POSIX-only fcntl unconditionally. kpress.publish and kpress.cli transitively import that module, so the package cannot import on Windows even though pyproject.toml declares Operating System :: OS Independent. CI only runs on Ubuntu. Replace the lock with a portable implementation and add Windows CI/smoke coverage, or explicitly restrict supported platforms and metadata.
