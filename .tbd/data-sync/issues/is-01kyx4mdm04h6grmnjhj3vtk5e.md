---
type: is
id: is-01kyx4mdm04h6grmnjhj3vtk5e
title: Prove fragment assets never take host theme ownership
kind: task
status: closed
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-07-31-declarative-embedding.md
labels:
  - testing
  - release-0.3.0
dependencies:
  - type: blocks
    target: is-01kyx4mmt246scpm3vebrpf1ca
parent_id: is-01kyx2e4pq85s0fm0vek4ptvye
created_at: 2026-07-31T22:27:33.631Z
updated_at: 2026-07-31T22:59:37.168Z
closed_at: 2026-07-31T22:59:37.163Z
close_reason: Added a real-Chromium late-load regression covering every selected fragment module, host-owned root/storage/OS-listener invariants, settings theme:request, and explicit resolver opt-in; targeted browser and static checks pass.
---
Add the smallest deterministic regression matrix across Python manifests and the real browser lifecycle. Loading every entry point from a default auto fragment after ready must not register or run the theme resolver, read KPress theme storage, bind OS color-scheme listeners, or mutate host-stamped root theme attributes. Explicit resolver opt-in and standalone pages must retain their behavior.
