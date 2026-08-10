---
type: is
id: is-01kzkszj80ybn3c6avfx1884j4
title: Table code should step down a mono tier at every width, not only on mobile
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
created_at: 2026-08-09T17:43:56.415Z
updated_at: 2026-08-09T18:10:36.744Z
closed_at: 2026-08-09T18:10:36.743Z
close_reason: Fixed on fix/table-code-mono-tier
---
components.css scoped `.kpress-table code, .kpress-table pre { font-size: var(--kpress-font-size-mono-small) }` to the narrow band only (@container kpress-doc (max-width: 47.99rem)). At every wider pane, table code fell back to `.kpress code` at --kpress-font-size-mono.

The two ramps in style-tokens.css pair by index, holding code at one optical weight against the text around it:
  mono / normal       = 0.820
  mono-small / smaller = 0.833
  mono-tiny / tiny     = 0.824

A table reduces its text to `small` (0.95) but left code at `mono` (0.82), i.e. 0.863 of its own cell -- heavier inside a table than the identical span in prose, which mono's larger x-height exaggerates.

CORRECTION to the original filing: the narrow band was NOT achieving the right pairing via this declaration. It looked correct only because that band ALSO drops table text to `smaller`; the pairing came from the text side. So `small` has no mono partner at all (the text ramp has four tiers, mono has three), and neither candidate is exact -- mono-small gives 0.789, mono gives 0.863. mono-small is closer to the ramp's 0.82 and reads subordinate rather than competing.

Fix: hoist the declaration to the base table rules so it applies at every width, and drop the now-redundant narrow-band copy (the narrow band's result is unchanged at 0.833).

Measured in Chromium on KPress defaults (16px base): wide pane 15.2px cell, code 13.12px -> 12px; narrow pane unchanged at 14.4px/12px.
