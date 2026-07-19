---
type: is
id: is-01kxxmbxzyjt0gwhaaw2cjmwsf
title: "Release v0.2.3: publish GitHub release and verify external package"
kind: task
status: open
priority: 1
version: 1
labels: []
dependencies: []
created_at: 2026-07-19T16:46:50.878Z
updated_at: 2026-07-19T16:46:50.878Z
---
Patch release v0.2.3 (history-aware section navigation, structural TOC tree normalization, column-scoped numeric table alignment, TOC toggle clearance, print margin alignment, tooling consolidation). Pre-release review done, make verify green (540 pytest + 145 vitest, audits clean), release notes in docs/releases/0.2.3.md, version refs rolled. Remaining: publish the GitHub release with tag v0.2.3 (fires publish.yml trusted publishing), then verify externally per docs/publishing.md steps 7-8: uvx --from kpress==0.2.3 kpress --version / --help / doctor, README quickstart against PyPI, project page metadata.
