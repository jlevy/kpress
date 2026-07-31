---
type: is
id: is-01kyx4mmt246scpm3vebrpf1ca
title: Finish v0.3.0 release preparation and downstream validation
kind: task
status: in_progress
priority: 1
version: 4
spec_path: docs/done/declarative-embedding.plan.md
labels:
  - release-0.3.0
dependencies: []
parent_id: is-01kyx2e4pq85s0fm0vek4ptvye
created_at: 2026-07-31T22:27:40.993Z
updated_at: 2026-07-31T23:21:05.533Z
---
Update README, installation, TODO, and declarative-embedding plan state for v0.3.0; close completed parent beads and move the finished plan to docs/done. Run the full kpress release gate, install the exact source commit into metabrowser without changing its locked release pin, run its full suite and targeted browser integration, then publish a reviewed PR with green CI. Tagging and PyPI publication remain a separate explicit release action.
