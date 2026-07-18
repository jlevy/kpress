---
type: is
id: is-01kxvtffanekddw4e8e9reavja
title: "PR #25 review R2: re-clicking the current fragment creates duplicate history entries"
kind: bug
status: open
priority: 2
version: 1
labels: []
dependencies: []
parent_id: is-01kxvtfevrqbqjb0akmd1ac1xj
created_at: 2026-07-18T23:55:09.524Z
updated_at: 2026-07-18T23:55:09.524Z
---
history.js:209-214 — every owned click pushes an entry even when destination URL equals location.href; native Chrome does not push on re-click. Skip pushState for same-URL activation, still scroll. Cover in vitest + browser smoke. (PR https://github.com/jlevy/kpress/pull/25, review comment 5013389312)
