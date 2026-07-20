---
type: is
id: is-01kxyxr8kj6s9ev21asbwbpehg
title: "Server markup: _render_toc header row, expand-all button, data attributes, contract classes, CSS"
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-07-18-collapsible-toc.md
labels: []
dependencies:
  - type: blocks
    target: is-01kxyxr8tdmjyw82spkp5ktzgy
parent_id: is-01kxvtjgzee34yvykhc06e775z
created_at: 2026-07-20T04:50:06.577Z
updated_at: 2026-07-20T04:50:14.829Z
---
When toc_collapse_depth is set AND at least one entry is deeper: render kpress-toc-header wrapping the title link plus the kpress-toc-expand-all button (both sprite icons, aria-expanded, aria-label), and data-kpress-toc-collapse-depth / data-kpress-toc-expand-on-scroll on the nav. Off or nothing-collapsible => byte-identical output. Register kpress-toc-header, kpress-toc-expand-all, kpress-toc-collapsed in contract.py PUBLIC_CSS_CLASSES. CSS in components.css: header flex row, quiet icon button keyed off aria-expanded, kpress-toc-collapsed row-close motion with standard tokens and reduced-motion suppression. pytest render-gate unit tests. Spec: Design > Server markup, CSS.
