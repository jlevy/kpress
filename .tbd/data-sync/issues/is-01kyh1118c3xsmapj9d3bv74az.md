---
type: is
id: is-01kyh1118c3xsmapj9d3bv74az
title: Perform the final 0.2.4 code and contract review
kind: task
status: in_progress
priority: 1
version: 9
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
updated_at: 2026-07-27T06:56:50.378Z
---
After all remediation changes land, review the aggregate v0.2.3...release-candidate delta rather than individual commits. Confirm Python APIs, template variables, CSS/JS contracts, data attributes, manifests, defaults, generated identifiers, and host behavior match the intended v0.2.4 design. For GitHub issue #33, verify the old heading algorithm and label/table slug coupling are removed completely, every consumer uses the new single source of truth, and no compatibility modes, alias ids, redirects, dual outputs, or stale documentation remain. Confirm docs, migration guidance, tests, and goldens match every intentional alpha-breaking change; record findings and block publication on unresolved P0/P1/P2 release defects.

## Notes

SENIOR REVIEW PUBLISHED for candidate `4c8a713991b01493d1d1ae16b7b7d7e53c499e1a` / PR
#35: https://github.com/jlevy/kpress/pull/35#issuecomment-5088221299

Verdict: changes requested.
One unresolved P2/Medium release defect, KPR-REV-01, independently confirms the Cursor
inline finding: `collapseDepth: 0` hides the control but leaves
`data-kpress-toc-collapse-depth` on server-configured markup, so collapse-only row
clipping and transitions remain active.
The fix must remove the activation attribute for the disabled binding, restore its exact
original state on disposal, add lifecycle assertions, and rerun the focused TOC suite
plus `make verify`.

No P0/P1 or additional P2 findings were found.
The issue #33 hard migration, public contracts, docs, tests/goldens, locked
dependencies, licensing, and distribution inspection otherwise passed review.
GitHub distribution, lint, and Python 3.12-3.14 CI are green.
Keep this bead open until KPR-REV-01 is fixed and the updated head is re-reviewed;
private security sign-off remains a separate release gate.
