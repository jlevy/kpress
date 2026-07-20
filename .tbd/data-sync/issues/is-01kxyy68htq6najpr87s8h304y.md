---
type: is
id: is-01kxyy68htq6najpr87s8h304y
title: "PR #29 review K2: wide tables spill outside embedded panes when TOC absent"
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01kxyy5396ecjd4hqyvh1aggpc
created_at: 2026-07-20T04:57:45.273Z
updated_at: 2026-07-20T05:09:36.204Z
closed_at: 2026-07-20T05:09:36.203Z
close_reason: "Fixed: base wide-table bleed now pane-relative (100cqw); browser test pins the no-TOC narrow-pane case (red on old CSS). Note: spill requires host-widened --kpress-measure; stock tokens cap below any wide-band pane."
---
Medium. src/kpress/format/static/css/components.css:718-722,1610-1622. Wide-breakpoint container-relative reset only exists under has-toc selectors; no-TOC embedded docs keep base left:50%/translateX(-50%)/100vw and spill past pane edges. Fix: container-relative base geometry or equal-specificity no-TOC reset (100cqw). Add browser test. From PR #29 review.
