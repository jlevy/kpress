---
type: is
id: is-01kyx2e4pq85s0fm0vek4ptvye
title: "Make fragment theme assets host-safe (GitHub issue #42)"
kind: bug
status: closed
priority: 1
version: 9
spec_path: docs/done/declarative-embedding.plan.md
labels:
  - release-0.3.0
dependencies: []
parent_id: is-01kytxza2a4r789k649dzrantj
child_order_hints:
  - is-01kyx4m399r7ezw7gtp716g504
  - is-01kyx4m3hte3n46jm78r53h0rr
  - is-01kyx4mdm04h6grmnjhj3vtk5e
  - is-01kyx4mdx4esn96svjc5mbbsjd
  - is-01kyx4mmt246scpm3vebrpf1ca
created_at: 2026-07-31T21:49:10.737Z
updated_at: 2026-07-31T23:28:39.803Z
closed_at: 2026-07-31T23:28:39.802Z
close_reason: "Fixed #42 by making automatic fragment assets host-owned, removing the settings-to-resolver import edge, adding explicit resolver opt-in, removing inert dynamic theme fields, and proving default/opt-in behavior in Python, DOM, and real Chromium."
---
Default fragment manifests can execute the standalone kpress theme resolver: theme.js is an entry point for system mode, and settings-widget.js statically imports it even when a host filters that entry point. This reintroduces a competing root-theme writer in embedded hosts. Before v0.3.0, make fragment defaults safe for host-owned theme state, make settings/theme coupling lazy or explicitly opted in, correct the dynamic-render and embedding docs, and add a browser regression proving that loading default fragment assets does not mutate the host root theme. Tracks https://github.com/jlevy/kpress/issues/42.
