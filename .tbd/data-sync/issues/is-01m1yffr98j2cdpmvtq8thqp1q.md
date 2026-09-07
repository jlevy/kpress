---
type: is
id: is-01m1yffr98j2cdpmvtq8thqp1q
title: "Future: Greek sizing inside the composite (scale KaTeX Greek to the reading face)"
kind: feature
status: closed
priority: 3
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
  - future
dependencies: []
parent_id: is-01m1yfesy4xsgdvn6wttcwmfhj
created_at: 2026-09-07T17:43:34.951Z
updated_at: 2026-09-07T19:25:16.782Z
closed_at: 2026-09-07T19:25:16.781Z
close_reason: "Shipped inside the feature after all: the composite's italic slots scale KaTeX's Greek to PT Serif's x-height (115.0% / 112.6%) and the upright slots its capitals to PT Serif's cap height (102.5% / 102.0%), with the metric tables scaled by the same factors. Any further tuning is a new bead."
resolution: null
duplicate_of: null
---
Deferred by the owner on 2026-09-07, prototyped the same day as route J in docs/math-text-face.research.md: KaTeX_Math-Italic Greek range at size-adjust 113.4% (x-height match) and KaTeX_Main Greek capitals at 102.5% (cap-height match), metrics scaled by the same factors. Reads as an improvement. Two @font-face rules plus a generator parameter; can be pulled into the feature if the owner agrees.
