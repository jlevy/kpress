---
type: is
id: is-01m1yycvp74jn8484k1zxvtma8
title: Tooltip preview should not grow the scroller's scroll extent
kind: bug
status: open
priority: 2
version: 1
labels: []
dependencies: []
created_at: 2026-09-07T22:04:08.773Z
updated_at: 2026-09-07T22:04:08.773Z
---
Nonblocking suggestion from the PR #53 senior review (comment 5575825645). A link in the final table row of a 700px pane opens a bottom-right preview at y=706; its 337px height increases the scroller's scrollHeight from 1386 to 1729. The offscreen table placement predates PR #53, but the scroll-extent mutation follows from the popover being an absolutely-positioned child of the scroller. Suggested fix: a measured-height flip or clamp at src/kpress/format/static/js/tooltips.js (the bottom-right/top-right branch of positionTooltip), with a browser assertion that opening and dismissing the preview preserves the scroller's scrollHeight. Horizontal extent was unaffected.
