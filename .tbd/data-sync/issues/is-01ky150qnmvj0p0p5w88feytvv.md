---
type: is
id: is-01ky150qnmvj0p0p5w88feytvv
title: Reject non-integer dynamic TOC collapse depths
kind: bug
status: open
priority: 2
version: 1
labels:
  - toc
  - python
  - host-api
dependencies: []
parent_id: is-01ky147hh0nbx9vhjphw3fabn3
created_at: 2026-07-21T01:35:33.043Z
updated_at: 2026-07-21T01:35:33.043Z
---
render_view only compares toc_collapse_depth < 1. Float and bool values pass and are stamped as 1.5 or True even though browser parsing disagrees; strings raise a raw TypeError instead of KPressInvalidRequestError. Validate isinstance(value, int), explicitly reject bool, and require >=1 before cache/render; add float, bool, and string boundary tests.
