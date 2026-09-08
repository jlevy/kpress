---
title: "Research: Source Sans 3 Inside KaTeX Mathematics"
description: What Source Sans 3 measures against the KaTeX faces and PT Serif, how much its advances move along the weight axis, and which weight a per-face metric table can honestly be built at
author: Claude (agent), for samanthadrakova@gmail.com
---
# Research: Source Sans 3 Inside KaTeX Mathematics

**Date:** 2026-09-07 (last updated 2026-09-07)

**Author:** Claude (agent), for samanthadrakova@gmail.com

**Status:** Complete; the composite it recommends is implemented as
`KPress Math Text Sans` on `squares/sans-math` (bead `kpr-7f9z`).

## Overview

The [math text face](research-2026-09-07-math-text-face.md) draws the Latin letters and
digits inside KaTeX from PT Serif and hands KaTeX PT Serif’s own metrics to lay them
out. It does that everywhere, which leaves the mathematics in a caption, a footnote or a
table set in the serif while the words around it are Source Sans 3. This brief measures
what a second composite would cost and what it can honestly promise.

The question that decides the design is narrow: a KaTeX metric table is *per face*, not
per weight, and Source Sans 3 is a variable face whose advances grow with weight.
A table built at one weight describes glyphs drawn at another only approximately, so
either the drawn weight is pinned to the table’s weight, or the error is stated.
Both halves of that trade were measured.

## Questions to Answer

1. What does Source Sans 3 measure against `KaTeX_Main` and against PT Serif, at every
   weight kpress’s sans contexts request?
2. How far do the advances and the heights of Latin letters and digits move along the
   weight axis, and what does that cost a per-face metric table?
3. Which weight should each of the composite’s slots be built at?
4. What are the Greek scale factors for the sans, per slot?
5. Should operators come from Source Sans 3, as digits and letters do?
6. Does the variable face the screen draws from agree with the static instances print
   draws from, so one table can serve both?

## Scope

Included: the vendored Source Sans 3 variable faces and the static instances
`devtools/instance_sans.py` writes; the vendored KaTeX faces; PT Serif for reference.
Measured with fontTools from the shipped woff2 files, in units of 1/1000 em; “stem” is
the narrowest ink run across `l` at half its height, “`o` stroke” the same across `o`,
so stem against `o` stroke is the face’s contrast.

Excluded: Greek from Source Sans 3 (the vendored subset has none, exactly as PT Serif’s
does not), a different sans face, and the question of whether sans mathematics should
exist at all, which the [plan](../../math-text-face.plan.md) settles.

## Findings

### Source Sans 3 against the faces it has to sit beside

| Face | x-height | Cap height | Digit height | Ascender (`l`) | Stem `l` | `o` stroke |
| --- | --- | --- | --- | --- | --- | --- |
| Source Sans 3 at 370 | 484 | 660 | 638 | 714 | 71 | 73 |
| Source Sans 3 at 400 | 486 | 660 | 638 | 712 | 82 | 85 |
| Source Sans 3 at 550 | 490 | 660 | 637 | 708 | 107 | 110 |
| Source Sans 3 at 600 | 491 | 660 | 636 | 706 | 115 | 118 |
| Source Sans 3 at 650 | 494 | 660 | 636 | 703 | 131 | 135 |
| Source Sans 3 at 700 | 496 | 660 | 635 | 700 | 147 | 150 |
| KaTeX_Main-Regular | 442 (ink 431) | 683 | 666 | 694 | 81 | 98 |
| KaTeX_Main-Bold | 450 (ink 444) | 686 | 655 | 694 | 123 | 143 |
| KaTeX_Math-Italic | 441 | 683 | — | 694 | 83 | 96 |
| KaTeX_Math-BoldItalic | 532 (ink 452) | 680 | 461 | 694 | 127 | 139 |
| PT Serif Regular | 500 | 700 | 712 | 752 | 90 | 96 |

The italic instances measure the same verticals as the upright ones at every weight and
carry slightly narrower stems (66 at 370 rising to 136 at 700).

Three things follow, and they make the sans case a different problem from the serif one.

**The height mismatch is the same size and the opposite sign for digits.** Source Sans’s
x-height is 10.0% above `KaTeX_Main`’s (486 against 442), close to PT Serif’s 13.1%. But
its digits are *shorter* than Computer Modern’s, 638 against 666, where PT Serif’s are
taller, 712. So the swap does not push a numerator out of the box KaTeX computed, as the
serif swap did; it leaves a little slack in it.
Either way the table has to say so, which is the point of shipping one.

**The weight mismatch is nearly gone.** Source Sans at 400 has an 82 stem against
`KaTeX_Main`’s 81, so the two faces are the same colour; PT Serif’s 90 was 11% heavier.
What is left is contrast: Source Sans is monoline (82 against 85) while Computer Modern
is a 1:1.21 modulated face (81 against 98). Beside Source Sans, the KaTeX symbols read a
shade darker on their round strokes and identical on their stems, which is a much
smaller discord than the serif pairing had.

**The advance mismatch is also nearly gone.** Source Sans sets `1` on a 0.497em advance
against `KaTeX_Main`’s 0.500em. That is a useful fact for anyone writing a test: the
serif regression can tell which face drew a digit from its advance alone (0.533 against
0.500), and the sans regression cannot.
It has to ask Chromium which face it resolved.

### What the weight axis does to a per-face table

Advance widths of the 62 Latin letters and digits, relative to the same glyph at 400:

| Style | Axis step | Max | Median | Mean |
| --- | --- | ---: | ---: | ---: |
| upright | 400 → 370 | 3.08% (`f`) | 1.00% | 1.12% |
| upright | 400 → 550 | 6.51% (`f`) | 2.27% | 2.49% |
| upright | 400 → 650 | 12.67% (`f`) | 4.58% | 4.86% |
| upright | 400 → 700 | 16.78% (`f`) | 6.00% | 6.45% |
| upright | 370 → 700 | 20.49% (`f`) | 7.09% | 7.68% |
| italic | 400 → 650 | 13.65% (`I`) | 4.56% | 5.02% |
| italic | 370 → 700 | 21.99% (`I`) | 7.18% | 7.95% |

Heights over the same axis barely move: across 370 → 700 the largest change in any
glyph’s ink height is 0.035 em and the median is 0.005 em, because the design keeps cap
height fixed at 660 and lets the x-height drift by 12/1000 while the stems double.

That asymmetry is the whole finding.
The entries a KaTeX metric table is *for* — `depth` and `height`, which drive fraction
boxes, script placement, radical clearance and accent height — are very nearly
weight-invariant, so a table built at any weight lays out a run drawn at any other
correctly. The entries that move are `width` and the italic correction, and they move
enough (a median 4.6% at the sans bold weight, a worst case of 12.7%) that a table built
at 400 must not be used to describe glyphs drawn at 650.

### Which weight each slot is built at

The composite has four style and weight slots, as the serif one does, and the drawn
weight in each is **pinned by the slot’s own `font-weight` descriptor** rather than
inherited from the context.
Pinning is what makes the tables exact rather than approximate: CSS Fonts 4 clamps a
variable face to the range its `@font-face` declares, so a single-valued descriptor
draws one weight whatever the context asks for, and that weight is the weight the table
was built at.

The two weights are 400 and the sans bold token, 650:

- **400 for the regular slots**, because that is the weight KaTeX already asks for.
  Upstream’s root rule is `.katex { font: normal 1.21em KaTeX_Main, … }`, and the `font`
  shorthand resets `font-weight` to `normal`. So mathematics inside a caption, a
  footnote or a table is set at 400 today and stays at 400 with the composite, whatever
  weight the surrounding text carries.
  A host that sets a caption at 410 gets its mathematics at 400, 10 units light, which
  is a 0.15% advance difference by interpolation from the 3.08% measured over the 30
  units down to 370: below anything visible, and exactly described by the table.
- **650 for the bold slots**, because `--kpress-font-weight-sans-bold` is what “bold”
  means in every other sans context kpress ships — table headers, headings, the dialect
  boxes. `\mathbf{D}` inside a 410-weight caption therefore reaches the same 650 as a
  bold word in the caption beside it, rather than upstream’s 700, which is a step
  heavier than any bold the document otherwise sets.

The alternative — declaring each slot over the whole `200 900` axis and letting the
context’s weight carry through — was rejected on the table above.
It would buy a 410-weight caption a 410-weight mathematics, a difference no reader can
see, and would pay for it by handing KaTeX widths that are wrong by up to 12.7% wherever
a host sets a heavier weight inside `.katex`.

### The Greek scale factors

The vendored Source Sans subset has no Greek, so KaTeX’s Greek stays and is scaled to
Source Sans’s own vertical measure, exactly as the serif composite scales it to PT
Serif’s: italic Greek to the x-height, upright capitals to the cap height.

| Slot | Source Sans measure | KaTeX face | Factor |
| --- | ---: | --- | ---: |
| normal 400 (Main-Regular) | cap 660 | KaTeX_Main-Regular 683 | 0.966 |
| normal 650 (Main-Bold) | cap 660 | KaTeX_Main-Bold 686 | 0.962 |
| italic 400 (Math-Italic) | x 486 | KaTeX_Math-Italic 441 | 1.102 |
| italic 650 (Math-BoldItalic) | x 494 | KaTeX_Math-BoldItalic 452 | 1.093 |

`Main-Italic` and `Main-BoldItalic` take the italic slots’ factors rather than their
own, for the reason the serif generator records: `\mathit` is laid out from those tables
but its Greek is drawn by the italic slot’s `KaTeX_Math` face, so the table has to scale
by the face that is drawn.

The upright factors are below 1, which the serif composite’s never were: Computer
Modern’s Greek capitals are 3.5% *taller* than Source Sans’s capitals, so they shrink.

### Operators stay KaTeX

The same check the serif brief ran, on the sans, and with the same answer.

| Face | `+` centre | `=` centre | `−` centre | `+` advance | `≤` `≥` |
| --- | ---: | ---: | ---: | ---: | --- |
| Source Sans 3 at 400 | 330 | 330 | 330 | 497 | absent |
| Source Sans 3 at 650 | 330 | 330 | 330 | 520 | absent |
| PT Serif Regular | 341 | 344 | 344 | 533 | absent |
| KaTeX_Main-Regular | 250 | 250 | 250 | 778 | present |

Source Sans centres its operators 0.080 em above KaTeX’s math axis — a little less than
PT Serif’s 0.094 em, and still nearly a pixel and a half at 18px, so a Source Sans minus
sign would sit above the bar of the fraction beside it.
It also sets `+` on 0.497 em against KaTeX’s 0.778 em, so `2 + 3` would lose 0.281 em of
the space KaTeX builds around a binary operator without KaTeX knowing it had, and it has
no `≤` or `≥`, so a relation would come from one face and the equals sign beside it from
another. Each of those three is on its own a reason the serif brief eliminated its route
H; measured together on the sans, none of them is smaller here.
Letters and digits are the whole of what should move, as in the serif composite.

### One table serves screen and print

The screen draws the composite’s Latin ranges from the variable faces
(`source-sans-3-latin-wght-{normal,italic}.woff2`) clamped by the slot’s descriptor; a
printed page draws them from the static instances, because Chromium’s PDF writer turns a
variable face away from its default position into Type3 outline paths (the reason
[Print Sans Faces](research-2026-09-07-print-sans-faces.md) exists).
Two sets of files, so the question is whether one metric table describes both.

It does, exactly: instancing the variable face at 400 and at 650 in both styles and
comparing all 62 advances against the shipped static instances gives a maximum
difference of 0.000000 em.
The generator therefore reads the static instances, and what it writes is true of the
variable face at the same position.

## Key Insights

- **The vertical entries of a metric table are weight-invariant and the horizontal ones
  are not.** That is what makes a per-face table workable for a variable reading face at
  all, and it is also what says the two bold slots need their own build weight rather
  than a shared one.
- **The sans pairing is a face problem, not a weight problem.** Source Sans at 400 and
  `KaTeX_Main` have the same stem to within a unit; what separates them is a 10%
  x-height gap and the fact that one is monoline and the other modulated.
  So the sans composite buys less contrast repair than the serif one did and more
  identity: the numbers in a caption become the caption’s numbers.
- **The serif regression’s cheapest probe does not transfer.** PT Serif’s digits are
  6.6% wider than Computer Modern’s, so an advance measurement identifies the face;
  Source Sans’s are 0.6% narrower, which no layout measurement can separate from noise.
  A sans regression has to ask the engine which face it resolved
  (`CSS.getPlatformFontsForNode`), which is what the print sans regression already does.

## Recommendation

Ship `KPress Math Text Sans` as a second composite with the same slot structure as the
serif one: the Source Sans variable faces over `U+0030–0039, U+0041–005A, U+0061–007A`
with single-valued `font-weight` descriptors at 400 and 650, the static instances at the
same weights layered over the same ranges under `@media print`, and the KaTeX faces over
Greek at 96.6%, 96.2%, 110.2% and 109.3%. Build the six metric tables from the 400 and
650 static instances.
Keep operators, relations, delimiters and radicals in the KaTeX faces.

## Open Questions

- **Headings and the TOC.** Both are sans roles, and both are set at the sans bold
  weight (`.kpress-prose h1` through `h6` carry
  `font-weight: var(--kpress-font-weight-sans-bold, 650)`). Giving them the composite
  would set their mathematics at 400 against 650 words, which is the one place the
  pinned weight is visibly wrong, so they are outside the scope for now.
  Routing a heading’s mathematics to the bold slots is not possible with a per-class
  table: KaTeX picks the table from the TeX, not from the CSS.
- **Tooltips.** A footnote preview is rendered outside the `.kpress` wrapper, so neither
  composite reaches it; the overlay scope is being fixed separately.
- **Table headers.** `.kpress-table th` is inside the composite’s scope through
  `.kpress-table` and is set at 650, so mathematics in a header has the heading problem
  in miniature. It is rare enough to accept, and it is still an improvement in face.
- **Byte cost.** On a page that inlines every asset the sans composite adds the two
  variable faces again (about 28 KB each as woff2), the four static instances under
  print (15 KB each) and a second metrics table.
  Subsetting the composite’s faces is `kpr-hhdc`.

## References

- [Research: Harmonizing the Reading Face with KaTeX Mathematics](research-2026-09-07-math-text-face.md),
  whose method, units and reference measurements this brief reuses.
- [Research: Print Sans Faces](research-2026-09-07-print-sans-faces.md) for why print
  needs the static instances.
- [Math Text Face](../../math-text-face.plan.md);
  [KPress Design: Math Text Face](../../kpress-design.md#math-text-face).
- [CSS Fonts 4, matching font styles](https://www.w3.org/TR/css-fonts-4/#font-style-matching),
  for the clamping rule the pinned descriptors rely on.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
