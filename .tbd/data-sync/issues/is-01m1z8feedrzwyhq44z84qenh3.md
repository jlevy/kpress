---
type: is
id: is-01m1z8feedrzwyhq44z84qenh3
title: Derive the math font wait from what the document contains, not from the mode
kind: feature
status: open
priority: 2
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T01:00:19.268Z
updated_at: 2026-09-08T09:44:31.755Z
---
Raised by the senior review of PR #58 (comment 5577424528) as the structural follow-up behind findings R3 and R4. The wait katex-init.js runs today is unconditional over the mode: all six KaTeX_Main/KaTeX_Math faces and all four composite slots, whatever the page draws. Two costs follow. (1) Over-fetch, measured on a \\sum...\\int fixture: +6 requests and +135,396 B (+115%) against the pre-fix build, of which KaTeX_Main-Italic and KaTeX_Main-BoldItalic are drawn by nothing on that page. (2) A residual repaint the wait cannot reach: display \\sum arrives half-size and settles at +103% width when KaTeX_Size2 lands (+20.2ms on loopback), and KaTeX_AMS and the five alphabet families do the same, because without preload hints a construct-specific face cannot be requested before the render creates a node needing it. The server already knows which constructs each document contains, so it could stamp the faces a page will actually draw and the init could wait on exactly those, closing both. Measure the display-math case first: \\sum and \\int in display mode are common enough that waiting on Size1-Size4 for documents containing display math may pay on its own. Do not fold this into kpr-hhdc (composite subsets), which shrinks the same bytes by a different route.

## Notes

Partially addressed by merged PR #59 (a265d553). Every render stages its actual KaTeX
HTML under the real CSS cascade, requests the fonts needed by its glyphs, and waits
before revealing it. This covers large operators, AMS, and explicit math alphabets,
including constructs first introduced by a dynamic host callback.

Keep this bead open for its remaining transfer-cost objective: initial preparation
still loads the six Main/Math faces and all four slots for each selected composite
profile. Reducing that warmup to styles actually present is separate from the now-fixed
construct repaint. Composite font subsetting remains separately tracked in kpr-hhdc.
