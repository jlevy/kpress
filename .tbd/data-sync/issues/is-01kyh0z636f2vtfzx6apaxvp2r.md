---
type: is
id: is-01kyh0z636f2vtfzx6apaxvp2r
title: KPress v0.2.4 patch release
kind: epic
status: closed
priority: 1
version: 22
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
updated_at: 2026-07-30T19:26:58.724Z
closed_at: 2026-07-30T19:26:58.723Z
close_reason: "KPress v0.2.4 released end to end. PR #35 and issue #33 shipped the intentional alpha identifier migrations and release hardening; PR #34 was closed superseded; exact release commit 9ba160f passed local and main CI/security gates; GitHub release v0.2.4 published through successful Trusted Publishing run 30573667810; the exact registry artifacts passed independent clean-environment verification; PR #36 merged the public closeout ledger and exact-main CI run 30574695542 passed."
---
Ship the current post-v0.2.3 merged delta as KPress v0.2.4: presentation polish, collapsible TOC, document-actions widget, reviewed dependency maintenance, and the intentional alpha migration to pinned GitHub-compatible heading anchors from GitHub issue #33. Release scope excludes the unmerged interactive-footnote-popover feature epic and general roadmap work. Backward compatibility is not maintained for the tracked heading, footnote, and table-identifier migrations: no legacy modes, alias anchors, redirects, dual identifiers, or compatibility attributes. Done means all public and private release blockers are resolved, exact-head main CI and the complete local release gate are green with no unexpected browser skips or dependency advisories, contract and migration notes are accurate, wheel/sdist and clean-room workflows are verified, the GitHub release publishes through PyPI Trusted Publishing, and the registry package passes post-publication smoke tests.

## Notes

RELEASE-CANDIDATE STATUS 2026-07-30: implementation/review branch codex/v0.2.4-release-readiness at 3234dca is pushed as PR #35, mergeable/CLEAN, with no unresolved review threads and all six GitHub checks green. The complete local make verify gate passed again on the exact head with 574 pytest/Playwright tests, 173 Vitest assertions, zero dependency-audit findings, built-distribution inspection, and isolated-wheel smoke. Final engineering review: https://github.com/jlevy/kpress/pull/35#issuecomment-5135079479.

PR #34 is not part of the release and should not merge: it duplicates the PostCSS remediation with version 8.5.23 inside the 14-day cool-off until 2026-08-07T17:05:13Z and conflicts with PR #35's package-lock.json. Review: https://github.com/jlevy/kpress/pull/34#issuecomment-5135079718. Merge PR #35 first, confirm exact-head main CI and advisory state, then close PR #34 as superseded.

Remaining gates are external/stateful: kpr-3bp0 private security sign-off; merge plus exact-head main/alert confirmation for kpr-z52k and final review closure; then kpr-9oue publication and kpr-for5 registry verification. No merge, tag, release, or publication was performed.
