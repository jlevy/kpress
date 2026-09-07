---
type: is
id: is-01m1yfesy4xsgdvn6wttcwmfhj
title: "Math text face: letters and digits from the reading face in KaTeX"
kind: epic
status: closed
priority: 2
version: 8
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
child_order_hints:
  - is-01m1yffpn6v2vwm6b1cqkvszee
  - is-01m1yffpzgwmmbyrzj561k6sa3
  - is-01m1yffq9s7xz2p0temphqz1zq
  - is-01m1yffqm4ktp7gvk5jrag9j6a
  - is-01m1yffqyysqevrgj22mvy6keg
  - is-01m1yffr98j2cdpmvtq8thqp1q
created_at: 2026-09-07T17:43:03.875Z
updated_at: 2026-09-07T19:10:32.793Z
closed_at: 2026-09-07T19:10:32.792Z
close_reason: Feature complete on squares/page-fixes, PR jlevy/kpress#53; the deferred sans-math and Greek-sizing follow-ups stay open (Greek lowercase and capitals are already scaled inside the composite; the bead tracks any further tuning).
resolution: null
duplicate_of: null
---
Draw every Latin letter and digit inside KaTeX mathematics from the reading face (PT Serif), keep operators, relations, delimiters and Greek in the KaTeX faces, set inline math at the prose size, and supply KaTeX with the reading face's metrics. On by default, switchable off, open to other reading faces by contract. Design and phases: docs/math-text-face.plan.md; evidence: docs/math-text-face.research.md. Driven from the squares repository (epic think-rk9v), which carries this branch.
