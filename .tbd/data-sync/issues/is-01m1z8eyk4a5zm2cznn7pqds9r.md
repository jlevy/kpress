---
type: is
id: is-01m1z8eyk4a5zm2cznn7pqds9r
title: "PR #58 review R7: the by-name KaTeX path rests on an unstated host assumption"
kind: bug
status: closed
priority: 3
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1z8drasjh3hct7hke23s0kj
created_at: 2026-09-08T01:00:03.027Z
updated_at: 2026-09-08T01:39:30.364Z
closed_at: 2026-09-08T01:39:30.363Z
close_reason: "Fixed on squares/math-paints-once (26d6822, 9b1778a); disposition posted on PR #58."
resolution: null
duplicate_of: null
---
katex-init.js L163-171 exempts KaTeX_Main/KaTeX_Math from description matching because the pinned bundle is the only thing that declares them. Nothing stops a host declaring its own KaTeX_Main faces; if one does, fonts.forEach yields both and FontFace.load() fetches KPress's shadowed files onto a page that never draws them, which is the same objection the design raises against rel=preload hints. Fix: state the assumption in the host-integration seam (do not redeclare KaTeX_Main/KaTeX_Math; use the KPress Math Text hook).
