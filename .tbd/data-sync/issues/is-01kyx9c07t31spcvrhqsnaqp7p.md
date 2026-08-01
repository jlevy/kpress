---
type: is
id: is-01kyx9c07t31spcvrhqsnaqp7p
title: "PR #43 review S2: explain singleton theme-change listener"
kind: bug
status: closed
priority: 3
version: 3
labels:
  - release-0.3.0
dependencies: []
parent_id: is-01kyx8cq65jqj03gde1081a1ym
created_at: 2026-07-31T23:50:20.665Z
updated_at: 2026-08-01T00:08:46.264Z
closed_at: 2026-08-01T00:08:46.264Z
close_reason: "Fixed in 79f611f, merged through PR #43 as d0379d2, with local and GitHub CI green."
---
Suggestion S2 at src/kpress/format/static/js/theme-controls.js. Add a concise production comment explaining why the module-level theme:change listener intentionally lives for the singleton module lifetime.
