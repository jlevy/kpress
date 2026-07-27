---
type: is
id: is-01kyh0z636f2vtfzx6apaxvp2r
title: KPress v0.2.4 patch release
kind: epic
status: open
priority: 1
version: 20
spec_path: docs/publishing.md
labels:
  - release
  - v0.2.4
  - breaking-alpha
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
child_order_hints:
  - is-01kyh110evqk49r4m30vz1xvac
  - is-01kyh110q16d1dfmhvzarfbzs5
  - is-01ky150q341w6skb6esanebvct
  - is-01ky150qddmda8kaqethhf0tk1
  - is-01ky150qnmvj0p0p5w88feytvv
  - is-01ky150qyjtw9f6ypdm4kcsqvm
  - is-01kyh1118c3xsmapj9d3bv74az
  - is-01kyh111g7g982p1der5dyxsz5
  - is-01kyh111r6095nckxsmz94wddt
  - is-01kyh110ytpdk145h3m87y0241
  - is-01ky150r6vegs67zh623tnwy7j
  - is-01kyh11209n4en189vpa2ag5b9
  - is-01kyh1128faa021b48wxd17zzr
  - is-01kyh1kdvsza3f2qy8cfhhktc5
  - is-01kyh5xswebfjx97t88cnab498
created_at: 2026-07-27T05:32:38.885Z
updated_at: 2026-07-27T06:59:16.493Z
---
Ship the current post-v0.2.3 merged delta as KPress v0.2.4: presentation polish, collapsible TOC, document-actions widget, reviewed dependency maintenance, and the intentional alpha migration to pinned GitHub-compatible heading anchors from GitHub issue #33. Release scope excludes the unmerged interactive-footnote-popover feature epic and general roadmap work. Backward compatibility is not maintained for the tracked heading, footnote, and table-identifier migrations: no legacy modes, alias anchors, redirects, dual identifiers, or compatibility attributes. Done means all public and private release blockers are resolved, exact-head main CI and the complete local release gate are green with no unexpected browser skips or dependency advisories, contract and migration notes are accurate, wheel/sdist and clean-room workflows are verified, the GitHub release publishes through PyPI Trusted Publishing, and the registry package passes post-publication smoke tests.

## Notes

RELEASE-CANDIDATE STATUS 2026-07-27: implementation/review branch codex/v0.2.4-release-readiness at 4c8a713 is pushed as PR #35, mergeable/CLEAN. Canonical local make verify and GitHub lint, distribution, Python 3.12, 3.13, and 3.14 CI are green. Issue #33 migration and all implementation, documentation, validation, and artifact child beads are closed. Remaining gates are intentionally external/stateful: kpr-3bp0 private security sign-off; merge plus exact-head main/alert confirmation for kpr-z52k and final review closure; then kpr-9oue publication and kpr-for5 registry verification. No tag, merge, release, or publication was performed.
