---
type: is
id: is-01kyh111g7g982p1der5dyxsz5
title: Run the complete 0.2.4 release-candidate validation gate
kind: task
status: open
priority: 1
version: 4
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
updated_at: 2026-07-27T05:34:14.313Z
---
From a clean up-to-date main on the exact release-candidate SHA, run make verify with the repository-pinned Python and Node toolchains. Require lint/type/format/hygiene/supply-chain checks, all Python and browserless tests, both dependency audits, distribution build and isolated wheel smoke to pass. Run focused real-browser TOC, tooltip, wide-table, navigation, security-boundary, and lifecycle probes; treat unexpected skips, console errors, network failures, or audit findings as release failures. Confirm exact-head GitHub CI is green on Python 3.12-3.14.
