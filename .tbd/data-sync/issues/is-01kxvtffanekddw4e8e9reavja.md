---
type: is
id: is-01kxvtffanekddw4e8e9reavja
title: "PR #25 review R2: re-clicking the current fragment creates duplicate history entries"
kind: bug
status: closed
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01kxvtfevrqbqjb0akmd1ac1xj
created_at: 2026-07-18T23:55:09.524Z
updated_at: 2026-07-19T00:04:18.587Z
closed_at: 2026-07-19T00:04:18.586Z
close_reason: "In 0fac777. R2 fixed: same-URL re-activation skips pushState, scroll only; vitest spy test + history.length probe in browser smoke"
---
history.js:209-214 — every owned click pushes an entry even when destination URL equals location.href; native Chrome does not push on re-click. Skip pushState for same-URL activation, still scroll. Cover in vitest + browser smoke. (PR https://github.com/jlevy/kpress/pull/25, review comment 5013389312)
