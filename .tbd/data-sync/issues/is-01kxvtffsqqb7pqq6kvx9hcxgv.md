---
type: is
id: is-01kxvtffsqqb7pqq6kvx9hcxgv
title: "PR #25 review R4: keyboard fragment activation loses native focus-navigation semantics"
kind: bug
status: open
priority: 2
version: 1
labels: []
dependencies: []
parent_id: is-01kxvtfevrqbqjb0akmd1ac1xj
created_at: 2026-07-18T23:55:10.006Z
updated_at: 2026-07-18T23:55:10.006Z
---
history.js:213-221 — pushState+scrollIntoView leaves focus origin at the source link; native navigation moves the sequential-focus start to the target. Focus the target (temporary tabindex, preventScroll) in the owned path. Enter-activation test. (PR https://github.com/jlevy/kpress/pull/25, review comment 5013389312)
