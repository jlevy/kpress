---
type: is
id: is-01m1z1st1e16fv3dac88902wgm
title: "Math paints once: wait for the composite faces before the first KaTeX render"
kind: bug
status: in_progress
priority: 1
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-07T23:03:38.795Z
updated_at: 2026-09-07T23:04:28.839Z
---
Owner (2026-09-07): on page load the digits in formulas visibly change font. Measured on the squares explainer (every face inlined as a data URI): the page ships no pre-rendered math; katex-init renders 18 nodes at about 350 ms and 189 by 540 ms; the KPress Math Text faces carry no font-display (auto) while the KaTeX faces declare swap; the composite's PT Serif slot is a separate face from the prose PT Serif and is decoded lazily on first use, so the first paint of a formula uses the family's fallback, KaTeX_Main, and swaps to PT Serif when the slot finishes decoding. Fix in katex-init.js: before the first render, await document.fonts.load for each composite slot the page can use (normal, italic, bold; a sample string covering a Latin letter, a digit and a Greek letter so both faces of each slot load) and for the KaTeX faces the bundle names, then render, so the math appears once in its final faces; with inlined data this costs tens of milliseconds, and in hosted mode it delays the math rather than flashing it. Give the composite faces font-display: block so a face that is somehow not ready hides its text rather than showing a fallback. Add a Playwright test with an init script (page.add_init_script) that records the time of the first .katex insertion and each composite face's status transitions, asserting every composite face is loaded before the first math node is inserted; keep the opt-out modes working. Consider rel=preload hints for hosted mode and say why or why not.
