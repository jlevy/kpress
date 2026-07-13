---
type: is
id: is-01kxcppx52sr5t9s438qwamc62
title: Confirm trusted publishing and publish KPress 0.1.0
kind: task
status: open
priority: 1
version: 3
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-13T03:00:42.273Z
updated_at: 2026-07-13T03:24:05.798Z
---
Confirm the PyPI pending-publisher tuple for jlevy/kpress, merge the single stabilization PR with CI green, publish GitHub release v0.1.0, verify trusted publication, then install kpress==0.1.0 in a clean external project and repeat the documented CLI/library/examples smoke.

## Notes

All code-owned P1 stabilization gates are closed and validated (491 Python tests, 117 Vitest tests, full lint/type/public-hygiene gate, clean-room wheel). Remaining work is external/release-state: review and merge the single stabilization PR, confirm the PyPI trusted publisher, publish exact tag v0.1.0, then verify installation from a clean external project.
