---
type: is
id: is-01kyty8qwmms8t029r8xs6ya1k
title: Theming embedder-contract docs and changelog
kind: task
status: closed
priority: 2
version: 5
spec_path: docs/done/declarative-embedding.plan.md
labels: []
dependencies: []
parent_id: is-01kytxza2a4r789k649dzrantj
created_at: 2026-07-31T01:57:50.612Z
updated_at: 2026-07-31T23:21:06.595Z
closed_at: 2026-07-31T02:45:39.981Z
close_reason: "Theming embedder contract documented across design/host/skill docs; 0.3.0 migration table added; spec record corrected per PR #40 review; cache-key fix landed separately (cb752ca)."
---
Document the embedder theming contract per the spec: stamp data-kpress-resolved-theme on one chosen scope and update it on toggle, nothing else; do not load theme.js (or no-op override the theme behavior if assets include it); element-over-ancestor precedence rule; SSR outputs are theme-agnostic and cacheable. Update kpress-design.md, kpress-operations-and-host-integration.md, the using-kpress skill, and the changelog (migration lines for element-stamping hosts).
