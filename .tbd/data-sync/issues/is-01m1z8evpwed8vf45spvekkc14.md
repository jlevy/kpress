---
type: is
id: is-01m1z8evpwed8vf45spvekkc14
title: "PR #58 review R5: the math-assets note describes pre-fix behaviour"
kind: bug
status: open
priority: 3
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1z8drasjh3hct7hke23s0kj
created_at: 2026-09-08T01:00:00.087Z
updated_at: 2026-09-08T01:00:00.087Z
---
docs/kpress-design.md L1634-1638 still says the woff2 faces are fetched on demand per face and that a trivial \$x^2\$ pulls only the Main/Math faces. After PR #58 a trivial \$x^2\$ pulls all six Main/Math faces plus the composite's eight, eagerly, before the render. The passage contradicts the new 'Paints once' paragraph in the same file. Fix: keep the lazy statement for the construct-specific families and cross-reference Paints once for the two the init loads up front.
