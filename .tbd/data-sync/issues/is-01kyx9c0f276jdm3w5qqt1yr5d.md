---
type: is
id: is-01kyx9c0f276jdm3w5qqt1yr5d
title: "PR #43 review S3: clarify page-only RenderOptions theme state"
kind: bug
status: closed
priority: 3
version: 3
labels:
  - release-0.3.0
dependencies: []
parent_id: is-01kyx8cq65jqj03gde1081a1ym
created_at: 2026-07-31T23:50:20.897Z
updated_at: 2026-08-01T00:08:46.270Z
closed_at: 2026-08-01T00:08:46.270Z
close_reason: "Fixed in 79f611f, merged through PR #43 as d0379d2, with local and GitHub CI green."
---
Suggestion S3 at src/kpress/format/model.py:110,132. Clarify that RenderOptions.theme_mode and resolved_theme configure standalone page shell/bootstrap state and are ignored by fragment SSR.
