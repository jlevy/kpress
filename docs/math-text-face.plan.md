---
title: Math Text Face
description: Draw the letters and digits inside KaTeX mathematics from the reading face, with matching metrics, as a feature that is on by default and open to other faces
author: Claude (agent), for samanthadrakova@gmail.com
---
# Feature: Math Text Face

**Date:** 2026-09-07 (last updated 2026-09-07)

**Author:** Claude (agent), for samanthadrakova@gmail.com

**Status:** Implemented on `squares/page-fixes` (2026-09-07); Safari and Firefox checks
by hand remain.

**Tracking:** epic `kpr-sc4f`; tasks `kpr-g93o` (metrics generator and asset),
`kpr-c4oz` (composite faces and rules), `kpr-ai4c` (option, attribute, wiring, init
hook), `kpr-mot3` (tests, goldens, docs); deferred `kpr-7f9z` (sans math) and `kpr-c2tr`
(Greek sizing). Font consistency across screen and print is epic `kpr-b4mq`, below.
The consuming repository that carries this branch (squares, epic `think-rk9v`, and
`think-phgo` for fonts) tracks its own integration.

## Overview

KPress sets prose in PT Serif and mathematics in KaTeX, whose faces derive from Computer
Modern. The two disagree in x-height and stroke weight, and no size token can reconcile
both. The [research brief](project/research/research-2026-09-07-math-text-face.md)
measured the difference, prototyped eight routes on a rendered paper, surveyed what
LaTeX and the web renderers do, and settled on one: draw every Latin letter and digit
inside mathematics from the reading face, keep operators, relations, delimiters,
radicals and Greek in the KaTeX faces, set inline math at the prose size, and give KaTeX
the reading face’s own glyph metrics so its layout matches what it draws.

This plan makes that a KPress feature: on by default, switchable off per document, and
defined by a contract a host can satisfy with a reading face other than PT Serif.

## Goals

- Every Latin letter and digit in inline and display math is drawn from the reading
  face, in the matching weight and style (`\mathbf`, `\mathit`, `\boldsymbol`, `\text`,
  `\mathrm`, operator names and plain digits included).
- Operators, relations, delimiters, big operators, radicals, accents and Greek stay in
  the KaTeX faces, on KaTeX’s math axis.
- KaTeX lays out the swapped glyphs from the reading face’s metrics, so fraction boxes,
  script positions and italic corrections are computed for the glyphs drawn.
- The feature is on by default and switchable off per document; the old look is one
  option away.
- The face is a contract, optimized for PT Serif and open to another: a host that
  supplies its own faces and metrics under the same names gets the same behaviour.
- The vendored `katex.min.js` and `katex.min.css` stay byte-identical.

## Non-Goals

- Sans mathematics: letters from Source Sans 3 when the reader chooses the sans reading
  face, or inside sans contexts.
  Recorded under Future Work.
- Greek from the reading face; the vendored subset has none.
  KaTeX’s Greek is kept and scaled to the reading face instead (below).
- Punctuation inside mathematics (`, .` `…`) from the reading face; a one-line range
  change if it is ever wanted.
- Replacing KaTeX or rebuilding the KaTeX fonts.
- Upstreaming from the `squares/page-fixes` branch to `main`; an open question, not a
  deliverable here.

## Background

The brief’s findings this plan relies on:

- KaTeX draws digits, operator names and `\text{}` from whatever family the root
  `.katex` rule names; they carry no font class, so the only way to route them by glyph
  is a `unicode-range` composite family.
- KaTeX lays out from a metric table in its bundle,
  `[depth, height, italic, skew, width]` per face and code point, and exports
  `katex.__setFontMetrics(face, table)` to replace a face’s table at runtime (verified
  in the vendored 0.16.45 bundle).
  There is no getter, so a replacement table must be complete.
- PT Serif’s operators are centred 0.094em above KaTeX’s axis and it has no `≤`, so
  operators must not move.
- Scaling Computer Modern to PT Serif’s x-height makes it worse; the disharmony is
  weight as much as height.
- Headless Chromium’s print path is the same engine; a fourteen-page document exported
  through a print pipeline gave the same page count, a clean layout and self-agreeing
  renders.

Prior art: `unicode-math`’s `range=up/{num}` and `range=it/{latin}` and `mathspec` do
the same thing in LaTeX; `newtxmath` ships the same mixture pre-metricized for a dozen
text faces; MathJax and KaTeX have no supported route.

## Design

### Approach

One composite CSS family, `KPress Math Text`, in four style and weight slots.
Each slot is two `@font-face` rules with the same descriptors and disjoint
`unicode-range`s: the reading face for digits and Latin letters, and the KaTeX face that
slot replaces over the Greek range, scaled with `size-adjust`. Everything else is
claimed by no face and falls through to the next family in each rule’s stack, which is
that same KaTeX face; declaring it under the composite as well would only duplicate it
in a page that inlines its assets.

| Slot | Reading face | KaTeX face for Greek and the stack | Ranges taken by the reading face |
| --- | --- | --- | --- |
| normal 400 | PT Serif Regular | KaTeX_Main-Regular | U+0030–0039, U+0041–005A, U+0061–007A |
| italic 400 | PT Serif Italic | KaTeX_Math-Italic | U+0041–005A, U+0061–007A |
| normal 700 | PT Serif Bold | KaTeX_Main-Bold | as normal 400 |
| italic 700 | PT Serif Bold Italic | KaTeX_Math-BoldItalic | as italic 400 |

The root `.katex` family becomes `"KPress Math Text", KaTeX_Main, …`, and the class
rules that name a KaTeX family explicitly are pointed at the composite with the matching
style: `.mathnormal` and `.mathit` italic, `.mathbf` bold, `.boldsymbol` bold italic,
`.textrm` and `.mainrm` normal.
`.mathrm` and `.text` set no family and inherit the root.
Delimiters, big operators, AMS, calligraphic, fraktur, script, sans and typewriter
classes are untouched.

Disjoint ranges rather than an overlay into `KaTeX_Main` itself: the result then does
not depend on which stylesheet is linked last, which matters because KPress links
`katex.min.css` after its own stylesheets and a host that inlines everything may
concatenate them in the other order.
A host that wants another face declares its own `KPress Math Text` rules after KPress’s;
CSS Fonts 4 checks the last-defined face first, so the host’s faces win for the ranges
they declare and KPress’s KaTeX fallbacks keep the rest.

Sizes: with the letters in the prose face, inline math is the prose size.
`--kpress-katex-size-prose` and `--kpress-katex-size-display` both become `1em` when the
feature is on, since TeX sets displayed equations at the text size and the display lift
read as a size jump once the letters were the reading face; the sans token already is.

Metrics: a generated asset, `katex/katex-text-metrics.js`, that defines
`globalThis.kpressKatexTextMetrics` as complete tables for the six affected faces
(Main-Regular, Main-Italic, Main-Bold, Main-BoldItalic, Math-Italic, Math-BoldItalic):
KaTeX’s own entries, with the swapped code points rewritten from the reading face’s
bounds and advances (depth, height, italic correction as ink overhang past the advance,
width; skew kept from KaTeX). `katex-init.js` applies them with `katex.__setFontMetrics`
before `renderMathInElement` when the feature is on.
A host with another face ships its own table under the same global, generated by the
same tool.

The switch: a render option `math_text_font: Literal["prose", "katex"]`, default
`"prose"`, stamped as `data-kpress-math-text` on `<html>` by the page shell (fragments
bake no attribute; an embedding host stamps its own root, as with `prose_font`). The
feature rules and the size token are scoped positively, to a `.kpress` that has not
opted out, through one `:not()` that excludes three things wherever they are stamped:
`data-kpress-math-text="katex"` on the wrapper or any ancestor, the wrapper’s baked
`data-kpress-fonts="system"`, and the reader’s persisted
`data-kpress-font-set="system"`, which the bootstrap stamps on `<html>`. An opted-out
wrapper keeps KaTeX’s own rules and the `1.05em` token untouched, so there is nothing to
revert and link order decides nothing.
The init script applies the metrics under the same three conditions, decided over every
math host on the page, since KaTeX’s tables are one setting per page; and when a host
wants the face but the tables cannot be applied, it stamps the opt-out on `<html>` so
the faces go with them.
The reader’s serif or sans prose choice does not change the math face; that is the
sans-math follow-up.

### Components

- `static/katex/katex-text-face.css`: kpress-authored, lazy with the math closure; the
  eight `@font-face` rules for `KPress Math Text`, the scoped size token, the scoped
  root family and class rules, with the specificity note.
  `style-tokens.css` and `components.css` are untouched.
- `static/katex/katex-text-metrics.js`: generated; listed in `KATEX_JS_ASSETS` before
  `katex-init.js`; part of the lazy math closure, so a document without math still loads
  nothing.
- `static/katex/katex-init.js`: apply the tables when present and the attribute says
  `prose`.
- `format/model.py`, `format/render.py`, `templates/page.html.jinja`, `contract.py`: the
  option, its stamping, the public-contract listing.
- `devtools/katex_text_metrics.py`: reads `katex.min.js` for the base tables and the
  reading-face woff2 files for the swapped entries, writes the asset; `--check` verifies
  the shipped asset is what the inputs produce.
  fontTools in the dev group.
- Docs: a “Math text face” subsection under Theme and Fonts in `kpress-design.md` (what
  is drawn from what, the contract for another face, the option); the host integration
  doc gains the two host hooks (faces and metrics) and the note for hosts that inline
  assets (below).

### Host Integration

A host that serves KPress assets by URL needs nothing: the composite names the same face
files the prose already uses, and the browser fetches each once.
A host that inlines every asset into one file (a self-contained page served from
`file://` or an artifact host) has two things to do: rewrite the composite’s
`../katex/fonts/…` sources as well as the `../fonts/…` ones when it inlines `@font-face`
blocks, and include `katex-text-metrics.js` before any script of its own that calls
`katex.render`, since the tables must be set before the first render.
Such a host pays for a second inlined copy of each reading face the composite names,
about 44 KB per face as base64.

### API Changes

- `RenderOptions.math_text_font: MathTextFont = "prose"`,
  `MathTextFont = Literal["prose", "katex"]`, exported through the public contract;
  `format. math_text_font` in document options.
- `data-kpress-math-text="prose" | "katex"` on the page root.
- CSS: the family name `KPress Math Text` and its slot contract (four style and weight
  pairs, disjoint ranges, reading face for U+0030–0039, U+0041–005A, U+0061–007A).
- JS: `globalThis.kpressKatexTextMetrics`, an object keyed by KaTeX face name whose
  values are complete KaTeX metric tables; read once by `katex-init.js`.
- Devtool: `python -m devtools.katex_text_metrics [--check]`.

## Implementation Plan

One phase; the steps are small and each is testable on its own.

- [x] Add fontTools to the dev group; write `devtools/katex_text_metrics.py` with
  `--check`; generate `katex/katex-text-metrics.js`; wire `--check` into `make lint`.
- [x] Add the eight `KPress Math Text` faces, the scoped size token, the root family and
  the class rules in `katex/katex-text-face.css`.
- [x] Add `math_text_font` to `RenderOptions`, the document options, the page shell
  attribute and the public contract; add the asset to `KATEX_JS_ASSETS`.
- [x] Apply the metrics in `katex-init.js` before rendering when the attribute is
  `prose`.
- [x] Tests (see Testing Strategy); refresh the goldens that record stylesheet sizes and
  hashes.
- [x] Document the feature and the host contract; one commit per step in the branch’s
  style.

## Testing Strategy

- Unit: the default is `prose`; `katex` and `prose` stamp the attribute; the public
  contract lists the option; `katex-text-face.css` declares eight `KPress Math Text`
  faces with the expected ranges and per-slot `size-adjust` values equal to the
  generator’s, points the six class rules at the composite, and scopes every rule on the
  three opt-outs.
- Metrics: `devtools.katex_text_metrics --check` passes against the shipped asset; a
  spot check that `Main-Regular` U+0031 carries PT Serif’s height (0.712) and width
  (0.533) and that U+002B is unchanged from KaTeX.
- JS (vitest): `katex-init.js` calls `__setFontMetrics` once per face before
  `renderMathInElement` when the attribute is `prose`, and not when it is `katex` or the
  font mode is `system`.
- Playwright: on a rendered page with `$s(10) = 3 + 1/\sqrt{2}$` and
  `$\frac{4001}{4000}$`, the advance of a rendered digit is 0.533 of the math font size
  (PT Serif) rather than 0.5 (KaTeX_Main); the numerator’s ink box lies inside the
  `.katex-display` box; with `math_text_font="katex"` both revert.
- Browsers: Chromium in the test suite; Safari and Firefox by hand or through
  Playwright’s WebKit and Firefox builds before the branch is considered done.

## Rollout Plan

On by default on `squares/page-fixes`. A document that wants the old look sets
`math_text_font: katex`. A host with another reading face follows the documented
contract. Upstreaming to `main` is decided after a consuming site has shipped with it.

## Open Questions

- Sans contexts: captions and labels set in Source Sans carry PT Serif math letters.
  Consistency of the math face across the document is the usual choice; restricting the
  scope to prose contexts is one selector if captions read better with the KaTeX faces.
- A `size-adjust` of 3–5% on the KaTeX faces inside the composite, so symbols keep a
  small lift while letters stay at prose size.
- Byte cost in a page that inlines every asset: the explainer grew from 1,177 KB to
  1,441 KB (three reading faces and three scaled Greek faces, its bold-italic slot being
  pruned as unreachable, plus the 32 KB metrics table).
  The upright Greek faces buy a 2–2.5% cap-height match for about 75 KB of that; if the
  cost matters more than the match, drop them and stop scaling the upright Greek entries
  in the generator together.
  The duplicate bytes themselves are `kpr-hhdc` under Font Consistency.
- Whether to upstream to `main`, and under what option name.
- The composite’s accents: the generator keeps KaTeX’s `skew` for the swapped italic
  letters, so `\hat{x}` over a PT Serif Italic `x` is placed for Computer Modern’s
  slant. Deriving skew from the reading face’s italic angle is a small follow-up if an
  accent ever looks off.

## Font Consistency

The owner’s rule (2026-09-07): a document resolves every text run to a face kpress
ships, on screen and in print, never to whatever the reader’s or the renderer’s machine
happens to have. The faces are PT Serif, Source Sans 3 (variable on screen, static in
print), the KaTeX faces and the composite, and a shipped mono.
Measuring the squares explainer PDF for the math text face showed where the rule was not
yet met:

| In the 946 KB PDF | Bytes | Why |
| --- | ---: | --- |
| PT Serif, embedded subsets | 92 KB | as intended |
| KaTeX faces, four embedded subsets | 25 KB | as intended |
| Source Sans 3 as Type3 outline paths, 17 fonts | 345 KB | Chromium cannot embed a variable font at a non-default weight |
| Menlo, 134 characters of inline code | 56 KB | kpress ships no mono face |
| Georgia, 48 list bullets | 16 KB | U+25AA is not in PT Serif’s latin subset |
| Helvetica, the atlas figure | 54 KB | its own pipeline; accepted |

The Type3 paths carry the right weight (a 410 stem is 0.083 em in the PDF and on
screen), but Preview smooths text drawn through the font machinery and not paths: with
Quartz font smoothing on, embedded faces gain 5–20% ink at 24–36 px and the paths gain
none, so the sans read a step lighter than the serif and the mathematics beside it.
On screen, LocalPunct borrows Georgia’s quotation marks into the prose stack when the
reader has Georgia, which the squares shell already refuses in print for the same
reason.

Tracked under epic `kpr-b4mq`:

- `kpr-w0s9`, in progress on this branch: static Source Sans 3 instances for print at
  the weights kpress’s sans contexts request, generated by `devtools/instance_sans.py`,
  declared in the generated `print-fonts.css`, led by `print.css` under print media.
  Hosts that override the weight tokens instance their own set; a host that inlines
  assets may supply them only at PDF time so its page’s bytes do not change.
  The exporter waits for the faces print layout asks for, and for the ones only the
  `@page` footer asks for, before it prints; without that wait a slow face prints as
  blank space.
- `kpr-v731`: vendor Source Code Pro, static 400 and 700, as the mono face and lead the
  mono stack with it; re-tune the mono size token by x-height; a fonts README recording
  provenance and licence for every vendored face.
  `kpr-aq8o` decides the final mono face against stated criteria; Source Code Pro stays
  until it does.
- `kpr-2tmj`: draw the list marker as a box, not a glyph.
- `kpr-asj4`: retire the LocalPunct borrowing so PT Serif sets its own quotation marks,
  keeping the borrowing only as an explicit host hook.
- `kpr-yxtu`, done on this branch: the mathematics paints once.
  `katex-init.js` loads the faces the mode will draw from before the first render, and
  the composite carries `font-display: block`, so a formula is never painted in
  KaTeX_Main and repainted in PT Serif.
  On a twenty-formula page over loopback the first `.katex` node was inserted at 70ms
  against composite slots decoding at 111–116ms; with the wait it is inserted at 129ms,
  after all of them. `rel=preload` hints were considered and refused: they would name the
  font URLs a second time in the page shell, would have to be gated on the document
  containing math, and would fetch KPress’s reading face on a host that has declared its
  own composite faces.
  See [kpress-design.md](kpress-design.md#math-text-face).
- `kpr-hhdc`: ship the composite’s faces as subsets.
  On an inlined page the six composite faces are 216 KB of base64, every byte a
  duplicate of a PT Serif or KaTeX blob already inlined under its own family; subsets
  should recover about 170 KB of it.

The consuming repository’s side is squares epic `think-phgo`: the PDF font guard that
fails on any family outside the shipped set (`think-xd7t`), subsetting the inlined KaTeX
faces to the page’s own glyphs (`think-f8q9`), and adopting the mono, marker and quote
changes when they land (`think-9r58`).

## Future Work

Recorded as a deferred bead under the epic (`kpr-7f9z`), not part of this plan:

- **Sans math.** When the reader chooses the sans reading face, or inside sans contexts,
  draw the letters and digits from Source Sans 3 with its own metrics: a second set of
  composite faces keyed on `data-kpress-prose-font="sans"` and a second metrics table
  from the same generator.

Greek sizing, once listed here, shipped inside the feature: the composite’s italic slots
scale KaTeX’s Greek to PT Serif’s x-height (115.0% and 112.6%) and the upright slots its
capitals to PT Serif’s cap height (102.5% and 102.0%), with the metric tables scaled by
the same factors, `\mathit`’s table included since its Greek is drawn by the italic
slot’s face. Browsers without `size-adjust` (before Chrome 92, Firefox 92 and Safari 17)
draw the Greek unscaled while laying it out scaled.

## References

- [Research: Harmonizing the Reading Face with KaTeX Mathematics](project/research/research-2026-09-07-math-text-face.md).
- Commit `ef3074c` (KaTeX sizing tokens), `components.css` “KaTeX sizing”, `assets.py`
  (`KATEX_JS_ASSETS`, the lazy math closure), `katex-init.js`.
- [KPress Design: Theme and Fonts](kpress-design.md#theme-and-fonts);
  [Operations and Host Integration](kpress-operations-and-host-integration.md).
- [CSS Fonts 4, composite fonts](https://www.w3.org/TR/css-fonts-4/#composite-fonts).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
