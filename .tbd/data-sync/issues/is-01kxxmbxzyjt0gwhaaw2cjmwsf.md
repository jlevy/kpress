---
type: is
id: is-01kxxmbxzyjt0gwhaaw2cjmwsf
title: "Release v0.2.3: publish GitHub release and verify external package"
kind: task
status: open
priority: 1
version: 2
labels: []
dependencies: []
created_at: 2026-07-19T16:46:50.878Z
updated_at: 2026-07-19T17:36:15.193Z
---
Patch release v0.2.3 (history-aware section navigation, structural TOC tree normalization, column-scoped numeric table alignment, TOC toggle clearance, print margin alignment, tooling consolidation). Pre-release review done, make verify green (540 pytest + 145 vitest, audits clean), release notes in docs/releases/0.2.3.md, version refs rolled. Remaining: publish the GitHub release with tag v0.2.3 (fires publish.yml trusted publishing), then verify externally per docs/publishing.md steps 7-8: uvx --from kpress==0.2.3 kpress --version / --help / doctor, README quickstart against PyPI, project page metadata.

## Notes

Release prep landed: PR #26 merged to main as 77bfd7c, main CI green. Local make verify green on the release commit (540 pytest incl. real-browser history+clearance smokes, 145 vitest, audits clean, distribution checks + clean-room wheel smoke). Tag push from the remote session was blocked (403; env push access is branch-scoped), so create the tag at release time: publish the GitHub release with NEW tag v0.2.3 targeting main (77bfd7c). publish.yml then runs make verify on the tag, checks version==0.2.3, and uploads via trusted publishing. After that: docs/publishing.md steps 7-8 (uvx --from kpress==0.2.3 kpress --version/--help/doctor, README quickstart, project-page metadata), then close this bead.
