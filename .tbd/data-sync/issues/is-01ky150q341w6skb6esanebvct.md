---
type: is
id: is-01ky150q341w6skb6esanebvct
title: Reset collapsible TOC control state during behavior disposal
kind: bug
status: open
priority: 2
version: 1
labels:
  - toc
  - accessibility
  - javascript
dependencies: []
parent_id: is-01ky147hh0nbx9vhjphw3fabn3
created_at: 2026-07-21T01:35:32.451Z
updated_at: 2026-07-21T01:35:32.451Z
---
After expand-all is activated, disposing and re-binding toc.js removes row-collapse classes but leaves the expand-all button at aria-expanded=true with the Collapse TOC label. The new binding starts with allExpanded=false and re-collapses rows, so ARIA/UI state is contradictory and the first click expands instead of collapsing. Reset aria-expanded, aria-label, and title in the disposer; add a test that expands, disposes/rebinds, and clicks once.
