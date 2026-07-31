---
type: is
id: is-01kyx4m3hte3n46jm78r53h0rr
title: Decouple settings controls from theme resolver execution
kind: task
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-07-31-declarative-embedding.md
labels:
  - javascript
  - release-0.3.0
dependencies:
  - type: blocks
    target: is-01kyx4mdm04h6grmnjhj3vtk5e
  - type: blocks
    target: is-01kyx4mdx4esn96svjc5mbbsjd
parent_id: is-01kyx2e4pq85s0fm0vek4ptvye
created_at: 2026-07-31T22:27:23.321Z
updated_at: 2026-07-31T22:27:33.923Z
---
Use red-green checked-JavaScript tests to remove the settings-widget to theme.js execution edge without a dynamic import. Move behavior-neutral toggle binding behind a request event module: standalone theme.js handles the request, while an embedding host can handle it without loading the resolver. Keep the published theme.js toggle export and update the asset dependency graph.
