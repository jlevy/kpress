---
type: is
id: is-01kyh111r6095nckxsmz94wddt
title: Inspect release artifacts and clean-room user workflows
kind: task
status: open
priority: 1
version: 3
spec_path: docs/publishing.md
labels:
  - release
  - packaging
  - testing
dependencies:
  - type: blocks
    target: is-01kyh11209n4en189vpa2ag5b9
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
created_at: 2026-07-27T05:33:39.973Z
updated_at: 2026-07-27T05:34:14.313Z
---
Inspect the final wheel and sdist contents and metadata, then install the wheel outside the checkout. Run the README quickstart and all bundled static-site, wrapped-site, and single-document examples against that installed artifact; verify linked and hashed reader assets load, the new TOC/document-actions behavior is present when enabled, repository-only files do not ship, and outputs are reproducible.
