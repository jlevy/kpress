---
type: is
id: is-01m1yycnmv23qkqsd5q7dd91kk
title: "K53-R4: footnote previews lose their math font context"
kind: bug
status: closed
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01m1yyca1dg146m92xn73ft93r
created_at: 2026-09-07T22:04:02.586Z
updated_at: 2026-09-07T22:32:05.661Z
closed_at: 2026-09-07T22:32:05.660Z
close_reason: "Fixed on squares/page-fixes; see PR #53 commits 92eb56c / a9b43b1 / 3a3a87f"
resolution: null
duplicate_of: null
---
src/kpress/format/static/js/tooltips.js mounts previews outside .kpress, so the composite family and size rules in katex-text-face.css stopped applying to cloned math. PR #53.
