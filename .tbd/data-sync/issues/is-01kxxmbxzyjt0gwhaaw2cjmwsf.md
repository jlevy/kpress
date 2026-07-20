---
type: is
id: is-01kxxmbxzyjt0gwhaaw2cjmwsf
title: "Release v0.2.3: publish GitHub release and verify external package"
kind: task
status: closed
priority: 1
version: 4
labels: []
dependencies: []
created_at: 2026-07-19T16:46:50.878Z
updated_at: 2026-07-19T18:05:46.760Z
closed_at: 2026-07-19T18:05:46.757Z
close_reason: "Released and verified. GitHub release v0.2.3 published at 77bfd7c (gh CLI per tbd setup-github-cli proxied-session flow); publish.yml green: full release gate, tag/version check, trusted publishing upload. External verification from the registry: kpress --version reports 0.2.3; --help and doctor healthy (optimizer/brotli/pdf show expected optional skips); README-style quickstart build succeeds and ships js/history.js + js/toc.js; PyPI metadata correct (AGPL-3.0-or-later, py3.12-3.14 classifiers, repo/issue links, wheel+sdist)."
---
Patch release v0.2.3 (history-aware section navigation, structural TOC tree normalization, column-scoped numeric table alignment, TOC toggle clearance, print margin alignment, tooling consolidation). Pre-release review done, make verify green (540 pytest + 145 vitest, audits clean), release notes in docs/releases/0.2.3.md, version refs rolled. Remaining: publish the GitHub release with tag v0.2.3 (fires publish.yml trusted publishing), then verify externally per docs/publishing.md steps 7-8: uvx --from kpress==0.2.3 kpress --version / --help / doctor, README quickstart against PyPI, project page metadata.

## Notes

Release prep merged: PR #26 -> main 77bfd7c369cdc65f7b31778d89eb4b51f354fa73 (the verified release commit; make verify green there: 540 pytest incl. real-browser smokes, 145 vitest, audits clean, clean-room wheel). PR #27 (tbd 0.4.1 pin) will move main past it, so the release MUST pin the target commit: gh release create v0.2.3 --target 77bfd7c369cdc65f7b31778d89eb4b51f354fa73 --title 'KPress 0.2.3' --notes-file docs/releases/0.2.3.md (title/body convention matches v0.2.2: name 'KPress X.Y.Z', body = release-notes file verbatim). In-session publication is impossible: no MCP release tool; sandbox GitHub API egress returns policy 403 ('GitHub access is not enabled for this session'); tag pushes 403 (branch-scoped). After publication: verify per docs/publishing.md steps 7-8, then close this bead.
