---
type: is
id: is-01kyh1mtcjvq2v0s4fs62y1jsp
title: Implement the dependency-free Python GitHub slugger
kind: task
status: open
priority: 1
version: 2
spec_path: docs/publishing.md
labels:
  - anchors
  - python
dependencies:
  - type: blocks
    target: is-01kyh1n3gzvf1bn35dz3xteteq
parent_id: is-01kyh1kdvsza3f2qy8cfhhktc5
created_at: 2026-07-27T05:44:27.790Z
updated_at: 2026-07-27T05:45:29.739Z
---
Implement a small stateful Python slugger with one instance per parse_markdown call. Use vendored generated Unicode data or equivalent pinned source data so results do not vary with the Python runtime Unicode database; validate every supported Python version against the complete upstream fixtures. Preserve upstream collision bookkeeping, including cases where a natural heading already occupies a suffixed slug. Do not trim, collapse hyphens, substitute section for an empty result, expose maintainCase, retain the old set-based suffix-from-2 function, or add a compatibility branch. Keep the implementation internal unless a separately reviewed public API need is demonstrated. Remove the old heading-specific use of _SLUG_RE and keep provenance next to generated data.
