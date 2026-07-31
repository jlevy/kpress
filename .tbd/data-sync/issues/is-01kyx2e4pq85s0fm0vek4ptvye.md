---
type: is
id: is-01kyx2e4pq85s0fm0vek4ptvye
title: "Make fragment theme assets host-safe (GitHub issue #42)"
kind: bug
status: open
priority: 1
version: 1
spec_path: docs/project/specs/active/plan-2026-07-31-declarative-embedding.md
labels:
  - release-0.3.0
dependencies: []
parent_id: is-01kytxza2a4r789k649dzrantj
created_at: 2026-07-31T21:49:10.737Z
updated_at: 2026-07-31T21:49:10.737Z
---
Default fragment manifests can execute the standalone kpress theme resolver: theme.js is an entry point for system mode, and settings-widget.js statically imports it even when a host filters that entry point. This reintroduces a competing root-theme writer in embedded hosts. Before v0.3.0, make fragment defaults safe for host-owned theme state, make settings/theme coupling lazy or explicitly opted in, correct the dynamic-render and embedding docs, and add a browser regression proving that loading default fragment assets does not mutate the host root theme. Tracks https://github.com/jlevy/kpress/issues/42.
