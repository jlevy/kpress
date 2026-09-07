---
type: is
id: is-01m1yffpzgwmmbyrzj561k6sa3
title: KPress Math Text composite faces, class rules, size token, system revert
kind: task
status: closed
priority: 2
version: 3
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies:
  - type: blocks
    target: is-01m1yffqm4ktp7gvk5jrag9j6a
parent_id: is-01m1yfesy4xsgdvn6wttcwmfhj
created_at: 2026-09-07T17:43:33.615Z
updated_at: 2026-09-07T19:10:32.514Z
closed_at: 2026-09-07T19:10:32.514Z
close_reason: "Landed in jlevy/kpress#53 (commits 06301dd, 1d82940, 98594f2, 6cd820e): metrics generator and asset, KPress Math Text composite and init hook, option and contract, tests, goldens and docs."
resolution: null
duplicate_of: null
---
style-tokens.css: eight @font-face rules (four slots x reading face + KaTeX face, disjoint unicode-ranges), --kpress-katex-size-prose: 1em under [data-kpress-math-text=prose], revert under [data-kpress-fonts=system]. components.css: root .katex family and the .mathnormal/.mathit/.mathbf/.boldsymbol/.textrm/.mainrm rules pointed at the composite, with the specificity note.
