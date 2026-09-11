---
type: is
id: is-01m1z743jtmn911ekdsga2pevj
title: "After sans math and paint-once both land: the wait covers KPress Math Text Sans and its faces block"
kind: task
status: closed
priority: 2
version: 3
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T00:36:39.113Z
updated_at: 2026-09-08T06:41:53.494Z
closed_at: 2026-09-08T06:37:13.466Z
close_reason: "Done on kpress#57 before it merged (05ce8fb): the wait covers KPress Math Text Sans and its faces block"
resolution: null
duplicate_of: null
---
Found by the merge of main into squares/sans-math (fb9df70) with a read-only trial merge of #58: the two branches merge cleanly in katex-init.js but disagree semantically. (1) #58's TEXT_FACE_FONTS waits only on KPress Math Text at 400 and 700; the sans composite KPress Math Text Sans pins 400 and 650 and is not in the wait, so caption, footnote and table mathematics would still paint in the fallback and repaint. Add its four shorthands (normal and italic at 400 and 650), keyed on the same mode detection katex-init uses for the table set, and extend the Playwright paint-once test to a sans context. (2) #58 sets font-display: block on the eight serif composite faces; the eight sans screen faces still say swap, and #58's assertion covers only the serif family; flip them and assert both families. Also resolve the one textual conflict, tests/js/katex-init.test.js, where both sides append cases. Do this on whichever of the two branches lands second, before it merges.

## Notes

DONE, landed on squares/sans-math and merged to main with #57 (merge commit 7fcc226).
Left open for the coordinator to close.

Both halves are done, in commit 1942bcb:

(1) The wait covers both composites. Which composites to wait for is now the same
question as which tables to install, asked once for the page instead of once per node:
the sets are collected with `textMetricsSet`, the function the render loop selects tables
with, over the same `.kpress-math-render` nodes, so there is no second notion of "this
page has sans mathematics" that could disagree with the one the render uses. A page with
no math in a sans role asks for the serif slots alone, exactly as before the sans
composite existed, and a page that has opted out waits on the KaTeX faces alone. The sans
slots are asked for at 400 and 650 (not 400 and 700): a shorthand at the serif weights
would match the other slot's face and leave the drawn one to arrive late.

(2) The eight sans screen faces are `font-display: block`, asserted over both families in
one test. The four static instances inside `@media print` keep `swap` deliberately -- no
first paint to protect in a PDF, and `block` blanks a whole run rather than the code
points the face claims -- and that is asserted too.

The `tests/js/katex-init.test.js` conflict is resolved with both sides' cases. New
coverage: three vitest cases on which composites a page asks for (both, sans only under
the reader's sans reading face, and no sans slot on an all-prose page), and a Playwright
`test_sans_role_mathematics_paints_once_in_its_final_faces` asserting on a page with
mathematics in prose, a table cell and a footnote that every face of BOTH composites
loaded before the first `.katex` node existed, that every face the wait's own record says
it covered did too, and that the wait settled rather than being released by its deadline.

The wait ceiling stays at 3000ms, at or above Chrome's block period, per the #58 addendum
(comment 5577461326).
