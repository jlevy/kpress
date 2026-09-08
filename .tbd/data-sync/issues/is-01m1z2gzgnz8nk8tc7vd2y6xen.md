---
type: is
id: is-01m1z2gzgnz8nk8tc7vd2y6xen
title: Settle the remaining sans weight literals and the caption weight
kind: task
status: open
priority: 2
version: 2
spec_path: docs/math-text-face.plan.md
labels: []
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-07T23:16:18.068Z
updated_at: 2026-09-08T00:54:18.409Z
---
The 2026-09-07 sans weight audit (three weight tokens: light 370, medium 550, bold 650) found five contexts still deciding weight by number or by omission. Two were fixed on squares/font-consistency (the tab label's literal 600, which disagreed with its own print rule, and the video placeholder's literal 700, the only sans chrome above the bold token). These are what remain, each needing a decision rather than a mechanical change:

1. components.css `.kpress-footnote-ref a` / `.kpress a.kpress-footnote-backref` / `.kpress-tooltip .kpress-footnote-nav-link` ask for a literal 600. It is the only sans consumer of 600, and devtools/instance_sans.py ships two static print instances (600 normal and italic, ~30 KB) solely to serve it. Snapping it to the bold token would let the print set drop from six weights to five; the design doc names "the footnote controls' 600" as a known value, so this is a deliberate choice to revisit rather than a defect.

2. `.kpress-table th` is the one caps label at 650 bold; the TOC title, the disclosure summaries, the print tab label and the doc-actions badge are all 550 medium. One of the two is wrong. Decide whether caps labels are medium with table headers a deliberate exception, or whether the idiom is bold.

3. `.kpress-figcaption` (document.css) and `.para-caption` (components.css) declare no font-weight at all, so both fall through to 400 -- and `.kpress-figcaption` inherits from its container, so a caption inside `.kpress .concepts` (650) renders bold while the same caption in prose renders 400. Captions should state a weight.

4. `.sans-text h1` / `h2` ask for 380 and 440, which CSS matching lands on 370 and 400, and `.kpress-prose h4` asks for 540, which lands on 550. All three are documented as deliberate in kpress-design.md, so this is only a question of whether they should say the token they land on.

Deliverable: a decision per context, the rules changed under the tokens, goldens, and a note in the design doc saying what the weight of a caption and a label is, so the next one does not get invented. If the footnote 600 goes, regenerate the print instance set and update tests/test_print_sans_faces.py EXPECTED_LANDING.

5. `components.css:804` (`.kpress-tooltip`) and `components.css:1420` (`.kpress .debug`) each declare a literal `font-weight: 400` inside an explicit sans rule. Both read as resets, putting a surface back to regular where it might otherwise inherit a heavier weight, and both are legitimate on those grounds. They are outside the register as written, because with only light/medium/bold tokens the rule that every sans weight comes from a token cannot cover a regular. Decide with the rest: add a regular token and point them at it, or state in the design doc that a reset to 400 is the one sanctioned literal and say why. Raised as K56-R11 in the senior review of PR #56 (comment 5577269395) and added here rather than fixed on that branch, since it is the same decision as the other four.
