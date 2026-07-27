---
type: is
id: is-01kyh1118c3xsmapj9d3bv74az
title: Perform the final 0.2.4 code and contract review
kind: task
status: open
priority: 1
version: 5
spec_path: docs/publishing.md
labels:
  - release
  - review
  - contract
  - breaking-alpha
dependencies:
  - type: blocks
    target: is-01kyh111g7g982p1der5dyxsz5
  - type: blocks
    target: is-01ky150r6vegs67zh623tnwy7j
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
created_at: 2026-07-27T05:33:39.468Z
updated_at: 2026-07-27T05:45:48.439Z
---
After all remediation changes land, review the aggregate v0.2.3...release-candidate delta rather than individual commits. Confirm Python APIs, template variables, CSS/JS contracts, data attributes, manifests, defaults, generated identifiers, and host behavior match the intended v0.2.4 design. For GitHub issue #33, verify the old heading algorithm and label/table slug coupling are removed completely, every consumer uses the new single source of truth, and no compatibility modes, alias ids, redirects, dual outputs, or stale documentation remain. Confirm docs, migration guidance, tests, and goldens match every intentional alpha-breaking change; record findings and block publication on unresolved P0/P1/P2 release defects.
