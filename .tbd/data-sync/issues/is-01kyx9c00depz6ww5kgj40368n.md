---
type: is
id: is-01kyx9c00depz6ww5kgj40368n
title: "PR #43 review S1: remove duplicate theme-control synchronization"
kind: bug
status: closed
priority: 3
version: 3
labels:
  - release-0.3.0
dependencies: []
parent_id: is-01kyx8cq65jqj03gde1081a1ym
created_at: 2026-07-31T23:50:20.427Z
updated_at: 2026-08-01T00:08:46.258Z
closed_at: 2026-08-01T00:08:46.258Z
close_reason: "Fixed in 79f611f, merged through PR #43 as d0379d2, with local and GitHub CI green."
---
Suggestion S1 at src/kpress/format/static/js/theme.js setKpressTheme. Remove the direct syncThemeControls pass and retain the theme:change listener as the single synchronization path, with tests.
