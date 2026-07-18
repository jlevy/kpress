---
type: is
id: is-01kxvqmm4nt009pa0wnfway5ed
title: "Table numeric alignment: column-scoped detection + typographic minus"
kind: bug
status: open
priority: 1
version: 1
labels: []
dependencies: []
created_at: 2026-07-18T23:05:32.564Z
updated_at: 2026-07-18T23:05:32.564Z
---
Two defects in numeric table-cell alignment (data-kpress-numeric), reported from finterm-site rendering:

1. The numeric-cell patterns (Python _NUMERIC_CELL_RE in format/markdown.py and JS NUMERIC_CELL_PATTERN in static/js/tables.js) only accept ASCII '-'/'+' signs, so a typographic minus U+2212 ('−35%') is not detected and stays left-aligned while '+45%' in the same column right-aligns.

2. Detection is per-cell, so mixed columns end up with mixed alignment. Alignment should be column-scoped: a column is numeric only if all non-empty body (td) cells are numeric (empty cells don't disqualify); then every cell in the column (incl. header) is marked. Otherwise no cell in the column is marked (default left align).

Fix both the Python renderer and the JS runtime identically; also unify the two patterns (JS lacks currency symbols and leading-dot decimals that Python accepts). Update tests, kpress-design.md, and goldens as needed.
