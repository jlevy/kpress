---
type: is
id: is-01kyh1kdvsza3f2qy8cfhhktc5
title: "Adopt exact GitHub heading-anchor semantics (GitHub #33)"
kind: feature
status: open
priority: 1
version: 9
spec_path: docs/publishing.md
labels:
  - release
  - anchors
  - markdown
  - breaking-alpha
dependencies:
  - type: blocks
    target: is-01kyh1118c3xsmapj9d3bv74az
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
child_order_hints:
  - is-01kyh1m8q37qtxf4r96g9d5g21
  - is-01kyh1mgqdqtezed0cda8qm03h
  - is-01kyh1mtcjvq2v0s4fs62y1jsp
  - is-01kyh1n3gzvf1bn35dz3xteteq
  - is-01kyh1n9kc7rrjc7ks3tc558aa
  - is-01kyh1nrge3scekb0ggx5n9261
  - is-01kyh1p3vz1r6qaqc9693pte3d
created_at: 2026-07-27T05:43:42.200Z
updated_at: 2026-07-27T05:45:31.808Z
---
Resolve https://github.com/jlevy/kpress/issues/33 as a v0.2.4 release blocker. Replace the current ASCII-only, suffix-from-2 heading IDs with a dependency-free Python port whose contract is pinned to github-slugger 2.0.0, tag commit 3461c4350868329c8530904d170358bca1d31448, and its 78 published fixtures. The stateful slugger is scoped per parsed document; heading IDs, DocumentTree metadata, TOC hrefs, page-model hrefs, internal-link diagnostics, history navigation, scroll spy, and tooltips must agree for punctuation, Unicode, empty results, and duplicate collisions. KPress is alpha: DO NOT MAINTAIN the old algorithm or add legacy modes, alias anchors, redirects, fallback IDs, or dual output. Remove obsolete code and document the intentional anchor migration. Keep heading slugs separate from footnote identities, table column metadata, routes, widgets, tabs, and CSS-only tokens.
