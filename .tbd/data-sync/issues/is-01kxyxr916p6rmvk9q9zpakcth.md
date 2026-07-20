---
type: is
id: is-01kxyxr916p6rmvk9q9zpakcth
title: Goldens and E2E acceptance for collapsible TOC
kind: task
status: open
priority: 2
version: 1
spec_path: docs/project/specs/active/plan-2026-07-18-collapsible-toc.md
labels: []
dependencies: []
parent_id: is-01kxvtjgzee34yvykhc06e775z
created_at: 2026-07-20T04:50:07.013Z
updated_at: 2026-07-20T04:50:07.013Z
---
New golden scenario with toc_collapse_depth: 1 pinning header/button/attribute markup; all existing goldens byte-identical. E2E per docs/kpress-e2e-testing.runbook.md: long-document script covering initial collapsed state, expand-all/collapse-all, scroll-follow group handoff, TOC click into a collapsed section, and reduced-motion emulation applying state without transition. Spec: Testing Strategy.
