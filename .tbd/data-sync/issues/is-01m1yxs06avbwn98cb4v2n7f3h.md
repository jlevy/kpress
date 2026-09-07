---
type: is
id: is-01m1yxs06avbwn98cb4v2n7f3h
title: Draw the list marker as a box, not a glyph
kind: bug
status: in_progress
priority: 2
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-07T21:53:18.012Z
updated_at: 2026-09-07T22:36:31.745Z
---
document.css (~200), components.css (~1561) and print.css (~348) set the list marker with content: "\25AA\FE0E". PT Serif's latin subset has no U+25AA, so the marker falls down the prose stack to Georgia on Macs (16 KB of Georgia embedded in the squares PDF for 48 bullets) and to something else elsewhere. Draw it as a pseudo-element box (width, height, background: currentColor, positioned by the existing top calc) so it depends on no font and is identical on every machine, keep its size relative to the font size token, and keep hosts that override the marker working. Goldens and the reader parity tests.
