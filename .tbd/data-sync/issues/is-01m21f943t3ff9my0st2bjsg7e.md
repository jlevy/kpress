---
type: is
id: is-01m21f943t3ff9my0st2bjsg7e
title: Code inside a tooltip preview draws in the platform monospace, not the shipped face
kind: bug
status: open
priority: 2
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T21:37:40.983Z
updated_at: 2026-09-08T21:37:40.983Z
---
Found auditing kpress's chrome for squares#134: tooltips.js mounts the preview popover outside every .kpress wrapper on purpose (see its comment and the components.css note), so the .kpress code rule never matches it. The popover's own rules (.kpress-tooltip code, .kpress-tooltip pre) set size and wrapping but no family, so the code element tooltips.js injects for a code preview, and any code inside a footnote preview cloned from the author's HTML, renders in whatever monospace the reader's machine supplies. Same class of defect as the math overlays that #57 fixed by carrying the mode into the overlay: give the tooltip scope the mono family (and the mono size rung) the same way it already carries the math face, and add a browser assertion that a code preview resolves to a custom face.
