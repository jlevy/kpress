---
type: is
id: is-01kyh110evqk49r4m30vz1xvac
title: Restore green main by remediating the PostCSS advisory
kind: bug
status: in_progress
priority: 0
version: 9
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
updated_at: 2026-07-27T06:47:50.098Z
---
Current main d1f014f fails the required npm audit because postcss 8.5.16 is affected by GHSA-r28c-9q8g-f849. PR #34 updates to 8.5.23 and is green, but that third-party version was published 2026-07-24 and remains inside the 14-day cool-off until 2026-08-07T17:05:13Z. Before release, either wait for the cool-off then revalidate and merge, or obtain the documented human-approved security exception after advisory, provenance, lock-diff, and yank-status review. Exact-head main CI must be green afterward.

## Notes

IMPLEMENTED in release-candidate commit 4c8a713 / PR #35: package-lock.json pins transitive PostCSS exactly 8.5.18 with nanoid 3.3.15. Node 24.18.0/npm 11.10.0 npm ci succeeded; local make verify and PR lint/distribution/Python 3.12-3.14 CI are green with npm audit reporting zero vulnerabilities. The 8.5.18 release is the oldest patched version and outside the 14-day cool-off. Keep open until PR #35 merges and exact-head default-branch CI/alert state confirms remediation; PR #34's too-recent 8.5.23 remains untouched.
