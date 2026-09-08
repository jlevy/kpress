---
type: is
id: is-01m1yffqyysqevrgj22mvy6keg
title: "Future: sans math (letters and digits from Source Sans 3 in sans prose and sans contexts)"
kind: feature
status: closed
priority: 2
version: 7
spec_path: docs/math-text-face.plan.md
labels:
  - typography
  - future
dependencies:
  - type: blocks
    target: is-01m1z743jtmn911ekdsga2pevj
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-07T17:43:34.621Z
updated_at: 2026-09-08T06:37:13.159Z
closed_at: 2026-09-08T06:37:13.158Z
close_reason: "Shipped: kpress#57 merged to main at 7fcc226 on 2026-09-08 after a senior review (request changes, all findings and the addendum addressed) and the paint-once reconciliation"
resolution: null
duplicate_of: null
---
Started 2026-09-07 on branch squares/sans-math (stacked on squares/print-sans-faces), by the owner's decision to run it in parallel now that the PT Serif math text face has shipped on squares/page-fixes. Scope: a second composite family, KPress Math Text Sans, drawing the digits and Latin letters of mathematics from Source Sans 3 with its own metrics tables from devtools/katex_text_metrics.py, applied when the reader chooses the sans reading face (data-kpress-prose-font=sans) and inside sans contexts of a serif document (figure captions, footnotes, tables and other sans roles), so the mathematics in a caption is set in the caption's own face and weight. Screen draws from the variable face across its weight range; print declares the static instances (kpr-w0s9) as the composite's faces so the PDF embeds them. Greek from the KaTeX faces scaled to Source Sans 3's x-height and cap height, as the serif composite does for PT Serif. katex-init selects the table set per rendered node's context, since KaTeX's metric tables are global per render call. Measure first: x-height, cap height, digit height, stem at 370 to 700, and advance-width variation across the weight axis (the metrics table is per face, not per weight, so the error bound must be stated). Additive changes only, beside the serif composite, since PR #53's review fixes touch the same files and will be merged in.
