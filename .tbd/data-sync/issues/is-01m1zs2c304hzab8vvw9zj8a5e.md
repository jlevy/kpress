---
type: is
id: is-01m1zs2c304hzab8vvw9zj8a5e
title: "Decide: rename the sans math family, or fix the host's substring count of KPress Math Text blocks"
kind: task
status: closed
priority: 2
version: 3
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T05:50:16.535Z
updated_at: 2026-09-08T10:19:37.323Z
closed_at: 2026-09-08T10:19:37.313Z
close_reason: "Resolved by Squares PR #128, merged as 33cd47606dae223664f117945631440aa5c8ece9, with KPress pinned to 7b20ae702acf37020e6132265c8faa0ba74e4465. The host matches composite font families exactly instead of counting KPress Math Text as a substring, preserving the published KPress Math Text Sans family name. The merged host tree matches tested head 43c006bc; all pre-merge fast, Pages, and full deferred checks passed."
resolution: null
duplicate_of: null
---
Owner decision, raised by the senior review of #57 (K57-R2, second half). The consuming
squares host counts the composite's @font-face blocks in packing/devtools/render_explainer.py
with `"KPress Math Text" in block` -- a SUBSTRING test. The new family `KPress Math Text Sans`
satisfies it too, so the host counts 20 blocks against an expected 8 and raises SystemExit
before it reaches any other check. That is the consuming page the owner plans to judge caption
mathematics on, so it blocks the evaluation rather than the merge.

Two options, and kpress can only take the first:

(a) Rename the sans family so it is not a superstring of the serif one -- `KPress Sans Math
    Text` or `KPress Math Sans`. Cheap and fully reversible today: the family is introduced by
    #57 and has never shipped, so it is not yet public API. Costs the naming symmetry with
    `KPress Math Text`, and touches the stylesheet, katex-init.js's COMPOSITE_FONTS, the CSS
    and Playwright contract tests, and the docs.

(b) Fix the host to match families exactly rather than by containment, in the same block as
    #57. kpress's names are legitimate and a substring test over font-family names is the
    actual defect; this is one line in squares.

The selector-length half of K57-R2 is already fixed on the branch: the seven over-budget
preludes are gone (477 -> 339 max, which is origin/main's own maximum), and
tests/test_sans_math_face_css.py now measures the budget exactly the way the host does,
`len(prelude.strip()) < 400`, over every rule in the file.

## Notes

PREMISE CHANGED. #57 merged to main at 7fcc226 while this was being written, so
`KPress Math Text Sans` has now shipped on main. Option (a), renaming the family, is no
longer the free and fully reversible change described in the description: it is a change
to a name that is out, even if no release has cut yet. Check whether a release has gone
out before choosing, and weigh option (b), the one-line exact-match fix in the squares
host, correspondingly higher.

What has not changed: the consuming host still raises SystemExit before it reaches any
other check, because `"KPress Math Text" in block` in packing/devtools/render_explainer.py
counts the sans blocks too, 20 against an expected 8. Until one of the two options lands,
the squares explainer does not build -- which is the page the caption mathematics was to
be judged on.
