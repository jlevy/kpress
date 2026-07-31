---
type: is
id: is-01kyty8pj56bv51ej8mjr3c2wn
title: "Theme selector overhaul: symmetric forms, co-located color-scheme"
kind: task
status: closed
priority: 1
version: 8
spec_path: docs/done/declarative-embedding.plan.md
labels: []
dependencies:
  - type: blocks
    target: is-01kyty8pwqgtgwprxy3p2p2hnc
  - type: blocks
    target: is-01kyty8q78gkqp1y8e7pz8rcn4
  - type: blocks
    target: is-01kyty8qj1bwn65xtzahcbv0rf
  - type: blocks
    target: is-01kyty8qwmms8t029r8xs6ya1k
parent_id: is-01kytxza2a4r789k649dzrantj
created_at: 2026-07-31T01:57:49.253Z
updated_at: 2026-07-31T23:21:02.389Z
closed_at: 2026-07-31T02:28:04.951Z
close_reason: Symmetric two-scope selector grammar in style-tokens + syntax.css, color-scheme co-located, theme css files folded/deleted, pins + goldens updated; full suite and lint gate green.
---
Rewrite the palette x theme selector matrix in style-tokens.css to exactly two symmetric forms per state per the spec Design: ancestor form :where([data-kpress-resolved-theme=dark]) :is(.kpress, .kpress-page-main, .kpress-tooltip) at (0,1,0) ordered after the unkeyed light defaults, and element form :is(...)[data-kpress-resolved-theme=dark] at (0,2,0); light gets identical twins. Element wins over ancestor. Apply the same two-form treatment to the warm palette blocks (palette x theme combos). Declare color-scheme inside the same rules; delete theme-light.css and theme-dark.css and their asset-manifest entries. data-kpress-theme (mode) disappears from all CSS. Update test_asset_contract.py pinned strings; regenerate goldens.
