---
type: is
id: is-01kyh1128faa021b48wxd17zzr
title: Verify the published kpress 0.2.4 package and close the release
kind: task
status: closed
priority: 1
version: 5
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
updated_at: 2026-07-30T19:26:57.779Z
closed_at: 2026-07-30T19:26:57.775Z
close_reason: "Verified the exact PyPI kpress==0.2.4 package in a clean Python 3.14 environment: version, help, doctor, README quickstart, single-doc, static-site, and wrapped-site builds all passed from site-packages. PyPI serves the reviewed wheel and sdist with matching SHA256 digests, AGPL-3.0-or-later metadata, Python 3.12-3.14 classifiers, and expected source/issues links; GitHub release v0.2.4 carries the reviewed release notes and points to 9ba160f. PR #36 reconciled TODO.md, passed review and all checks, merged as f59c44f, and exact-main CI run 30574695542 passed."
---
From a clean environment, install the exact registry package kpress==0.2.4 and verify version, help, doctor, README quickstart, and representative bundled examples. Confirm the PyPI project page shows the expected AGPL metadata, Python classifiers, source/issues links, and release notes; confirm the GitHub release and package artifacts match the reviewed candidate; then reconcile/close all epic children and update the public release status.
