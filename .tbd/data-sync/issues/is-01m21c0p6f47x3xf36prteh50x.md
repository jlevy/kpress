---
type: is
id: is-01m21c0p6f47x3xf36prteh50x
title: Settings table named a host hook mathematics does not read
kind: bug
status: open
priority: 2
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T20:40:38.862Z
updated_at: 2026-09-08T20:40:38.862Z
---
docs/kpress-design.md gave the math_text_font row the host hook `--kpress-host-font-prose` with the gloss 'the composite follows the reading face'. It does not follow it.

Measured on a page with inline and display mathematics, rendered with head_extra_html setting `--kpress-host-font-prose: Palatino, serif` on :root:

  .kpress-prose p          -> Palatino, serif
  .kpress-prose h1         -> Palatino, serif
  .katex .mord.mathnormal  -> "KPress Math Text", KaTeX_Math, serif
  .katex .mord.text        -> "KPress Math Text", KaTeX_Main, "Times New Roman", serif

katex/katex-text-face.css hard-names KPress Math Text in all 44 of its font-family declarations and reads no --kpress-host-font-* variable.

Fixed by correcting the cell to 'none' and pointing at the two documented math seams (redeclare the composite faces after katex-text-face.css, regenerate the metric tables with devtools/katex_text_metrics.py), which kpress-operations-and-host-integration.md already describes correctly.

Decision recorded in the same commit: the composite SHOULD NOT follow the hook. KaTeX lays out from per-face metric tables in globalThis.kpressKatexTextMetrics and the Greek slots carry size-adjust values computed against PT Serif's x-height and cap height, so a family swapped by CSS variable alone would leave Computer Modern boxes around the new face's glyphs. Retargeting mathematics silently from a prose hook would produce exactly the failure the ops doc warns about.

Fixed in branch squares/font-settings-fixes.
