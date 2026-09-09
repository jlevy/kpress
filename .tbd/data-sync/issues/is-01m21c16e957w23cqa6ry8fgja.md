---
type: is
id: is-01m21c16e957w23cqa6ry8fgja
title: "font_mode: system prints /Type3 outlines on macOS, undocumented"
kind: bug
status: open
priority: 2
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T20:40:55.496Z
updated_at: 2026-09-08T20:40:55.496Z
---
font_mode: system puts /Type3 glyph procedures in an exported PDF for every sans role. This is the same failure the mono_weights gate exists to prevent, and a reader reaches it through the settings widget's own System fonts toggle.

Measured on one page (prose, a sans heading, a footnote, a table, a code block) through render_pdf:

  font_mode=custom  31,846 bytes  0 /Type3
    PTSerif-Regular, KPressPrintSans-400/550/650, PlanetaireMonoText Regular/Bold/Italic
  font_mode=system  91,339 bytes (2.9x)  7 /Type3 objects over 3 descriptors
    EAAAAA+.SFNS-Regular, JAAAAA+.SFNS-Regular, LAAAAA+.SFNS-Bold, plus Georgia and Menlo from the machine

Remedy considered and rejected on measurement. The suggestion was to round KPress's own sans weight tokens (550, 650) to weights a platform face has (400, 700) inside the system block, since those tokens are KPress's own choice. Patched style-tokens.css to do exactly that and re-measured: the same three .SFNS descriptors appear, every one still carrying NO FontFile, and the 7 /Type3 objects remain. The PDF only shrinks to 83,363 bytes because the synthetic embolden strokes go away. The cause is that Chromium cannot embed the macOS system UI face at any weight, not that the requested weights are unusual. The patch was reverted.

Documentation is therefore the fix: the measurement and the descriptor evidence now sit under the settings table in kpress-design.md, with a cross-reference from the Mono Face section, which also records that mono_font: system is unaffected (Menlo embeds as /Type0).

No test: the behaviour is macOS-specific (.SFNS), and on a Linux runner system-ui resolves to an embeddable face, so a regression test would assert a different thing in CI than on a developer's machine.

Documented in branch squares/font-settings-fixes.
