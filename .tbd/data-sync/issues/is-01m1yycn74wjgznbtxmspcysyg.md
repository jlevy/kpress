---
type: is
id: is-01m1yycn74wjgznbtxmspcysyg
title: "K53-R3: font chooser leaves rendered math in the previous mode"
kind: bug
status: closed
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01m1yyca1dg146m92xn73ft93r
created_at: 2026-09-07T22:04:02.147Z
updated_at: 2026-09-07T22:32:04.455Z
closed_at: 2026-09-07T22:32:04.453Z
close_reason: "Fixed on squares/page-fixes; see PR #53 commits 92eb56c / a9b43b1 / 3a3a87f"
resolution: null
duplicate_of: null
---
src/kpress/format/static/js/settings-widget.js applyFontSet switched CSS but katex-init.js never rebuilt the metric tables or the rendered math. PR #53.
