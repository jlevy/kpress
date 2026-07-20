---
type: is
id: is-01kxyy68asmy3qb7x8ke6kadmz
title: "PR #29 review K1: client runtime overwrites custom wide-table thresholds"
kind: bug
status: closed
priority: 1
version: 3
labels: []
dependencies: []
parent_id: is-01kxyy5396ecjd4hqyvh1aggpc
created_at: 2026-07-20T04:57:45.047Z
updated_at: 2026-07-20T05:03:25.333Z
closed_at: 2026-07-20T05:03:25.332Z
close_reason: "Fixed: server stamps resolved cutoff on article root; tables.js resolves per table (explicit config > stamps > defaults); tests added"
---
High. src/kpress/format/static/js/tables.js:124-139, src/kpress/format/render.py:194-195, src/kpress/publish/config.py:581-582. initKpressTables() re-classifies every .kpress-table with hard-coded 6/100 defaults, clobbering server-rendered marks produced under custom RenderOptions/kpress.yml thresholds. Fix: one source of truth — serialize resolved thresholds into the document, client uses them by default, explicit runtime override wins. Add integration test with non-default thresholds. From https://github.com/jlevy/kpress/pull/29#issuecomment-5018906119
