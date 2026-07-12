---
type: is
id: is-01kxcaxb0bnrt6yr3yhye4cq09
title: Restore Windows portability or correct the platform claim
kind: bug
status: open
priority: 1
version: 1
labels: []
dependencies: []
created_at: 2026-07-12T23:34:30.154Z
updated_at: 2026-07-12T23:34:30.154Z
---
src/kpress/publish/optimize.py imports POSIX-only fcntl unconditionally. kpress.publish and kpress.cli transitively import that module, so the package cannot import on Windows even though pyproject.toml declares Operating System :: OS Independent. CI only runs on Ubuntu. Replace the lock with a portable implementation and add Windows CI/smoke coverage, or explicitly restrict supported platforms and metadata.
