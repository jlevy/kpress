---
type: is
id: is-01m21eps97rv4hgc5ywk29degh
title: Refuse mono weight sets by what the document needs, not by what the packaged CSS could ask for
kind: feature
status: open
priority: 2
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T21:27:40.070Z
updated_at: 2026-09-08T21:37:39.479Z
---
Correction (2026-09-08, from an audit of kpress's own chrome): the original premise of this bead was too narrow and the refusal rule is better justified than it looked. Code does not take a second face only from syntax highlighting. It inherits weight and slant from whatever surrounds it, and kpress's own stylesheets make that ordinary: code inside a heading is bold (h1 to h6 at 650, h5 at 700), inside h2 or h6 it is italic, inside h4 it is italic at 540 which CSS matching resolves upward to the bold face, inside strong or b it is bold (650), inside a table header cell it is bold, and inside a summary it is 550 which resolves to bold. kpress also injects Pygments spans into every fenced block and syntax.css sets them bold, italic and bold-italic. So 'the document has no fenced block' is not sufficient to conclude that one face suffices; a page with a code span in any heading, strong, table header or summary needs more. What remains true is the measurement on the squares explainer (squares#134): its export embedded only PlanetaireMonoText-Regular before and after, so on that page one face would have served and four ship, about 60 KB of base64 it cannot use, because it inlines every face. So the useful version of this bead is narrower: give a host a way to declare or compute the styles its rendered tree actually demands, taking inheritance into account rather than only fenced blocks, and refuse only what that tree can reach. An analysis over the rendered DOM (which elements carrying code resolve to which weight and style) is the honest way to compute it, and kpress is the only side that can do it correctly.
