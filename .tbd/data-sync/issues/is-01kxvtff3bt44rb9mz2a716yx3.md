---
type: is
id: is-01kxvtff3bt44rb9mz2a716yx3
title: "PR #25 review R1: phone breakpoint overrides the new TOC clearance"
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01kxvtfevrqbqjb0akmd1ac1xj
created_at: 2026-07-18T23:55:09.290Z
updated_at: 2026-07-19T00:04:18.392Z
closed_at: 2026-07-19T00:04:18.391Z
close_reason: "In 0fac777. R1 fixed: phone-band rule made clearance-aware; playwright computed-style regression at 390px/900px, verified red on old CSS"
---
components.css:1619,1714 — max-width:47.99rem rule resets padding-inline to 0.5rem, same specificity, defeating the clearance at phone widths. Make the mobile rule clearance-aware and add width regression coverage. (PR https://github.com/jlevy/kpress/pull/25, review comment 5013389312)
