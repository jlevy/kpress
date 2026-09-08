---
type: is
id: is-01m215haewzqpqrx8jkczdq7e8
title: Correct the print-sans base64 inlining claim in the operations doc
kind: bug
status: open
priority: 3
version: 1
spec_path: docs/math-text-face.plan.md
labels: []
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T18:47:23.867Z
updated_at: 2026-09-08T18:47:23.867Z
---
PR #62 review K62-R9 named three places resting a design on 'a single-file page inlines every face it declares'. Two were fixed in PR #62 (docs/kpress-design.md and src/kpress/format/assets.py) plus the mono half of docs/kpress-operations-and-host-integration.md.

docs/kpress-operations-and-host-integration.md:674 still carries the same falsehood for the print sans instances: 'the ten instances are 154,452 bytes of woff2, about 151KB, which base64 grows by a third to 205,948 bytes, about 201KB'. Measured: zero base64 blobs in any asset mode. Inline mode leaves woff2 as external URLs and single-file export is refused at build.py:783-787, so no asset mode base64s a font.

Left out of PR #62 because it concerns the print sans rather than the mono face and predates that branch. Fix needs the print-sans inline behaviour re-measured before the sentence is rewritten.
