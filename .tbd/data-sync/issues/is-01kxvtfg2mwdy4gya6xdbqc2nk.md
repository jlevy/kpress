---
type: is
id: is-01kxvtfg2mwdy4gya6xdbqc2nk
title: "PR #25 review R5: server rendering retains stale numeric markers the client removes"
kind: bug
status: open
priority: 2
version: 1
labels: []
dependencies: []
parent_id: is-01kxvtfevrqbqjb0akmd1ac1xj
created_at: 2026-07-18T23:55:10.291Z
updated_at: 2026-07-18T23:55:10.291Z
---
markdown.py:747-767 — finalize only adds markers to numeric columns; authored data-kpress-numeric on mixed columns or span tables survives server-side while tables.js strips it. Normalize every recorded cell: remove then re-add. Python counterparts to JS stale/span tests. (PR https://github.com/jlevy/kpress/pull/25, review comment 5013389312)
