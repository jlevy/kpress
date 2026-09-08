---
type: is
id: is-01m1z8etnv4c2n54h14nh8m3s2
title: "PR #58 review R4: 'Paints once' does not say what still repaints"
kind: bug
status: closed
priority: 2
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1z8drasjh3hct7hke23s0kj
created_at: 2026-09-08T00:59:59.033Z
updated_at: 2026-09-08T01:39:29.087Z
closed_at: 2026-09-08T01:39:29.084Z
close_reason: "Fixed on squares/math-paints-once (26d6822, 9b1778a); disposition posted on PR #58."
resolution: null
duplicate_of: null
---
docs/kpress-design.md 'Paints once' never mentions the construct-specific families, which keep the bundle's swap. Measured residuals in default mode: display \\sum +20.2ms, the glyph painted 11.4x18.0px and settling at 23.1x36.0px (+103% wide); KaTeX_AMS +11.8ms, .katex root 77.5 -> 87.7px; Caligraphic/Fraktur/Script/SansSerif/Typewriter +11.0ms each. Structural, not a race: without preload hints a construct-specific face cannot be requested before the render creates a node needing it. The 3s ceiling also deserves a sentence (with the composite delayed 6s, math renders at 3541ms at KaTeX_Main's 0.500em and repaints to 0.533em). Fix: name the limit in the paragraph.
