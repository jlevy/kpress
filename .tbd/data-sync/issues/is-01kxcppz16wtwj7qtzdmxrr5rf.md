---
type: is
id: is-01kxcppz16wtwj7qtzdmxrr5rf
title: Migrate remaining render markup into live templates
kind: task
status: open
priority: 3
version: 1
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-13T03:00:44.197Z
updated_at: 2026-07-13T03:00:44.197Z
---
Move fragment/component HTML currently owned by render.py and markdown.py into strict, pinned, actually-used templates. Switch code and contract tests in the same change; never add dead templates.
