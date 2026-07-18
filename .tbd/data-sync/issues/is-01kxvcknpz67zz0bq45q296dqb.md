---
type: is
id: is-01kxvcknpz67zz0bq45q296dqb
title: Implement transient previews and pinned footnote popovers
kind: feature
status: open
priority: 1
version: 4
spec_path: docs/interactive-footnote-popovers.plan.md
labels:
  - reader
  - accessibility
dependencies:
  - type: blocks
    target: is-01kxvckp2hyaa03nak10yn2th5
  - type: blocks
    target: is-01kxvckpmfv1cgt5dgec07bn10
  - type: blocks
    target: is-01kxvckpx9wqdk9ek3b3jsv2zc
parent_id: is-01kxvck45rk5eya2jnm8spmr1v
created_at: 2026-07-18T19:52:47.068Z
updated_at: 2026-07-18T19:53:08.868Z
---
Split the footnote-preview behavior into descriptive transient and interactive pinned states with correct activation, dismissal, focus, and native fallback.
