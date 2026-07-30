---
type: is
id: is-01kyh110evqk49r4m30vz1xvac
title: Restore green main by remediating the PostCSS advisory
kind: bug
status: in_progress
priority: 0
version: 12
spec_path: docs/publishing.md
labels:
  - release
  - security
  - dependencies
  - ci
dependencies:
  - type: blocks
    target: is-01kyh1118c3xsmapj9d3bv74az
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
created_at: 2026-07-27T05:33:38.651Z
updated_at: 2026-07-30T19:02:25.228Z
---
Current main d1f014f fails the required npm audit because PostCSS 8.5.16 is affected by GHSA-r28c-9q8g-f849. PR #35 remediates the advisory with PostCSS 8.5.18, the oldest patched version that satisfies the repository's 14-day dependency cool-off, and passes the complete local release gate plus all PR checks. PR #34 is superseded: its PostCSS 8.5.23 pin remains inside the cool-off until 2026-08-07T17:05:13Z, duplicates the remediation, and conflicts with PR #35's lockfile. Done means PR #35 is merged, exact-head main CI and npm audit are green, the repository advisory state confirms remediation, and PR #34 is closed without merging.

## Notes

IMPLEMENTED in release-candidate commits 4c8a713 and 3234dca / PR #35: package-lock.json pins transitive PostCSS exactly 8.5.18 with nanoid 3.3.15. Local make verify passed again on 2026-07-30; all PR lint/distribution/Python 3.12-3.14/Cursor checks are green, and npm audit reports zero vulnerabilities. The 8.5.18 release is the oldest patched version outside the 14-day cool-off.

PR #34 was re-reviewed on 2026-07-30 and must not merge before v0.2.4. Its PostCSS 8.5.23 pin was published 2026-07-24T17:05:13Z and remains inside the 14-day cool-off until 2026-08-07T17:05:13Z; it duplicates the remediation in PR #35 and a combined merge-tree simulation conflicts in package-lock.json. Review: https://github.com/jlevy/kpress/pull/34#issuecomment-5135079718. After PR #35 merges and exact-head main CI/advisory state confirms remediation, close PR #34 as superseded and close this bead.
