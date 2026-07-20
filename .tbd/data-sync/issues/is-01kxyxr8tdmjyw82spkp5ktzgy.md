---
type: is
id: is-01kxyxr8tdmjyw82spkp5ktzgy
title: "Client behavior: toc.js grouping, visibility predicate, expand-all toggle, scroll-follow"
kind: task
status: closed
priority: 2
version: 4
spec_path: docs/project/specs/active/plan-2026-07-18-collapsible-toc.md
labels: []
dependencies:
  - type: blocks
    target: is-01kxyxr916p6rmvk9q9zpakcth
  - type: blocks
    target: is-01kxyxr97zpfhc03ge2fj8qhqc
parent_id: is-01kxvtjgzee34yvykhc06e775z
created_at: 2026-07-20T04:50:06.796Z
updated_at: 2026-07-20T06:18:30.713Z
closed_at: 2026-07-20T06:18:30.713Z
close_reason: "Implemented on feat/toc-collapse (932d4b1, 2b396d9): server markup + contract + CSS, toc.js collapse behavior; pytest, vitest, Biome, tsc green."
---
In the existing toc behavior: partition the flat li list into spine groups by collapse depth (head group before first spine entry always visible); single visibility predicate (allExpanded OR (expandOnScroll AND active group)); button toggles aria-expanded and aria-label; active group updates inside setActiveLink so scroll, TOC-click, and hash arrival all follow; JS-channel config collapseDepth/expandOnScroll via behaviors.configure overrides the data attributes; all listeners through on()/cleanups disposers. Vitest toc-collapse suite: partitioning (skipped levels, pre-spine entries), predicate under all four allExpanded x activeGroup combos, ARIA state, config precedence, disposer coverage. Spec: Design > Client state.
