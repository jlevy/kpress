---
type: is
id: is-01m1yycmsqe0rccmsjjgs5arez
title: "K53-R2: .textrm suppresses explicit nested italics"
kind: bug
status: closed
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01m1yyca1dg146m92xn73ft93r
created_at: 2026-09-07T22:04:01.718Z
updated_at: 2026-09-07T22:32:03.298Z
closed_at: 2026-09-07T22:32:03.296Z
close_reason: "Fixed on squares/page-fixes; see PR #53 commits 92eb56c / a9b43b1 / 3a3a87f"
resolution: null
duplicate_of: null
---
src/kpress/format/static/katex/katex-text-face.css set font-style: normal on .textrm, outranking upstream .textit for the single .mord.textrm.textit leaf KaTeX emits. PR #53.
