---
type: is
id: is-01kzcvs055vgf618n96tnabc1g
title: Reserve the wide-band TOC rail so the reading column stops jumping
kind: bug
status: closed
priority: 1
version: 2
labels: []
dependencies: []
created_at: 2026-08-07T01:00:37.412Z
updated_at: 2026-08-07T01:00:40.779Z
closed_at: 2026-08-07T01:00:40.778Z
close_reason: Implemented on fix/reserve-toc-rail
---
In the wide band (>=75rem of pane width) a document with a TOC gets the left-aligned 15rem/53rem grid; one under toc_min_headings gets no grid and reverts to the centred, measure-capped column. Measured in Chromium at a 1300px pane: the text starts at 306px instead of 344px and runs 43rem instead of 48rem. Across documents with varying heading counts the prose visibly jumps sideways and changes width.

Adds RenderOptions.toc_rail / KPressRenderRequest.toc_rail / format.toc_rail:
- auto (default): today's behavior, renders byte-identical
- reserved: the rail is part of the layout whenever format.toc != off, so the column keeps one position and one measure with or without a sidebar

render.py stamps data-kpress-toc-rail=reserved on the layout wrapper only in the held-open-but-empty case; the wide band now selects on three conditions (.has-toc, :has(.kpress-toc), the stamp). Also pins the optional thumbnail to the reading column -- with no explicit track, grid auto-placement was dropping it into the empty rail.
