---
type: is
id: is-01kyh1128faa021b48wxd17zzr
title: Verify the published kpress 0.2.4 package and close the release
kind: task
status: open
priority: 1
version: 3
spec_path: docs/publishing.md
labels:
  - release
  - publishing
  - verification
dependencies:
  - type: blocks
    target: is-01kyh0z636f2vtfzx6apaxvp2r
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
created_at: 2026-07-27T05:33:40.494Z
updated_at: 2026-07-27T05:34:14.313Z
---
From a clean environment, install the exact registry package kpress==0.2.4 and verify version, help, doctor, README quickstart, and representative bundled examples. Confirm the PyPI project page shows the expected AGPL metadata, Python classifiers, source/issues links, and release notes; confirm the GitHub release and package artifacts match the reviewed candidate; then reconcile/close all epic children and update the public release status.
