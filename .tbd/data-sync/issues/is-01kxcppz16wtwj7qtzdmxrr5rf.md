---
type: is
id: is-01kxcppz16wtwj7qtzdmxrr5rf
title: Migrate remaining render markup into live templates
kind: task
status: open
priority: 2
version: 3
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-13T03:00:44.197Z
updated_at: 2026-07-13T04:50:00.931Z
---
Move fragment/component HTML currently owned by render.py and markdown.py into strict, pinned, actually-used templates. Switch code and contract tests in the same change; never add dead templates.

## Notes

PR #11 second-review suggestion S1 addressed by raising the live-template migration from P3 to P2 so new renderer markup does not indefinitely widen the gap.
