---
type: is
id: is-01kxe5fsycffktg2g4jmw6nxm9
title: Make golden fixtures readable and reviewable
kind: task
status: closed
priority: 1
version: 3
labels:
  - testing
  - golden
dependencies: []
created_at: 2026-07-13T16:38:12.683Z
updated_at: 2026-07-13T16:59:11.833Z
closed_at: 2026-07-13T16:59:11.833Z
close_reason: "Replaced opaque JSON golden trees with compact frontmatter-format YAML, consolidated the mode scenario, documented updates, and confirmed PR #13 CI is green."
---
Replace the opaque JSON golden tree artifacts introduced before/through PR #12 with concise deterministic YAML written through frontmatter-format conventions. Preserve broad behavioral visibility while making multiline content and diffs transparent; keep the harness simple, selective regeneration deliberate, and tests/documentation clear.
