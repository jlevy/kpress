---
type: is
id: is-01ky150r6vegs67zh623tnwy7j
title: Prepare 0.2.4 release notes and README version references
kind: task
status: closed
priority: 1
version: 6
spec_path: docs/publishing.md
labels:
  - release
  - docs
  - breaking-alpha
dependencies:
  - type: blocks
    target: is-01kyh11209n4en189vpa2ag5b9
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
created_at: 2026-07-21T01:35:33.594Z
updated_at: 2026-07-27T06:34:18.221Z
closed_at: 2026-07-27T06:34:18.221Z
close_reason: "Completed the 0.2.4 documentation/tracking deliverables: archived and reconciled the TOC plan, corrected TODO/docs indexes and version references, and added reviewed alpha-breaking migration/release notes. Flowmark and the full docs gate pass."
---
Before tagging v0.2.4, complete publishing checklist step 4: add docs/releases/0.2.4.md, add it to docs/README.md as current, and update README version/install/self-contained-output references from 0.2.3 to 0.2.4. The release notes must prominently describe the intentional alpha migration from GitHub issue #33 with old/new anchor examples, duplicate suffix changes, Unicode behavior, ordinal footnote ids, literal table data-col plus data-col-index, and the required downstream action to regenerate stored deep links and host link indexes. State that no legacy anchors or compatibility attributes are emitted. Dynamic package versioning already derives 0.2.4 from the tag; no hard-coded package version bump is needed.
