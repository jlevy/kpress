---
type: is
id: is-01kxcppx52sr5t9s438qwamc62
title: Confirm trusted publishing and publish KPress 0.1.0
kind: task
status: closed
priority: 1
version: 7
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-13T03:00:42.273Z
updated_at: 2026-07-13T17:46:02.727Z
closed_at: 2026-07-13T17:46:02.726Z
close_reason: Published GitHub release v0.1.0 from green main commit 21f2d2b through PyPI Trusted Publishing; verified PyPI metadata, exact-version CLI and import, README quickstart, and all three bundled examples from a clean external environment.
---
Confirm the PyPI pending-publisher tuple for jlevy/kpress, merge the single stabilization PR with CI green, publish GitHub release v0.1.0, verify trusted publication, then install kpress==0.1.0 in a clean external project and repeat the documented CLI/library/examples smoke.

## Notes

All code-owned P1 stabilization gates are closed and validated (490 Python tests, 117 Vitest tests, full lint/type/public-hygiene, clean-room wheel, and final diff review). PR #11 GitHub Actions lint, Python 3.12/3.13/3.14, and wheel-smoke checks pass; optional Cursor Bugbot ended skipped. Remaining external/release work: confirm the PyPI trusted publisher, review and merge the single stabilization PR, publish exact tag v0.1.0, then verify installation from a clean external project.
