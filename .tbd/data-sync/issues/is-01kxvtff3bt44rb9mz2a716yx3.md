---
type: is
id: is-01kxvtff3bt44rb9mz2a716yx3
title: "PR #25 review R1: phone breakpoint overrides the new TOC clearance"
kind: bug
status: in_progress
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01kxvtfevrqbqjb0akmd1ac1xj
created_at: 2026-07-18T23:55:09.290Z
updated_at: 2026-07-18T23:55:17.268Z
---
components.css:1619,1714 — max-width:47.99rem rule resets padding-inline to 0.5rem, same specificity, defeating the clearance at phone widths. Make the mobile rule clearance-aware and add width regression coverage. (PR https://github.com/jlevy/kpress/pull/25, review comment 5013389312)
