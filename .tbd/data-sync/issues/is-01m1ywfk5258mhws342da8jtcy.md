---
type: is
id: is-01m1ywfk5258mhws342da8jtcy
title: Tests and asset contract for the print sans faces
kind: task
status: in_progress
priority: 1
version: 2
labels:
  - typography
  - print
dependencies: []
parent_id: is-01m1ywfjt036hrzk0tk8p9je6v
created_at: 2026-09-07T21:30:41.185Z
updated_at: 2026-09-07T21:35:01.951Z
---
Asset contract lists the twelve instances and print-fonts.css; a test pins where every sans font-weight kpress's CSS requests lands on the instance set (exact for the tokens, 600 and 700; 380 to 370 and 440 to 400 for the sans-mode headings; 540 to 550); the generator's --check is exercised; a Playwright print-media test asserts the caption sans resolves to a 'Source Sans 3' custom face via CSS.getPlatformFontsForNode; goldens refreshed if the asset list is rendered.
