---
type: is
id: is-01kyh110evqk49r4m30vz1xvac
title: Restore green main by remediating the PostCSS advisory
kind: bug
status: in_progress
priority: 0
version: 8
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
updated_at: 2026-07-27T06:35:01.442Z
---
Current main d1f014f fails the required npm audit because postcss 8.5.16 is affected by GHSA-r28c-9q8g-f849. PR #34 updates to 8.5.23 and is green, but that third-party version was published 2026-07-24 and remains inside the 14-day cool-off until 2026-08-07T17:05:13Z. Before release, either wait for the cool-off then revalidate and merge, or obtain the documented human-approved security exception after advisory, provenance, lock-diff, and yank-status review. Exact-head main CI must be green afterward.

## Notes

IMPLEMENTED LOCALLY 2026-07-27 on codex/v0.2.4-release-readiness: package-lock.json pins transitive PostCSS exactly 8.5.18 with existing nanoid 3.3.15. Under Node 24.18.0/npm 11.10.0, npm ci succeeded, npm ls confirmed the intended closure, npm audit and the canonical make verify dependency audits reported zero vulnerabilities. The 8.5.18 release is the oldest patched version and is outside the 14-day cool-off. Awaiting PR CI/exact-head main before closure; PR #34's too-recent 8.5.23 remains untouched.
