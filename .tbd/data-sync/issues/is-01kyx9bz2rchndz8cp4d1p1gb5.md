---
type: is
id: is-01kyx9bz2rchndz8cp4d1p1gb5
title: "PR #43 review R2: document fixed-color page resolver behavior"
kind: bug
status: closed
priority: 3
version: 3
labels:
  - release-0.3.0
dependencies: []
parent_id: is-01kyx8cq65jqj03gde1081a1ym
created_at: 2026-07-31T23:50:19.479Z
updated_at: 2026-08-01T00:08:46.234Z
closed_at: 2026-08-01T00:08:46.234Z
close_reason: "Fixed in 79f611f, merged through PR #43 as d0379d2, with local and GitHub CI green."
---
R2 at src/kpress/format/render.py and docs/releases/0.3.0.md. Fixed-color standalone pages with settings off now include the resolver and write kpress.theme; document the migration and the RenderOptions-level library opt-out without adding an unrequested site-config surface.
