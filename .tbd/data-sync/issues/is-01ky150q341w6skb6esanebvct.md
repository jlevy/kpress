---
type: is
id: is-01ky150q341w6skb6esanebvct
title: Reset collapsible TOC control state during behavior disposal
kind: bug
status: open
priority: 2
version: 4
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
updated_at: 2026-07-27T05:34:14.313Z
---
After expand-all is activated, disposing and re-binding toc.js removes row-collapse classes but leaves the expand-all button at aria-expanded=true with the Collapse TOC label. The new binding starts with allExpanded=false and re-collapses rows, so ARIA/UI state is contradictory and the first click expands instead of collapsing. Reset aria-expanded, aria-label, and title in the disposer; add a test that expands, disposes/rebinds, and clicks once.
