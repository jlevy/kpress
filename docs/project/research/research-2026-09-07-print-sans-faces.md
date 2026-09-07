---
title: "Research: Why the Printed Sans Reads Lighter Than the Serif Beside It"
description: What Chromium's PDF writer does with a variable font, why a smoothing viewer leaves the result thin, and what a static instance changes
author: Claude (agent), for samanthadrakova@gmail.com
---
# Research: Why the Printed Sans Reads Lighter Than the Serif Beside It

**Date:** 2026-09-07 (last updated 2026-09-07)

**Author:** Claude (agent), for samanthadrakova@gmail.com

**Status:** Complete; the change it recommends ships as
[Print Sans Faces](../../kpress-design.md#print-sans-faces).

## Overview

A KPress document exported to PDF and opened in Preview shows a sans that reads a step
lighter than the PT Serif around it and lighter than the mathematics beside it.
The same document on screen does not.
Nothing in the stylesheets asks for a lighter sans on paper, and the print stylesheet
does not touch the sans weights, so the difference is made somewhere between the CSS and
the pixels a viewer draws.

This note records where.
The answer decides whether the fix belongs in the weight tokens (make the printed sans
heavier to compensate), in the export path, or in which font files ship.

## Questions to Answer

1. What does the exported PDF actually contain for the sans text, and how does that
   differ from PT Serif and the KaTeX faces in the same file?
2. Are the printed glyph shapes the right weight, or is the wrong weight being written?
3. If the shapes are right, what makes them read lighter on screen?
4. What changes if the same text is set in a static instance instead?

## Scope

Included: the PDF that headless Chromium writes for a KPress page, the fonts inside it,
the stem widths of one glyph across the PDF and the screen, and the ink a viewer puts on
the page with font smoothing off and on.
Excluded: print output from other engines (the PDF path is Chromium’s), paper printing
(this is about reading a PDF on a screen), and any change to the design of the sans
weights themselves.

## Findings

### What the PDF contains

The fonts in an exported 36-page document, by how each is written:

| Face | How it is written | Where |
| --- | --- | --- |
| Source Sans 3 Variable | Type3, glyphs as outline paths | every one of the 36 pages |
| PT Serif (four faces) | Type0, embedded font programs | as usual |
| KaTeX faces | Type0, embedded font programs | as usual |

Chromium cannot embed a variable font at any position but its default, so it falls back
to drawing each glyph as a path.
The two other families in the document are static files and embed normally, which is why
only the sans is affected.

### The shapes are the right weight

Measured on the stem of a caption `h` at 12pt, in em:

| Source | Stem width |
| --- | --- |
| The Type3 paths in the PDF | 0.0831 em |
| The same caption on screen | 0.0830 em |
| The variable face instanced at 410 | 0.0840 em |
| The variable face at its default (ExtraLight, 200) | 0.0300 em |

The paths in the PDF carry the weight the CSS asked for, to within a thousandth of an
em; they are not the ExtraLight default written out by mistake.
So nothing is being lost in the export, and adding weight to compensate would print text
heavier than the screen shows.

### Smoothing is the whole difference

A viewer that smooths text does so through the font machinery: it knows it is drawing
glyphs, and it can thicken the strokes to hold their color at small sizes.
Paths carry no such signal, so a viewer draws them as filled shapes and leaves them
alone. Measured with Quartz, the engine behind Preview, on one 12pt line, glyph `h`, as
the fraction of the glyph box covered in ink, with font smoothing off then on:

| How the glyph reaches the PDF | 3 px/pt | 2 px/pt |
| --- | --- | --- |
| Source Sans at 410, Type3 outline paths | 0.379 → 0.379 (no change) | 0.365 → 0.365 (no change) |
| Source Sans at 410, static instance, embedded | 0.376 → 0.395 (+5%) | 0.362 → 0.422 (+17%) |
| KaTeX_Main, embedded | 0.275 → 0.318 (+15%) | 0.273 → 0.327 (+20%) |

With smoothing off, all three are within a percent of each other and the page is
consistent.
With smoothing on, which is the default, the embedded faces gain 5 to 20% ink
and the paths gain none.
That gap is what a reader sees as a lighter sans.
The lower the resolution, the wider it gets, so the effect is strongest on the screens
where it is least welcome.

Rendered with MuPDF, which does not smooth, all three rows agree with the smoothing-off
column within 1%. The difference is the smoothing and not the outlines.

### What a static instance changes

A static instance is an ordinary font file: no `fvar`, one weight in `OS/2`, a name of
its own. Chromium embeds it as Type0 like PT Serif, and a viewer smooths it like any
other embedded font, which is the middle row of the table above.
Nothing else about the document changes: the same outlines, at the same weight, in the
same places.

## Key Insights

The bug is not in the weight and not in the export.
It is that two of the three families on the page reach the viewer as fonts and one
reaches it as drawings, and the viewer treats drawings differently.
That framing rules out the compensating fix (heavier print weights), because it would
make the printed sans wrong in the one configuration where the page is already
consistent, which is smoothing off.

It also sets the shape of the real fix: ship the sans to the PDF as a font.
Since the file that goes into the PDF is chosen by CSS font matching, this is a
stylesheet change plus a set of files, not a change to the export path.

## Recommendations

Ship static instances of the vendored variable faces at the weights KPress’s own sans
contexts request, declare them under `@media print` as a family distinct from the
variable one, and put that family first in the print sans stack.
Specifically:

- Six weights (370, 400, 550, 600, 650, 700) in normal and italic: the three weight
  tokens, the footnote controls’ 600, bold’s 700, and 400 for the resets.
  Twelve files of about 15KB.
- The family name `Source Sans 3` for the static set against `Source Sans 3 Variable`
  for the axis, which are the upstream names of the two releases.
  Distinct names keep the two from sharing a weight range, so font matching never has to
  break a tie.
- Generated rather than vendored, by `devtools/instance_sans.py`, with a `--check` mode
  in the lint gate: the instances are derived from files already in the repository, and
  a generator keeps them derivable when the weights change.
- Declared inside `@media print`, so a reader on screen downloads none of them.
- Behind `--kpress-host-font-sans-print`, so a host that changes the sans weights can
  point at its own instances.

Two requests land on a neighbor rather than an exact instance: the sans-mode headings
ask for 380 and 440, which CSS weight matching resolves to 370 and 400. That is a ten
and a forty unit difference on two headings, against instancing two more weights for
them; the mapping is pinned in `tests/test_print_sans_faces.py` so it stays a decision
rather than an accident.

## Methodology

The PDF was produced by the local `kpress export --pdf` path (headless Chromium) from a
36-page document containing prose, captions, footnotes and mathematics.
Its font list and the per-page font usage came from the PDF’s own resource dictionaries.
Stem widths were measured from the glyph outlines: from the Type3 path in the PDF, from
the screen rendering of the same caption, and from the variable face instanced with
fontTools at 410 and at its default position.
Ink fractions were measured by rasterizing one 12pt line at 3 and 2 pixels per point,
twice per configuration with Quartz font smoothing off and on, and counting covered
pixels in the glyph box; the same line was rasterized with MuPDF as a control.

## References

- [Print Sans Faces](../../kpress-design.md#print-sans-faces): the resulting design.
- [Print Sans Faces and Host Weights](../../kpress-operations-and-host-integration.md#print-sans-faces-and-host-weights):
  what a host that changes the weights owes its printed pages.
- `devtools/instance_sans.py`: the generator, and the public helpers a host instances
  with.
- [CSS Fonts 4](https://www.w3.org/TR/css-fonts-4/): the font matching algorithm, which
  decides where a request with no exact instance lands.
- [OpenType `fvar` table](https://learn.microsoft.com/en-us/typography/opentype/spec/fvar):
  the variation axes a static instance does not carry.
- [PDF 1.7, §9.6](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf):
  simple fonts, including the Type3 font dictionary.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
