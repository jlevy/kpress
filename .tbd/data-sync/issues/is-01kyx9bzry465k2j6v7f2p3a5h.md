---
type: is
id: is-01kyx9bzry465k2j6v7f2p3a5h
title: "PR #43 review R5: ignore malformed theme requests"
kind: bug
status: closed
priority: 3
version: 3
labels:
  - release-0.3.0
dependencies: []
parent_id: is-01kyx8cq65jqj03gde1081a1ym
created_at: 2026-07-31T23:50:20.189Z
updated_at: 2026-08-01T00:08:46.252Z
closed_at: 2026-08-01T00:08:46.252Z
close_reason: "Fixed in 79f611f, merged through PR #43 as d0379d2, with local and GitHub CI green."
---
R5 at src/kpress/format/static/js/theme.js:121-125. Add a regression proving a malformed theme:request does not reset persisted mode, then ignore requests whose mode is not a string.
