---
type: is
id: is-01kxnva4kfhwdgf0y1padfmqax
title: Make the Makefile dependency graph parallel-safe
kind: task
status: in_progress
priority: 2
version: 4
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-16T16:14:16.686Z
updated_at: 2026-07-16T16:40:18.879Z
---
Declare target prerequisites so parallel make invocations preserve install-before-tooling and build-before-distribution validation ordering.

## Notes

Default formatting, linting, and testing are serialized through recursive make after one install; direct quality targets use install order-only prerequisites. An actual make -j4 lint-check test build passed, including distribution validation.
