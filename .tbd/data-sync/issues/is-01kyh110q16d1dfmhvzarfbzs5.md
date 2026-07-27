---
type: is
id: is-01kyh110q16d1dfmhvzarfbzs5
title: Complete private security sign-off for the 0.2.4 candidate
kind: task
status: open
priority: 0
version: 3
spec_path: docs/publishing.md
labels:
  - release
  - security
dependencies:
  - type: blocks
    target: is-01kyh1118c3xsmapj9d3bv74az
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
created_at: 2026-07-27T05:33:38.912Z
updated_at: 2026-07-27T05:34:14.313Z
---
Resolve and regression-test every security-sensitive release blocker reported through the private review channel, without copying vulnerability details into public tbd data. Record only a private-review completion reference and a release-safe sign-off here; the release cannot proceed while this gate is open.
