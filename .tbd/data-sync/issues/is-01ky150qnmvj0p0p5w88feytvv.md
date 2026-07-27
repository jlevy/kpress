---
type: is
id: is-01ky150qnmvj0p0p5w88feytvv
title: Reject non-integer dynamic TOC collapse depths
kind: bug
status: closed
priority: 2
version: 6
spec_path: docs/publishing.md
labels:
  - toc
  - python
  - host-api
dependencies:
  - type: blocks
    target: is-01kyh1118c3xsmapj9d3bv74az
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
created_at: 2026-07-21T01:35:33.043Z
updated_at: 2026-07-27T06:34:11.852Z
closed_at: 2026-07-27T06:34:11.852Z
close_reason: Implemented the reviewed TOC/runtime/CI correction with focused unit and real-browser regressions; the canonical make verify gate passes with all Playwright tests executed and no unexpected skips.
---
render_view only compares toc_collapse_depth < 1. Float and bool values pass and are stamped as 1.5 or True even though browser parsing disagrees; strings raise a raw TypeError instead of KPressInvalidRequestError. Validate isinstance(value, int), explicitly reject bool, and require >=1 before cache/render; add float, bool, and string boundary tests.

## Notes

IMPLEMENTED LOCALLY 2026-07-27: render_view validates exact int (rejects bool/non-int) and >=1 before cache/render. Boundary regression covers 0, -1, float, bool, and string; all pass.
