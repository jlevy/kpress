---
type: is
id: is-01kyh1m8q37qtxf4r96g9d5g21
title: Freeze the GitHub slug contract, fixtures, and provenance
kind: task
status: open
priority: 1
version: 4
spec_path: docs/publishing.md
labels:
  - anchors
  - tests
  - supply-chain
dependencies:
  - type: blocks
    target: is-01kyh1mgqdqtezed0cda8qm03h
  - type: blocks
    target: is-01kyh1n9kc7rrjc7ks3tc558aa
  - type: blocks
    target: is-01kyh1nrge3scekb0ggx5n9261
parent_id: is-01kyh1kdvsza3f2qy8cfhhktc5
created_at: 2026-07-27T05:44:09.697Z
updated_at: 2026-07-27T05:45:30.342Z
---
Define the implementation contract before code changes. Pin parity to github-slugger 2.0.0 at commit 3461c4350868329c8530904d170358bca1d31448, not to mutable live GitHub behavior. Bring the complete 78-case published fixture corpus into the test surface with its ISC provenance and required license notice; do not add or execute an npm runtime dependency. Record the exact rules: use visible plain heading text, lowercase with GitHub-compatible mappings, remove the pinned Unicode 13 exclusion set, replace each literal ASCII space with one hyphen without trimming or collapsing, allow an empty base slug, and allocate duplicate/collision suffixes from -1 using the upstream occurrence bookkeeping. KPress does not expose maintainCase. Future upstream fixture or Unicode revisions require an explicit reviewed contract change.
