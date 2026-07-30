---
type: is
id: is-01kyh1118c3xsmapj9d3bv74az
title: Perform the final 0.2.4 code and contract review
kind: task
status: in_progress
priority: 1
version: 11
spec_path: docs/publishing.md
labels:
  - release
  - review
  - contract
  - breaking-alpha
dependencies:
  - type: blocks
    target: is-01kyh111g7g982p1der5dyxsz5
  - type: blocks
    target: is-01ky150r6vegs67zh623tnwy7j
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
created_at: 2026-07-27T05:33:39.468Z
updated_at: 2026-07-30T19:01:44.229Z
---
After all remediation changes land, review the aggregate v0.2.3...release-candidate delta rather than individual commits. Confirm Python APIs, template variables, CSS/JS contracts, data attributes, manifests, defaults, generated identifiers, and host behavior match the intended v0.2.4 design. For GitHub issue #33, verify the old heading algorithm and label/table slug coupling are removed completely, every consumer uses the new single source of truth, and no compatibility modes, alias ids, redirects, dual outputs, or stale documentation remain. Confirm docs, migration guidance, tests, and goldens match every intentional alpha-breaking change; record findings and block publication on unresolved P0/P1/P2 release defects.

## Notes

SENIOR REVIEW FOLLOW-UP COMPLETE on PR #35 head 3234dca60f9973652fa5dc8f444a8220719e6037. KPR-REV-01 was fixed by removing data-kpress-toc-collapse-depth for an explicit collapseDepth: 0 binding and restoring the exact original attribute state on disposal. The lifecycle regression proved red before the fix and green after it. Focused TOC suite 11/11; complete make verify passed with 574 Python/Playwright tests and 173 Vitest assertions; all six PR checks are green. Disposition map: https://github.com/jlevy/kpress/pull/35#issuecomment-5088342492; inline reply: https://github.com/jlevy/kpress/pull/35#discussion_r3655077209. No public P0/P1/P2 review defect remains.

FINAL RE-REVIEW 2026-07-30: PR #35 is unchanged at 3234dca, mergeable/CLEAN, has no unresolved review thread, and all six GitHub checks remain green. The full local make verify gate passed again on this exact head under Python 3.14.0 and Node 24.18.0: 574 pytest/Playwright tests, 173 Vitest assertions, lint/type/public-hygiene/supply-chain gates, zero npm/uv audit findings, distribution checks, and isolated-wheel smoke all passed. Final review: https://github.com/jlevy/kpress/pull/35#issuecomment-5135079479. PR #34 was reviewed and rejected for this release as a duplicate, policy-ineligible PostCSS bump that conflicts with the release-candidate lockfile: https://github.com/jlevy/kpress/pull/34#issuecomment-5135079718. This bead remains in progress only because private security sign-off, merge, and exact-head main confirmation are separately modeled dependencies.
