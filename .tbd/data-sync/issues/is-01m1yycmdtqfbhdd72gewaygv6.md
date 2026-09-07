---
type: is
id: is-01m1yycmdtqfbhdd72gewaygv6
title: "K53-R1: Greek rows scaled from the wrong source font"
kind: bug
status: closed
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01m1yyca1dg146m92xn73ft93r
created_at: 2026-09-07T22:04:01.338Z
updated_at: 2026-09-07T22:32:02.271Z
closed_at: 2026-09-07T22:32:02.260Z
close_reason: "Fixed on squares/page-fixes; see PR #53 commits 92eb56c / a9b43b1 / 3a3a87f"
resolution: null
duplicate_of: null
---
devtools/katex_text_metrics.py build_tables() supplied each target's own KaTeX table as the Greek source, so Main-Italic and Main-BoldItalic scaled Main-* rows although their composite slots draw KaTeX_Math-Italic and KaTeX_Math-BoldItalic. PR #53.
