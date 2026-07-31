---
type: is
id: is-01kyx4mdx4esn96svjc5mbbsjd
title: Reconcile embedding contracts and v0.3.0 migration guidance
kind: task
status: closed
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-07-31-declarative-embedding.md
labels:
  - docs
  - release-0.3.0
dependencies:
  - type: blocks
    target: is-01kyx4mmt246scpm3vebrpf1ca
parent_id: is-01kyx2e4pq85s0fm0vek4ptvye
created_at: 2026-07-31T22:27:33.923Z
updated_at: 2026-07-31T23:07:40.768Z
closed_at: 2026-07-31T23:07:40.767Z
close_reason: Pinned the public runtime-event contract; reconciled design, dynamic host, integration skill, and v0.3.0 migration docs with host-owned fragment defaults and explicit resolver opt-in; corrected pre-alpha color-hook history; lint and 92 focused tests pass.
---
Update the design, operations guide, shipped using-kpress skill, public contract notes, and 0.3.0 release notes to describe safe fragment defaults, explicit resolver opt-in, the theme-request event, and the dynamic API break. Remove the stale dual-attribute and impossible do-not-load-theme.js guidance. Correct the legacy color-hook note: those hooks have never affected a public release.
