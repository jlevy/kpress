---
title: Math Text Face
description: Draw the letters and digits inside KaTeX mathematics from the reading face, with matching metrics, as a feature that is on by default and open to other faces
author: Claude (agent), for samanthadrakova@gmail.com
---
# Feature: Math Text Face

**Date:** 2026-09-07 (last updated 2026-09-07)

**Author:** Claude (agent), for samanthadrakova@gmail.com

**Status:** Implemented on `squares/page-fixes` (2026-09-07), with the sans composite on
`squares/sans-math`; Safari and Firefox checks by hand remain.

**Tracking:** epic `kpr-sc4f`; tasks `kpr-g93o` (metrics generator and asset),
`kpr-c4oz` (composite faces and rules), `kpr-ai4c` (option, attribute, wiring, init
hook), `kpr-mot3` (tests, goldens, docs), `kpr-7f9z` (sans math); deferred `kpr-c2tr`
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
- Where the words around the mathematics are sans -- a caption, a footnote, a table, the
  reader’s sans reading face -- the letters and digits come from Source Sans 3 instead,
  with its own metrics, so the mathematics is set in the face of the text it sits in.
- The vendored `katex.min.js` and `katex.min.css` stay byte-identical.

## Non-Goals

- Mathematics in a heading or the TOC of a *serif* document from Source Sans 3. Both are
  sans roles and both are left out, but for two unrelated reasons, and neither is the
  “both are set at the sans bold weight” one this plan first gave: a sans heading is at
  550 (`h3`) or 540 (`h4`) against tables built at 400, and the TOC receives no rendered
  mathematics at all. Recorded under Future Work.
  Under the sans reading face the whole document is sans and headings get the composite
  with everything else.
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

One composite CSS family, `KPress Math Text`, in four style and weight slots; a second,
`KPress Math Text Sans`, repeats it from Source Sans 3 for the sans roles and is
described under [Sans Mathematics](#sans-mathematics) below.
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

### Sans Mathematics

A serif document sets its captions, footnotes, tables and dialect boxes in Source Sans
3, and a reader can set the prose itself in it.
A second composite, `KPress Math Text Sans`, draws the same Latin ranges there.
The mechanism is the first one repeated; three things about it are new, and all three
come out of one fact measured in the
[sans brief](project/research/research-2026-09-07-sans-math-face.md): a KaTeX metric
table describes one face *and one weight*, and Source Sans is a variable face.

**Pinned weights.** Across the 370-700 axis the Latin advances move a median 7.1% and a
worst 20.5%, while the tallest ink height moves 0.035 em and the median 0.005 em.
The entries a metric table is for -- the heights and depths fractions, scripts and
radicals are laid out from -- are therefore nearly weight-invariant, and the widths are
not. So each slot declares a single `font-weight` rather than the whole axis, and its
table is built at that weight: CSS Fonts 4 clamps a variable face to the range its
`@font-face` declares, so the drawn weight is the table’s weight whatever the context
asks for.

The two weights are 400 for the regular slots -- upstream’s
`.katex { font: normal 1.21em ... }` resets `font-weight`, so mathematics in a sans
context is set at 400 either way -- and `--kpress-font-weight-sans-bold` (650) for the
bold slots, which `.mathbf` and `.boldsymbol` ask for instead of upstream’s 700, so
`\mathbf{D}` in a caption reaches the same bold as a bold word beside it.

| Sans slot | Source Sans 3 | KaTeX face for Greek, scaled, and next in the stack | Factor |
| --- | --- | --- | ---: |
| normal 400 | Variable, clamped to 400 | KaTeX_Main-Regular | 96.0% |
| italic 400 | Variable italic, clamped to 400 | KaTeX_Math-Italic | 110.2% |
| normal 650 | Variable, clamped to 650 | KaTeX_Main-Bold | 95.2% |
| italic 650 | Variable italic, clamped to 650 | KaTeX_Math-BoldItalic | 109.3% |

The upright factors are below 1, which the serif composite’s never were: KaTeX_Main’s
`H` is 683 per 1000 em against the 656 Source Sans 3 draws at 400, so the upright slots
pull the Greek capitals down rather than up.
That 4.1% is a ratio of *Latin* cap heights, which is what the generator derives the
factor from, and not a measurement of the Greek outlines, whose own heights fall either
side of it -- `devtools/katex_text_metrics.py` records the 5.7pp spread it leaves.
The numerator is the drawn `H` rather than the declared `sCapHeight`, because Source
Sans reports a weight-invariant 660 at every instance while the glyph it actually draws
is 656 at 400 and 653 at 650; `OS2_INK_TOLERANCE` at 0.003 is what catches that.

**Accents are outside every range and stay at 1.0.** No accent code point the bundle
uses -- `^` U+005E for `\hat`, `~` U+007E for `\tilde`, U+02C9 for `\bar`, U+00A8 for
`\ddot`, U+20D7 for `\vec`, U+02C7–U+02DA for the rest -- falls inside a slot’s ranges,
so every accent draws from the KaTeX face unscaled and the generator leaves its metric
row alone. Over a reading-face Latin base that is right.
Over Greek the base is scaled and the accent is not: `\hat{\alpha}` in a sans role gets
a correctly positioned circumflex 9.3% narrow for its base (1/1.102), and `\hat{\Gamma}`
one 4.2% wide (1/0.960); the serif composite carries the same residual and a larger one,
13.0% narrow (1/1.15) and 2.4% narrow (1/1.025). It is recorded rather than fixed.
[kpress-design.md](kpress-design.md#math-text-face) has why widening the Greek ranges to
cover the accent code points was the option not taken: one glyph and one table row serve
both kinds of base, so scaling them repairs the rare construct at the common one’s
expense, and scaling the drawn glyph without the row would put the accent in the one
state this design forbids.

**Print.** Chromium’s PDF writer turns a variable face away from its default position
into Type3 outline paths, which is why the sans role has static instances at all
(`kpr-w0s9`). The `KPress Print Sans` instances at the same two weights are layered over
the same ranges inside `@media print`, declared last so CSS Fonts 4’s last-defined-face
rule hands them to print and leaves the screen alone.
The family is the instances’ own, not Source Sans’s: the upstream licence reserves the
name “Source” for the original.
Instancing the variable face at 400 and 650 reproduces every Latin advance of the
shipped instance exactly, so one metric table is true of both — which is why the
generator measures the sans slots from those instance files.

**Scope.** The rules are scoped on the roles where a kpress stylesheet sets
`--kpress-font-sans`, `--kpress-font-footnote` or `--kpress-font-table` on running
author text, and on `data-kpress-prose-font="sans"`, under the same three opt-outs as
the serif rules and one class more specific, so the sans composite wins inside a sans
context and does not exist outside one.
A third scope is the footnote preview overlay, which `tooltips.js` mounts outside every
`.kpress`: it carries a clone of math already laid out from the sans tables, and a
footnote is a sans role in every mode, so drawing it in the serif composite would put PT
Serif glyphs on Source Sans boxes.
It is the one place the two engines are decoupled — nothing re-renders in an overlay, so
the per-node selection below never reaches it — and the cascade alone holds them
together. Two scopes, not three: the document reaches the composite through the
`data-kpress-math-face="sans"` mark `katex-init.js` stamps, which covers the reader’s
sans reading face as well, and the overlay reaches it by position and mode stamp.
That is what keeps the selectors inside the 400-character budget the consuming host’s
stylesheet check applies — measured the host’s way, on `len(prelude.strip())`, the
longest rule in the file is 339 and none reaches 400. Spelling the twelve roles into
every rule ran to 477. Headings and the TOC are left out; see Future Work.

**What can actually carry mathematics.** The scope is where the composite applies, which
is not the same as where an author can put an expression today, and the two differ
enough to matter before the feature is judged on a page.
A Markdown image caption is HTML-escaped in `format/markdown.py`
(`_render_paragraph_close`), so `![caption with $x$](img.png)` never produces
mathematics at all; the branch’s own test file notes it.
Rendering each of the other containers through the pipeline shows the rest.
The natural inline spellings -- a one-line `<figcaption>`,
`<p class="para-caption">...</p>`, `<details><summary>...</summary>` -- leave `$x$`
literal, because markdown-it consumes a line that opens with a block-level HTML tag as
an HTML block and never runs the inline parser over it.
The same containers written as raw-HTML blocks, with blank lines around their content,
do render, and so does an inline-level wrapper such as
`<span class="sans-text">$x$</span>`; blank lines rather than newlines are what decides
it. Tables and footnotes need none of that and are the roles the composite pays off in
today, so caption mathematics specifically has to be written in the block form.

**Per-node metrics.** `__setFontMetrics` replaces a table in the KaTeX singleton, so
only one set exists at a time.
The generated asset carries both -- the serif set as its own face keys, the sans set
nested under `sans` -- and the render loop installs the set matching each node before
rendering it, leaving the serif set installed afterwards.
The role list `katex-init.js` tests with `closest()` is the stylesheet’s, and a test
pins the two copies together.
Both sets are required: sans faces laid out from serif numbers is the same forbidden
state as faces without metrics, and a missing `sans` key stamps the same opt-out on
`<html>`.

**Operators** stay KaTeX here too, on the same three measurements as the serif brief’s
route H: Source Sans centres `+ - =` 0.080 em above KaTeX’s math axis, sets `+` on 0.497
em against KaTeX’s 0.778 em, and has no `\le` or `\ge`.

### Components

- `static/katex/katex-text-face.css`: kpress-authored, lazy with the math closure; the
  eight `@font-face` rules for `KPress Math Text`, the scoped size token, the scoped
  root family and class rules, with the specificity note; then the twelve for
  `KPress Math Text Sans` (eight on screen, four static instances under print) and its
  fourteen rules, seven per scope.
  `style-tokens.css` and `components.css` are untouched.
- `static/katex/katex-text-metrics.js`: generated; listed in `KATEX_JS_ASSETS` before
  `katex-init.js`; part of the lazy math closure, so a document without math still loads
  nothing. Both table sets live in it, the sans one nested under `sans`.
- `static/katex/katex-init.js`: apply the tables when present and the attribute says
  `prose`, choosing the set per rendered node from the stylesheet’s own role list.
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
- [x] Sans mathematics (`kpr-7f9z`): measure Source Sans against the KaTeX faces and
  along its own weight axis; add the sans face plans, tables and `--check` coverage to
  the generator; declare `KPress Math Text Sans` with its print instances; scope its
  rules on the sans roles and the sans reading face; select the table set per node in
  `katex-init.js`; tests and docs.

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
- Sans unit: the generator’s sans plans build at 400 and 650 and carry the sans Greek
  factors; the shipped tables give `1` Source Sans’s 0.497em advance at 400 and 0.520em
  at 650 and leave `+` alone; the stylesheet declares four sans slots with single-valued
  weights, four static instances under `@media print` over the same ranges, and
  `size-adjust` values equal to the generator’s; every sans rule carries the three
  opt-outs and stays inside the selector budget; the role list in `katex-init.js` equals
  the stylesheet’s.
- Sans JS (vitest): a caption node is rendered with the sans tables installed and a
  prose node with the serif ones, the serif set is left installed afterwards, `sans` and
  `scale` are never installed as faces, and an asset without a `sans` key turns the face
  off.
- Sans Playwright: on a page with the same expression in prose, in a table cell and in a
  footnote, `CSS.getPlatformFontsForNode` reports PT Serif for the prose digits and
  Source Sans for the other two, a `KPress Print Sans` instance for the table under
  print media, Source Sans again inside the footnote preview overlay opened from that
  page, and KaTeX’s vertical list for the fraction is shorter in the sans roles than in
  prose.
- Browsers: Chromium in the test suite; Safari and Firefox by hand or through
  Playwright’s WebKit and Firefox builds before the branch is considered done.

## Rollout Plan

On by default on `squares/page-fixes`. A document that wants the old look sets
`math_text_font: katex`. A host with another reading face follows the documented
contract. Upstreaming to `main` is decided after a consuming site has shipped with it.

## Open Questions

- A `size-adjust` of 3–5% on the KaTeX faces inside the composite, so symbols keep a
  small lift while letters stay at prose size.
- Byte cost in a page that inlines every asset: the explainer grew from 1,177 KB to
  1,441 KB (three reading faces and three scaled Greek faces, its bold-italic slot being
  pruned as unreachable, plus the metrics table, 32,622 B at the time of that
  measurement); the sans composite adds the two variable faces again, the four static
  instances a printed copy uses, and a second metrics table.
  The upright Greek faces buy a 2–2.5% cap-height match for about 75 KB of that; if the
  cost matters more than the match, drop them and stop scaling the upright Greek entries
  in the generator together.
  The duplicate bytes themselves are `kpr-hhdc` under Font Consistency.
- Byte cost in a page that links its assets, which is the ordinary case and the one the
  sans composite makes concrete.
  `katex-text-metrics.js` is 69,455 bytes against the serif-only asset’s 34,960, or
  11,336 against 6,032 gzipped, so the sans tables are +5,304 bytes gzipped;
  `katex-text-face.css` adds a few kilobytes more, most of it comment, and under half a
  kilobyte gzipped once comments are stripped.
  Both files are linked on every page with any mathematics, whether or not that page has
  mathematics in a sans role, so the first visit pays roughly 8–9 KB gzipped and every
  later one pays nothing: the files are cacheable, no `@font-face` URL is new, and the
  rendered HTML is byte-identical either way.
  Making it lazy needs a `has_sans_math` beside `has_math` through `format/markdown.py`,
  `format/model.py` and `format/render.py`, the sans set in a file of its own, and
  `applyTextMetrics` in `katex-init.js` taught to accept one set rather than requiring
  both. Deliberately not done here; filed as a follow-up.
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

- `kpr-w0s9`, landed on `main`: static `KPress Print Sans` instances for print at the
  weights kpress’s sans contexts request, generated by `devtools/instance_sans.py`,
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

Not part of this plan:

- **Mathematics in a heading.** A heading is a sans role, but not at a weight either
  composite has a table for.
  `css/document.css` gives `h3` `--kpress-font-weight-sans-medium` (550) and `h4` 540,
  and the shared `h1`–`h6` rule’s `--kpress-font-weight-sans-bold` (650) is overridden
  at every level; `h1`, `h2`, `h5` and `h6` re-declare `--kpress-font-prose` and are not
  sans at all, `h2` being serif italic 400. Drawing a heading’s mathematics from the
  sans composite would set it at the pinned 400 against 550 or 540 words, and routing it
  to the bold slots instead is not possible with a per-class table: KaTeX picks the
  table from the TeX, not from the CSS. A third pair of slots pinned at the heading
  weights would be the honest fix, at the cost of another face and another table for
  each.
- **Mathematics in the TOC** is not future work at all, because the TOC never receives
  any. `_plain_inline_text` in `format/markdown.py` keeps only the `text` and
  `code_inline` children of a heading’s inline token, so a `math_inline` token is
  dropped before `Heading.title` exists, and `_render_toc` in `format/render.py` escapes
  what is left. A heading written `## Bound with $x$ inside` reaches the TOC with the
  expression simply absent from its title.

Sans math, once listed here, shipped as its own subsection above (`kpr-7f9z`). Greek
sizing, also once listed here, shipped inside the feature: the composite’s italic slots
scale KaTeX’s Greek to PT Serif’s x-height (115.0% and 112.6%) and the upright slots its
capitals to PT Serif’s cap height (102.5% and 102.0%), with the metric tables scaled by
the same factors, `\mathit`’s table included since its Greek is drawn by the italic
slot’s face. Browsers without `size-adjust` (before Chrome 92, Firefox 92 and Safari 17)
draw the Greek unscaled while laying it out scaled.

## References

- [Research: Harmonizing the Reading Face with KaTeX Mathematics](project/research/research-2026-09-07-math-text-face.md).
- [Research: Source Sans 3 Inside KaTeX Mathematics](project/research/research-2026-09-07-sans-math-face.md),
  which measures the sans composite and fixes its two build weights.
- Commit `ef3074c` (KaTeX sizing tokens), `components.css` “KaTeX sizing”, `assets.py`
  (`KATEX_JS_ASSETS`, the lazy math closure), `katex-init.js`.
- [KPress Design: Theme and Fonts](kpress-design.md#theme-and-fonts);
  [Operations and Host Integration](kpress-operations-and-host-integration.md).
- [CSS Fonts 4, composite fonts](https://www.w3.org/TR/css-fonts-4/#composite-fonts);
  [matching font styles](https://www.w3.org/TR/css-fonts-4/#font-style-matching), for
  the clamping rule the sans slots’ pinned weights rely on.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
