---
type: is
id: is-01ky150q341w6skb6esanebvct
title: Reset collapsible TOC control state during behavior disposal
kind: bug
status: closed
priority: 2
version: 6
spec_path: docs/publishing.md
labels:
  - toc
  - accessibility
  - javascript
dependencies:
  - type: blocks
    target: is-01kyh1118c3xsmapj9d3bv74az
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
created_at: 2026-07-21T01:35:32.451Z
updated_at: 2026-07-27T06:34:11.818Z
closed_at: 2026-07-27T06:34:11.817Z
close_reason: Implemented the reviewed TOC/runtime/CI correction with focused unit and real-browser regressions; the canonical make verify gate passes with all Playwright tests executed and no unexpected skips.
---
After expand-all is activated, disposing and re-binding toc.js removes row-collapse classes but leaves the expand-all button at aria-expanded=true with the Collapse TOC label. The new binding starts with allExpanded=false and re-collapses rows, so ARIA/UI state is contradictory and the first click expands instead of collapsing. Reset aria-expanded, aria-label, and title in the disposer; add a test that expands, disposes/rebinds, and clicks once.

## Notes

IMPLEMENTED LOCALLY 2026-07-27: TOC disposer now resets aria-expanded=false plus Expand TOC aria-label/title, removes collapsed rows, and regression covers expand -> dispose -> rebind -> first click.
