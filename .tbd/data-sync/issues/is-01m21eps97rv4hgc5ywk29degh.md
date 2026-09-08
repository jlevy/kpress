---
type: is
id: is-01m21eps97rv4hgc5ywk29degh
title: Refuse mono weight sets by what the document needs, not by what the packaged CSS could ask for
kind: feature
status: open
priority: 2
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T21:27:40.070Z
updated_at: 2026-09-08T21:27:40.070Z
---
Measured on the squares explainer while adopting Planetaire (squares#134, 2026-09-08): the page has 11 code spans, 179 characters, no fenced block, so syntax.css never matches a token and nothing on the page is italic or bold code. The export proves it: before the change it embedded Menlo-Regular and nothing else; after, PlanetaireMonoText-Regular and nothing else. So one declared style would have drawn every glyph, but mono_weights_rejection refuses any set that leaves a style the packaged stylesheets could ask for undeclared, so the page ships all four (79,421 bytes of base64 where about 20,000 would do, and it inlines every face). The rule is right for a document with highlighted code and wrong for one without. Options: let a host declare that it runs no highlighting (a setting, or inferred from the absence of fenced blocks in the rendered tree) and refuse only the styles that document can actually reach; or expose the analysis kpress already does so a host can compute the needed set and pass it. Either way keep the guarantee that no glyph is synthesized. Measure the saving on a page with fences and one without before choosing.
