---
type: is
id: is-01ky150r6vegs67zh623tnwy7j
title: Prepare 0.2.4 release notes and README version references
kind: task
status: open
priority: 1
version: 4
spec_path: docs/publishing.md
labels:
  - release
  - docs
dependencies:
  - type: blocks
    target: is-01kyh11209n4en189vpa2ag5b9
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
created_at: 2026-07-21T01:35:33.594Z
updated_at: 2026-07-27T05:34:14.313Z
---
Before tagging v0.2.4, complete publishing checklist step 4: add docs/releases/0.2.4.md, add it to docs/README.md as current, and update README version/install/self-contained-output references from 0.2.3 to 0.2.4. Dynamic package versioning already derives 0.2.4 from the tag; no hard-coded package version bump is needed.
