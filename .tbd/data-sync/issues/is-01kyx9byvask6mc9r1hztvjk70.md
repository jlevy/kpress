---
type: is
id: is-01kyx9byvask6mc9r1hztvjk70
title: "PR #43 review R1: remove theme-controls compatibility re-export"
kind: bug
status: closed
priority: 2
version: 3
labels:
  - release-0.3.0
dependencies: []
parent_id: is-01kyx8cq65jqj03gde1081a1ym
created_at: 2026-07-31T23:50:19.241Z
updated_at: 2026-08-01T00:08:46.220Z
closed_at: 2026-08-01T00:08:46.216Z
close_reason: "Fixed in 79f611f, merged through PR #43 as d0379d2, with local and GitHub CI green."
---
R1 at src/kpress/format/static/js/theme.js:24 and src/kpress/contract.py:485. Hard-cut the bindThemeToggleControls re-export from theme.js, remove that module's export pin while retaining theme-controls.js, keep the contract scanner strict, and document the import-path migration in v0.3.0 notes.
