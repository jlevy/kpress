---
type: is
id: is-01kxnva5hvwg73e953xeb08423
title: Validate installed KPress wheels through the public CLI
kind: task
status: closed
priority: 2
version: 5
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-16T16:14:17.659Z
updated_at: 2026-07-16T16:42:08.682Z
closed_at: 2026-07-16T16:42:08.682Z
close_reason: Implemented and validated the complete KPress tooling-floor convergence; all acceptance evidence is recorded in bead notes.
---
Extend clean-wheel validation to exercise version/help/doctor and a real static-site build from outside the checkout while retaining the existing asset/resource checks.

## Notes

Distribution validation creates an isolated venv outside the checkout, installs the built wheel, verifies packaged resources, runs version, help, doctor, and build commands, and checks the emitted HTML, manifest, CSS, JS, and font trees. make build passed for KPress 0.2.2 artifacts.
