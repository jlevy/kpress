---
type: is
id: is-01kxvtfga7q2dqt24vca0g579p
title: "PR #25 review R6: malformed fragments can throw in the new click path"
kind: bug
status: open
priority: 2
version: 1
labels: []
dependencies: []
parent_id: is-01kxvtfevrqbqjb0akmd1ac1xj
created_at: 2026-07-18T23:55:10.534Z
updated_at: 2026-07-18T23:55:10.534Z
---
history.js:209 — owned clicks call decodeURIComponent directly; href='#%' raises URIError. Reuse guarded fragmentId(). Malformed-fragment test. (PR https://github.com/jlevy/kpress/pull/25, review comment 5013389312)
