---
type: is
id: is-01kxcppx52sr5t9s438qwamc62
title: Confirm trusted publishing and publish KPress 0.1.0
kind: task
status: closed
priority: 1
version: 8
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-13T03:00:42.273Z
updated_at: 2026-07-13T17:50:07.197Z
closed_at: 2026-07-13T17:46:02.726Z
close_reason: Published GitHub release v0.1.0 from green main commit 21f2d2b through PyPI Trusted Publishing; verified PyPI metadata, exact-version CLI and import, README quickstart, and all three bundled examples from a clean external environment.
---
Confirm the PyPI pending-publisher tuple for jlevy/kpress, merge the single stabilization PR with CI green, publish GitHub release v0.1.0, verify trusted publication, then install kpress==0.1.0 in a clean external project and repeat the documented CLI/library/examples smoke.

## Notes

Completed 2026-07-13: merged release cleanups in PRs #13 and #14; published standard GitHub release v0.1.0 from commit 21f2d2b; PyPI Trusted Publishing run 29271499202 passed tag/version verification, tests, build, and upload; PyPI metadata, uvx CLI, clean Python 3.13 import, README build, and all three bundled examples passed. PR #15 updated the public ledger and post-release main CI passed.
