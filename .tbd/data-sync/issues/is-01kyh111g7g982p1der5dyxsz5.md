---
type: is
id: is-01kyh111g7g982p1der5dyxsz5
title: Run the complete 0.2.4 release-candidate validation gate
kind: task
status: closed
priority: 1
version: 6
spec_path: docs/publishing.md
labels:
  - release
  - testing
  - ci
dependencies:
  - type: blocks
    target: is-01kyh111r6095nckxsmz94wddt
  - type: blocks
    target: is-01kyh11209n4en189vpa2ag5b9
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
created_at: 2026-07-27T05:33:39.718Z
updated_at: 2026-07-27T06:47:39.450Z
closed_at: 2026-07-27T06:47:39.449Z
close_reason: "Release-candidate commit 4c8a713 passed the canonical local make verify gate and PR #35 CI: lint, distribution, and exact Python 3.12, 3.13, and 3.14 jobs all green. Real-browser suites executed without unexpected skips; both dependency audits are clean."
---
From a clean up-to-date main on the exact release-candidate SHA, run make verify with the repository-pinned Python and Node toolchains. Require lint/type/format/hygiene/supply-chain checks, all Python and browserless tests, both dependency audits, distribution build and isolated wheel smoke to pass. Run focused real-browser TOC, tooltip, wide-table, navigation, security-boundary, and lifecycle probes; treat unexpected skips, console errors, network failures, or audit findings as release failures. Confirm exact-head GitHub CI is green on Python 3.12-3.14.

## Notes

LOCAL RELEASE GATE GREEN 2026-07-27 under Python 3.14.0 and Node 24.18.0/npm 11.10.0: make verify passed 574 pytest/Playwright tests and 173 Vitest tests, Ruff/BasedPyright/codespell/Biome/tsc/public-hygiene/flowmark/supply-chain checks, npm and uv audits with zero findings, build inspection, and isolated wheel smoke. Real-browser TOC/history/tooltips/wide-table tests executed with no skips. Awaiting committed candidate SHA and GitHub Python 3.12-3.14 CI.
