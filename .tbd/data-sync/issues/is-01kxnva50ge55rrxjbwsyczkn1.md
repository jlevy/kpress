---
type: is
id: is-01kxnva50ge55rrxjbwsyczkn1
title: Harden publish-time caches and artifact validation
kind: task
status: closed
priority: 2
version: 4
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-16T16:14:17.104Z
updated_at: 2026-07-16T16:42:08.675Z
closed_at: 2026-07-16T16:42:08.675Z
close_reason: Implemented and validated the complete KPress tooling-floor convergence; all acceptance evidence is recorded in bead notes.
---
Disable mutable setup caches in the tag-triggered publish workflow and strengthen public artifact, doc-footer, and spelling hygiene without weakening release smoke tests.

## Notes

Publish disables uv and npm cache restoration. Public hygiene scans all maintained roots, enforces Common Doc footers with explicit rendering/generated exemptions, broadens codespell coverage, and verifies README footers inside artifacts.
