---
type: is
id: is-01m1yxs24czqc8y3zz1n6q9709
title: "Quotation marks from a shipped quote face: Source Serif 4's six glyphs, replacing the borrowed Georgia"
kind: task
status: in_progress
priority: 2
version: 3
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-07T21:53:20.010Z
updated_at: 2026-09-07T23:40:11.741Z
---
Decision (owner, 2026-09-07, after seeing the three treatments side by side on the explainer): PT Serif's own quotation marks are unacceptable because its opening pair hangs about 2px above its closing pair at 18px (13.18px against 11.18px above the baseline) and its doubles are 16% wider than Georgia's; the original LocalPunct borrowing of Georgia's quotes was deliberate work to avoid exactly that, done when PT Serif replaced Georgia as the reading face, and its rationale was never written down. The owner's rule that every glyph comes from a shipped face still stands, so the fix is to ship the quotes rather than borrow them: subset Source Serif 4 (fontsource @fontsource/source-serif-4 5.3.0, published 2026-07-19, OFL-1.1; the companion of the Source Sans 3 and Source Code Pro faces kpress vendors) to exactly the six code points U+0022, U+0027, U+2018, U+2019, U+201C and U+201D (about 1 to 2 KB as woff2), generated reproducibly by a devtool (devtools/subset_quotes.py with --check, byte-stable like instance_sans.py; source file sha256 and the command in static/fonts/README.md), declared as a unicode-range face named KPress Quotes that leads --kpress-font-prose ahead of PT Serif on screen and in print; keep --kpress-host-font-punctuation as the opt-out or override hook; drop the local(Georgia) face. Document the rationale clearly in kpress-design.md (Quotation Marks): the history, the measurement of PT Serif's marks, why Georgia was borrowed, why a shipped subset replaces it, and the screenshots' numbers. Tests: asset contract, a Playwright check that a quotation mark resolves to KPress Quotes (custom) in screen and print media and that the PDF embeds it; goldens. Supersedes the earlier scope of retiring LocalPunct in favour of PT Serif's own marks, which PR #56 currently carries and which this replaces.
