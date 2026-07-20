---
type: is
id: is-01kxyy68rv38d55bat6vc788cm
title: "PR #29 review K3: interactive tooltip content not keyboard operable"
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01kxyy5396ecjd4hqyvh1aggpc
created_at: 2026-07-20T04:57:45.498Z
updated_at: 2026-07-20T05:13:12.960Z
closed_at: 2026-07-20T05:13:12.959Z
close_reason: "Fixed via option (a): keyboard activation (click detail 0) keeps native navigation to the in-document footnote and dismisses the preview; pointer clicks still open it. DOM + real-browser keyboard tests added (red pre-fix)."
---
Medium. src/kpress/format/static/js/tooltips.js:526-557,672-678. Tooltip surface clickable with real links inside, but container is unfocusable role=tooltip; blur on source anchor removes tooltip so inner links can't be reached by keyboard; click-anywhere preview is pointer-only. Fix (pick one): noninteractive tooltip w/ navigation via focusable trigger, or focus-managed popover pattern. Add keyboard test. From PR #29 review.
