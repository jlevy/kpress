---
type: is
id: is-01kxyxr916p6rmvk9q9zpakcth
title: Goldens and E2E acceptance for collapsible TOC
kind: task
status: closed
priority: 2
version: 3
spec_path: docs/project/specs/active/plan-2026-07-18-collapsible-toc.md
labels: []
dependencies: []
parent_id: is-01kxvtjgzee34yvykhc06e775z
created_at: 2026-07-20T04:50:07.013Z
updated_at: 2026-07-20T06:22:45.690Z
closed_at: 2026-07-20T06:22:45.690Z
close_reason: Golden scenario toc-collapse pinned; Playwright acceptance passing in real Chromium (17c7c04); caught+fixed reduced-motion specificity bug.
---
New golden scenario with toc_collapse_depth: 1 pinning header/button/attribute markup; all existing goldens byte-identical. E2E per docs/kpress-e2e-testing.runbook.md: long-document script covering initial collapsed state, expand-all/collapse-all, scroll-follow group handoff, TOC click into a collapsed section, and reduced-motion emulation applying state without transition. Spec: Testing Strategy.
