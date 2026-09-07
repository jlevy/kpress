---
title: "Research: Harmonizing the Reading Face with KaTeX Mathematics"
description: Why Computer Modern math sits uneasily beside PT Serif, what LaTeX and the web renderers do about it, which CSS mechanisms apply, and what each route looks like on a rendered paper
author: Claude (agent), for samanthadrakova@gmail.com
---
# Research: Harmonizing the Reading Face with KaTeX Mathematics

**Date:** 2026-09-07 (last updated 2026-09-07)

**Status:** Complete; the feature it recommends is planned in
[Math Text Face](math-text-face.plan.md).

## Overview

KPress sets prose in PT Serif; the mathematics is typeset by KaTeX 0.16.45, whose faces
derive from Computer Modern.
The pairing works, but not invisibly: inline math reads a shade lighter and a shade
smaller than the words around it, and the effect is strongest on lines that alternate
between a variable, a number and a word.

This brief answers whether the *letters and digits* inside mathematics can be drawn from
the reading face while operators, relations, delimiters, radicals and Greek stay in the
KaTeX faces, and what that costs.
Three questions sit under it: what KPress does today, which measurable properties of the
two faces the eye is reacting to, and what prior art exists in the LaTeX world, in the
web math renderers and in CSS font technology for exactly this move.

The short answer: yes, and it is an established compromise with a well-documented shape.
LaTeX has done it for thirty years, from `mathptmx` to `mathastext`; the web renderers
mostly cannot, because they lay out from metric tables baked in at build time; but
KPress vendors KaTeX and owns its stylesheets, so a CSS composite family plus a small
metrics table gives the result the LaTeX packages give, with the same caveats they
document.
Eight prototype variants were rendered on a KPress-set paper and compared at 3×
to confirm it.

## Questions to Answer

1. How does KPress load its faces today, and where is the size of mathematics decided?
2. Which metrics differ between PT Serif and the KaTeX faces, and which of those
   differences does the eye read as disharmony?
3. Is drawing letters and digits from the text face inside mathematics an established
   practice, and which pitfalls are documented (LaTeX, MathJax, KaTeX, MathML Core)?
4. Which CSS mechanisms route code points to different faces and align their metrics,
   and which browsers support them?
5. What does each candidate route look like on a real document, and what does it cost in
   code, bytes and risk?

## Scope

Included: the KPress stylesheets and the vendored KaTeX; screen rendering in Chromium
and the print path headless Chromium produces; the Latin subset of PT Serif that KPress
ships. Excluded: designing or commissioning a math companion for PT Serif; changing the
reading face; replacing KaTeX, unless the evidence says the replacement is the cheaper
route (it does not, see the web renderers section).
Greek from the reading face is out of reach by construction: the PT Serif webfont KPress
ships is a 236-glyph Latin subset with no Greek, so `\theta` and `\pi` stay Computer
Modern on every route.

## Findings

### How KPress loads its faces today

KPress declares PT Serif four times (400 and 700, upright and italic), each block
carrying a Latin `unicode-range`, plus a `LocalPunct` face whose `src` is
`local("Georgia")` and whose range is the six quotation marks, and a variable Source
Sans 3 for the sans contexts.
The prose token is `--kpress-font-prose: "LocalPunct", "PT Serif", …`; the print
stylesheet drops `LocalPunct` so a printed file does not depend on which fonts the
reader owns. KaTeX is a lazy per-document asset: its stylesheet, scripts and faces are
emitted only for documents that contain math, and `katex.min.css` is linked after
KPress’s own stylesheets.

KaTeX’s own root rule is
`.katex { font: normal 1.21em KaTeX_Main, Times New Roman, serif }`. KPress overrides
the size (commit `ef3074c`, “size KaTeX to PT Serif rather than to KaTeX’s Times
default”) with three tokens: `--kpress-katex-size-prose: 1.05em`,
`--kpress-katex-size-sans: 1em`, `--kpress-katex-size-display: 1.1em`. Inline math is
seated with `vertical-align: baseline`.

The 1.21em itself has no recorded rationale.
It is in KaTeX’s first named commit (2013) with no explanation; the maintainers’ own
issue on it (#329, still open) says “MathJax uses a 116% font size multiplier … people
should be adjusting this size to match the font that it surrounds”; Distill ships 1.18em
and Observable moved toward 1.08em for a 17px body.
The story that it matches Times to Computer Modern appears in no source and should be
treated as folklore.

What KaTeX draws from which face is decided by class, and the class map is the whole
constraint on any CSS route (from the vendored `katex.min.css`):

| KaTeX class | Face | What lands there |
| --- | --- | --- |
| `.mathnormal` | KaTeX_Math italic | Latin variables (`n`, `s`, `t_k`) |
| `.mathit` | KaTeX_Main italic | `\mathit` |
| `.mathbf` | KaTeX_Main bold | `\mathbf{D}` |
| `.boldsymbol` | KaTeX_Math bold italic | `\boldsymbol` |
| `.textrm`, `.mainrm` | KaTeX_Main | `\textrm`, the upright fallback |
| `.mathrm` | *sets `font-style: normal` only* | `\mathrm`, family inherited from the root |
| `.text` | *no family* | `\text{…}`, family inherited from the root |
| `.amsrm`, `.mathbb` | KaTeX_AMS | blackboard bold, AMS symbols |
| `.delimsizing.sizeN`, `.op-symbol` | KaTeX_Size1–4 | stretched delimiters, `\sum` |
| *(no class)* | root `.katex` font, KaTeX_Main | **digits**, `+ − = < ( ) , .`, `\ldots`, operator names such as `tan` and `arctan`, upright Greek capitals |

The last row is the important one.
Digits and operator names carry no font class of their own; they are drawn by whatever
family the root `.katex` rule names, and so is `\text{}`, which does not inherit the
page font (KaTeX’s maintainers: “no, it’s not configurable”). So “digits from PT Serif,
operators from KaTeX” cannot be expressed by class at all.
It needs a family that answers differently per code point, which is what `unicode-range`
composites are for.

### The metrics, measured

Measured with fontTools from the woff2 files KPress ships and from the macOS system
copies of three reference faces, in units of 1/1000 em.
“Operator centre” is the vertical centre of the minus sign, which is the math axis a
font’s own operators sit on; “hairline” is that sign’s stroke thickness; “stem” is the
width of the vertical of `l` at half x-height; the `o` column is the thick side of a
round letter, so stem against hairline is the face’s contrast.

| Face | x-height | Cap height | Digit height | Ascender (`l`) | Operator centre | Hairline | Stem `l` | `o` stroke |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PT Serif Regular | 500 | 700 | 712 | 752 | 344 | 53 | 90 | 96 |
| PT Serif Italic | 507 | 700 | 712 | 752 | 344 | 53 | 88 | 91 |
| PT Serif Bold | 500 | 700 | 712 | 752 | 344 | 80 | 144 | 155 |
| KaTeX_Main-Regular | 442 (ink 431) | 683 | 666 | 694 | 250 | 40 | 81 | 98 |
| KaTeX_Math-Italic | 441 | 683 | old-style 452, unused | 694 | — | — | 83 | 96 |
| KaTeX_Main-Bold | 450 | 686 | 654 | 694 | 251 | 60 | 123 | 143 |
| Times New Roman | 447 | 662 | 676 | 694 | 333 | 40 | 81 | 92 |
| STIX Two Math | 473 | 657 | 642 | 706 | 259 (MATH `AxisHeight` 258) | 68 | 83 | 93 |
| Georgia | 481 | 693 | old-style 540 | 756 | 273 | 61 | 91 | 101 |

None of the KPress or KaTeX faces carries an OpenType `MATH` table; KaTeX’s own x-height
constant is 0.431 (from `cmsy10`) and its `axisHeight` is 0.25. Four things follow, and
together they are the whole diagnosis.

**No single scale factor can match PT Serif.** PT Serif’s x-height is 0.714 of its cap
height; Computer Modern’s is 0.647. At 1.05em, math lowercase is 7% shorter than the
prose lowercase, math capitals are 2% taller, and math digits are 2% shorter.
Matching x-heights would take 1.131em, and would push capitals 10% and digits 6% over
the prose. The 1.05em KPress chose is a fair split of an unsplittable difference.
This is what reads as “the baseline is a little different”: the baselines are aligned
exactly, and what differs is how far above the baseline the lowercase reaches.

**Scaling cannot fix weight.** PT Serif’s stems are 10–18% heavier than Computer
Modern’s and its hairlines a third heavier, so its contrast is about 1.8 against
Computer Modern’s 2.5. Beside PT Serif, Computer Modern is spindly at any size.
Michael Sharpe’s newtx documentation names this directly: its math fonts target text
faces “intermediate in weight between Computer Modern and Times”, and a low-contrast
face like Libertine “appears denser than Computer Modern but not as much so as Times”.
PT Serif is on the dense side of Times.
This is why route F below, which scales the math italic until its x-height meets PT
Serif’s, looks worse rather than better.

**PT Serif’s operators must stay out of the mathematics.** Its `+`, `−` and `=` are
centred at 344, close to Times at 333; KaTeX’s are centred at 250 and every fraction
bar, stretched delimiter and big operator KaTeX draws is centred on that axis.
A PT Serif minus sign in a KaTeX line would sit 0.094em, nearly two pixels at 18px,
above the bar of the fraction next to it, and PT Serif has no `≤` or `≥` at all, so a
relation would come from one face and the equals sign beside it from another.
Route H rendered exactly that and confirmed it.
Letters and digits are the whole of what should move.

**Digits are the strongest single fix.** A figure like 3.8770835 in Computer Modern sits
between PT Serif words with lighter strokes and narrower advances (500 against 533 per
em); the same digits from PT Serif are indistinguishable from a number in the prose,
which is what a reader of a paper expects, since the numbers are the point.

### How KaTeX chooses and lays out glyphs

KaTeX is a metrics-table renderer.
It lays out from a table embedded in `katex.min.js`: per face and per code point,
`[depth, height, italic correction, skew, width]` in em, generated by the project’s
Docker build from the TeX `.tfm` files of Computer Modern.
Horizontal runs of ordinary glyphs are left to the browser’s inline flow, so a wider
glyph from another face simply takes its width.
Vertical layout is not: struts, fractions (`num1..3`, `denom1..2`), sub- and
superscripts (`sup1..3`, `sub1..2`, the base glyph’s height, depth and italic
correction), radicals and accents (the base glyph’s `skew`, the `xHeight` clearance) are
all positioned from the table.
The maintainers are explicit that this is the design: “KaTeX has detailed metrics for
the glyphs in the KaTeX font, so it can work with those metrics.
In order to use another font, one would have to first extract the metrics for each glyph
in the font and make that data available to KaTeX” (ronkok, issue #1702), and “The use
of a different font would be a major project” (discussion #3716). Issue #123,
“Alternative font support”, has been open since 2014.

The consequence for any CSS-only route is measurable.
PT Serif digits are 0.046em taller than the Computer Modern digits KaTeX believes it is
placing, so a numerator overflows the box KaTeX computed by about a pixel at 18px.
Display padding usually masks it, and in inline math it is invisible, but it is real: at
3× device scale the element screenshot of `4001/4000` clips the tops of the numerator on
every CSS-only variant and on neither of the metric-aware ones.
Two published attempts at CSS-only font swaps report the same class of defect at larger
scale: an inherited-font hack where “the last letter of *mol* intersects the minus sign
of the superscript”, and a Roboto swap whose “hat accents are misplaced” until metrics
were supplied.

There are two ways to supply metrics without a custom KaTeX build, and both were checked
against the vendored bundle:

- The table is plain data in `katex.min.js` (`"Main-Regular":{48:[0,.64444,0,0,.5],…}`)
  and a build step can rewrite the entries for the swapped code points.
  Route G below does this: 228 entries across Main-Regular, Main-Italic, Math-Italic and
  Main-Bold, each rewritten from PT Serif’s glyph bounds and advance.
- KaTeX exports `katex.__setFontMetrics(fontName, table)`, which replaces the table for
  one face at runtime (verified: `function(e,t){Ur[e]=t}` in the bundle).
  There is no getter, so a page emits a complete merged table and calls the hook before
  rendering. This keeps `katex.min.js` byte-identical, which is the constraint KPress
  already applies to `katex.min.css`, and is the mechanism to prefer.

### What the routes look like on a document

Eight variants of a KPress-rendered paper (the squares `s(11)` explainer, a
fourteen-page document dense with inline and display math) were built by injecting CSS
(and for G, patched metrics) into the rendered page, served locally, and screenshotted
at 3× in Chrome with Playwright: the same four paragraphs and three display equations in
each.
The composite families use *disjoint* `unicode-range`s, so nothing depends on which
face wins an overlap.

| Route | What changes | Verdict from the screenshots |
| --- | --- | --- |
| A, current | nothing | Math visibly lighter and lower-waisted than the prose; digits in a sentence do not match the digits in the sentence before |
| B, digits and upright text | root `.katex` family becomes a composite, PT Serif for U+0030–0039 and KaTeX_Main for all else; `.mathrm`, `.textrm`, `.mainrm` to PT Serif | Numbers now match the prose; the `+ = <` beside them look a little thinner than before by contrast; variables still Computer Modern |
| C, B plus variables | `.mathnormal` to PT Serif Italic | `n`, `s(n)`, `t_k`, `B` sit at the prose x-height and weight; Greek and operator names still Computer Modern, which shows in `2 arctan t_k` |
| D, all Latin letters and digits | composite covers digits and A–Z, a–z; `.mathit`, `.mathbf`, `.boldsymbol` to the matching PT Serif faces | The most consistent line: `arctan`, `tan`, `\mathbf{D}_4` all read as the prose face; only symbols and Greek are Computer Modern, and the eye accepts that |
| E, D at 1em | `--kpress-katex-size-prose: 1em` | Letters and digits are now exactly the prose size, as they should be once they are the prose face; the KaTeX symbols shrink 5% with them and still read correctly |
| F, B plus size-adjusted math italic | `@font-face` for KaTeX_Math with `size-adjust: 113.4%` | The x-heights match but capitals and ascenders balloon and lines reflow; the stroke stays thin. Eliminated |
| G, D plus patched metrics | KaTeX’s table rewritten for the 228 swapped code points from PT Serif’s bounds | Identical to D inline; in display fractions the numerator box now contains the glyphs and the bar clearance is what KaTeX intends |
| H, D plus operators | `+ − = < >` from PT Serif too, as `mathastext` does in LaTeX | PT Serif’s `=` is two thirds the width of KaTeX’s and sits higher; `≥ 381/100 = 3.81` mixes a wide light relation with a narrow dark equals. Eliminated |
| J, the recommendation plus scaled Greek | inside the italic slot, a KaTeX_Math-Italic face restricted to the Greek range with `size-adjust: 113.4%` (lowercase to PT Serif’s x-height); in the upright slot, KaTeX_Main’s Greek capitals at 102.5% (to its cap height); the Greek entries of the metrics table scaled by the same factors | `θ_k`, `π/4` and `μ(Q)` now reach the height and nearly the weight of the PT Serif letters beside them, with the ascender of `θ` a shade above `t`; two `@font-face` rules and a scale parameter. Reads as an improvement; a visual decision rather than a measured one |

Route J is the Greek follow-up prototyped early: since the composite already owns the
italic slot, giving its Greek range a scaled face is the same mechanism with one more
rule, and scaling by the x-height ratio also thickens the strokes by the same 13%, which
brings Computer Modern’s Greek closer to PT Serif’s weight as well as its height.

Two details from the screenshots that an implementation has to carry:

- The PT Serif italic is a text italic, not a math italic: it has no italic correction
  of its own and no cursive `f`, so a function name set against a parenthesis, as in
  `s(11)`, wants a thin kern (`\mkern1mu`) in the source or an italic correction in the
  metrics table. This is the pitfall every LaTeX source documents (below).
- The composite leaves everything that is not a Latin letter or digit to KaTeX_Main, so
  punctuation inside math (`,` `.` `…`) remains Computer Modern.
  At reading sizes the difference is not visible; a range that also took `, .` from PT
  Serif would be a one-line follow-up if it ever is.

Byte cost: the PT Serif faces are 29–35 KB each as woff2, 40–47 KB as base64. In hosted
asset modes the composite costs nothing extra, since the browser fetches each face file
once however many `@font-face` rules name it.
A host that inlines every face as a data URI pays for a second copy of each face the
composite names: about 80 KB for a composite that pairs PT Serif Regular with
KaTeX_Main, or 44 KB per PT Serif face if the reading faces are overlaid into the KaTeX
families themselves.

Print: headless Chromium’s PDF path is the same Blink and Skia as the screen.
Exporting the eight-route test document through its print pipeline gave the same page
count, a clean print layout and byte-for-byte self-agreeing renders; in the file, the
math letters and digits come from the PT Serif subsets the prose already embeds, at the
prose size, while the symbols still come from the embedded KaTeX faces, and the file is
smaller because `KaTeX_Main-Bold` is no longer needed.

### Prior art in LaTeX

Mixing text-font letters and digits into mathematics is standard practice in LaTeX, in
two forms, and the documentation is candid that it is a compromise.

**Packaged mixtures.** `mathptmx` uses Times for Latin letters and Symbol for Greek and
other symbols; `mathpazo` does the same with Palatino; `fouriernc` sets New Century
Schoolbook letters with Fourier symbols; and Sharpe’s `newtxmath` has a dozen options
(`libertine`, `charter`, `xcharter`, `cochineal`, `stix2`, `ebgaramond`, `minion`,
`garamondx`, `baskervaldx`, `utopia`, …) each of which “loads different versions of math
italic and bold math italic based on X rather than Times” while operators, relations and
delimiters stay newtx.
In these the letters are re-metricized by the package author, and even so the TeX FAQ
says of the `mathptmx` mixture that it “is not entirely acceptable, but can pass in many
circumstances”. Even so, newtx’s letter swaps need per-letter repairs: `alty` for
Charter’s long-tailed `y`, `noxchvw` because Charter’s `v` reads as `\nu`, `cochf` to
restore the long text italic `f`.

**User-level mixtures.** Three packages take letters and digits directly from an
arbitrary text font:

- `mathastext` (Burnol) takes `a–z A–Z 0–9` and, by default, the punctuation and the
  base-size operators
  `! ? , . : ; + - = ( ) [ ] / < > | { } \`, using the en dash for minus. It leaves the prime, big operators and any delimiter above base size to the math fonts, and has `noplusnominus`, `noequal`, `noparenthesis`and`basic`
  (letters and digits only) to narrow the take.
  Its README opens: “Optimal typographical results for documents containing mathematical
  symbols can only be hoped for with math fonts specifically designed to match a given
  text typeface”, and promises output “perhaps not of the highest typographical quality,
  but at least not subjected to obvious visual incompatibilities between your text font
  and the math fonts”.
- `unicode-math` (Xe/LuaLaTeX) takes ranges: `\setmathfont{…}[range=up/{num}]` for
  digits, `range=up/{latin,Latin}` and `range=it/{latin,Latin}` for upright and italic
  letters, and its manual calls numerals from a specific font “A common request”.
  fontspec’s `Scale=MatchLowercase` scales the imported face to the document font’s
  x-height; `MatchUppercase` to its cap height.
- `mathspec` (XeLaTeX, older) does the same with
  `\setmathsfont(Digits,Latin)[Scale= MatchLowercase]{…}` and states the scope plainly:
  arrows and operators “whose designs are largely independent of an alphabetic typeface”
  are left to a math collection.

**What the documentation says goes wrong.** The narrow form, upright material only, is
the least controversial: unicode-math keeps `\mathrm` in sync with the text font by
default, and newtx already takes operator names and lining figures from the text face.
Taking *italic variables* from a text italic is where every source documents trouble,
and the trouble is exactly the metrics problem above:

- A text italic “extends way out of its declared bounding box”, and TeX only inserts
  italic correction automatically when the font’s interword-space parameter is zero,
  which is true of math italics and false of text italics; subscripts ignore it entirely
  (`mathastext` §1.8.2). `mathspec` §6 shows the symptom: “the function *f* is too close
  to the parenthesis” and an exponent that collides with its base, “because the font has
  metrics that are suitable for use in text, but not for mathematics”.
- Ligatures: `\mathit{ff}` forms a ligature in a text italic.
- Sizes: text fonts have no optical sizes, so `mathastext` sets script sizes to 10/8/6
  instead of LaTeX’s 10/7/5 because the defaults “give for subscripts of subscripts
  barely legible glyphs”.
  KaTeX scales its single-size faces by 0.7 and 0.5 for the same reason with the same
  cost; PT Serif’s larger x-height helps a little at script size, its hairlines thin
  exactly as Computer Modern’s do.
- The practical advice from the tex.stackexchange record is narrower than the packages
  allow: take only the letters that clash (`u v w`) and scale the text face so the
  x-heights agree (a measured 4.57pt against 4.42pt, factor 1.0342), or expect that “all
  accents need to be manually adjusted every time they are used”.

**What makes a pair harmonious.** The parameters the literature names, in the order they
show: x-height (the “match x-heights, not em sizes” rule: fontspec’s `MatchLowercase`,
MathJax’s ex-height matching, Sharpe’s 450/432 and 17% figures); weight and contrast
(Sharpe on Libertine’s density; Jackowski on TeX Gyre Math: “even essentially
geometrical shapes should also reflect the characteristic features of the main font, for
example, the thickness of stems”); rule thickness, which the OpenType MATH specification
recommends equal to the minus sign’s; the math axis (`σ22`, `AxisHeight`), on which
operators and fraction bars centre while letters sit on the baseline; the script shift
parameters, which Vieth derives from x-height and ascender and warns “different font
designs will also have different proportions … which could also have side-effects on the
calculations”; and figure style, since old-style digits leak into math unless a lining
set is chosen.
PT Serif’s default digits are lining figures (712 high), so the last point
is moot here.

**PT Serif specifically.** No published pairing exists.
The `paratype` CTAN package provides text support only and names no math companion; the
LaTeX Font Catalogue lists it without math support; newtx, `fontsetup` and Vieth’s 2023
survey never mention it.
Any pairing is KPress’s own, and the verified method is Sharpe’s: compare x-height, cap
height and stem weight and scale one side, which is what the size token does and what
the metrics table above quantifies.

### Prior art in the web renderers

**KaTeX.** No supported route.
The community practice is to tune `.katex { font-size }` to the body face and, at most,
override `\text{}` by CSS; overriding `.mathnormal` and digits by CSS is done by
hobbyists and produces the documented collisions unless metrics are supplied.
One published case did supply them: Yingtong Li (2022) redefined the alphanumerics with
`katex.__defineSymbol`, injected fontTools-extracted metrics with
`katex.__setFontMetrics`, and set the families by CSS, which is the shape route G takes.
A pull request adding an opt-in browser `math` font (#4129, 2026) is unmerged.
Serlo, an education platform, gave up on font switching and prefixes every formula with
`\sf` to use KaTeX’s own sans face.

**MathJax 3 and 4.** `mtextInheritFont: true` (or `mtextFont: "PT Serif"`) sets
`\text{}` in the surrounding font *and* measures it in the DOM, so its layout is
correct; that is the only content the option covers.
Digits and `\mathrm` cannot be redirected.
The CHTML output matches ex-heights automatically (`matchFontHeight`). MathJax 4 ships
eleven font packages (New Computer Modern by default, plus Latin Modern, STIX Two, TeX
Gyre Termes/Pagella/Bonum/Schola, DejaVu, Fira, Asana, the original TeX faces), and its
docs promise a tool to “replace the letters and numbers with a different font while
leaving all the rest of the characters unchanged”; as of MathJax 4.1.3 (July 2026) it
has not shipped, and the docs state “Mixing multiple fonts is currently not supported”.
Switching KPress to MathJax would buy correct `\text{}` and a choice of math face, at
the cost of a full font family and a new pipeline, and would still not give PT Serif
digits.

**Temml and MathML Core.** The one route where text-font letters and digits are
first-class and metric-correct.
The browser lays out MathML from an OpenType `MATH` font chosen by CSS, and the MathML
Core user-agent stylesheet puts `font-family: math` on `<math>` only, with no rule on
`mi`, `mn`, `mo` or `mtext`; so a page may write `mtext, mn { font-family: "PT Serif" }`
and the browser lays those runs out with PT Serif’s real metrics while `mi` and `mo`
keep the math font (Firefox settled on fonts-on-`<math>`-only in 2015 for exactly this
reason: a forced `mtext` font “isn’t going to match what is used in the text surrounding
the math”). Temml, by KaTeX’s co-maintainer, produces such MathML from TeX; its
`\text{}` emits a bare `<mtext>` that would inherit the math font unless the page rules
otherwise. Costs: a `MATH` webfont must be shipped (Latin Modern Math is 380 KB;
Chromium’s `math` generic resolves to a single preference font, so a page cannot rely on
the system), Temml’s own table lists rendering bugs in Chromium and WebKit for
extensible arrows, radical degrees and flattened accents, and `font-family: math`
reached Firefox only at 149 and Safari at 26.2. This is the right long-term answer for
the web and the wrong one for KPress today.

**Real-world CSS.** Distill.pub harmonizes by size and color only
(`span.katex { font-size: 1.18em; color: rgba(0,0,0,0.8) }`); ar5iv sets
`math, mjx-container` to STIX Two Math and says why (“proper subscript metrics”);
Wikipedia’s Math extension ships no font rules at all; Quarto, Pandoc and mdBook pass
KaTeX or MathJax through untouched.
No published site or library composes a text face with a math face by `unicode-range`;
the nearest thing is the CSS Fonts specification’s own STIXGeneral example, which
composes math symbol ranges into one family.

### CSS mechanisms and browser support

**`unicode-range` composites.** The standard mechanism, universally supported (Chrome 1,
Firefox 36, Safari 3.1). Several `@font-face` rules with the same `font-family`,
`font-style` and `font-weight` but different `unicode-range` values are one composite
face. The CSS Fonts 4 rules that matter: style matching happens *before* ranges are
consulted, so a PT Serif italic overlay joins the italic composite and never the upright
one; when ranges overlap, “the last rule defined is the first to be checked for a given
character”; a face whose range includes a code point but whose file lacks the glyph is
skipped and the next face in the composite tried; and if no face in the composite has
the glyph, matching moves to the next *family* in the stack, never to another style.
The “first available font” (which sets `ex`, `line-height: normal`, `from-font`) is the
first face whose range includes U+0020, so an overlay that excludes the space leaves
KaTeX_Main as the element’s reference font.
Two ways to write it: a new family name with disjoint ranges (what the prototype did;
independent of source order) or an overlay declared into `KaTeX_Main` itself after
KaTeX’s rule (fewer bytes when inlined; depends on order).
Google Fonts and Fontsource ship PT Serif itself as four-subset composites, so the
pattern is already in the file.

**Metric descriptors.** `size-adjust` (Chrome 92, Firefox 92, Safari 17) scales one
face’s outlines, advances and vertical metrics about the baseline; it worked live in
route F. `ascent-override`, `descent-override` and `line-gap-override` (Chrome 87,
Firefox 89) replace a face’s line metrics; Safari has not shipped them (WebKit landed
the implementation on 2026-08-06, after Safari 26.6). None of the four moves a glyph
relative to the baseline; only `vertical-align` or a positioned wrapper can, and nothing
here needs to. For this design the descriptors are optional: the letters are the prose
face at 1em, so PT Serif needs no adjustment, and the one refinement they offer is a
`size-adjust` of a few percent on the *KaTeX* faces so the symbols keep a small lift
while letters stay exactly prose size.

**`font-size-adjust`.** The two-value form and `from-font` (Chrome 127, Firefox 118,
Safari 17) rescale *each* face used in an element so a chosen metric matches, without
touching `em` units or a numeric `line-height`. It is the Safari-safe alternative to
`size-adjust` but the wrong tool here for two reasons: it applies to every face in the
subtree, and KaTeX_Size1–4 and KaTeX_AMS declare an x-height of zero, so it would have
to be scoped away from delimiters and AMS symbols; and it cancels `size-adjust` on the
same text.

**Vertical metrics.** Two faces on one line share a baseline by construction; the line
box grows to the tallest ascent and deepest descent (CSS Inline 3). PT Serif’s hhea,
typo and win metrics agree (1039/−286); the KaTeX faces have hhea equal to win (903/272
for Main) with typo 800/200 and the `USE_TYPO_METRICS` flag off, so every shipping
engine, FreeType in headless Chromium included, uses hhea.
It does not matter here: KaTeX sets `line-height: 1.2` and explicit struts, so the
faces’ own ascents never decide a line.

## Key Insights

- **The disharmony is x-height and weight, not baseline.** Both faces sit on the same
  baseline; PT Serif’s lowercase reaches 13% higher and its strokes are heavier.
  A size token can split the x-height difference against the cap and digit differences,
  and 1.05em already does, but no size makes Computer Modern’s hairlines match.
- **The KaTeX class map decides what is cheap.** Variables, `\mathit`, `\mathbf` and
  `\textrm` are one CSS rule each.
  Digits, operator names and `\text{}` are not addressable by class, so they need a
  composite family; that is one `@font-face` pair per weight and no JavaScript.
- **Taking letters and digits is safe; taking operators is not.** PT Serif’s math axis
  is 0.094em above KaTeX’s and it has no `≤`. Letters and digits from the text face and
  everything else from the math fonts is exactly the line the metrics draw, and it is
  narrower than what `mathastext` takes by default and wider than what the cautious
  tex.stackexchange advice takes.
- **CSS-only routes keep Computer Modern’s layout numbers.** The visible cost is a pixel
  of numerator overflow.
  KaTeX exports the hook to replace them, and the patch is 228 numbers computed from the
  same files KPress already ships.
- **The web has not solved this and KPress does not need it to.** MathJax cannot
  redirect digits; KaTeX’s maintainers call any font change a major project; MathML Core
  can do it properly but needs a 380 KB `MATH` font and browsers that shipped this year.
  A renderer that owns its stylesheets and vendors its bundle can do in CSS and forty
  lines of Python what the LaTeX packages do.

## Comparison Matrix

| Criterion | A, current | E, CSS routing at 1em | G, routing plus metrics | MathJax 4 | Temml / MathML Core |
| --- | --- | --- | --- | --- | --- |
| Letters and digits match the prose | no | yes | yes | `\text{}` only | yes, metric-correct |
| Symbols keep a designed math axis | yes | yes | yes | yes | yes |
| Layout numbers match the drawn glyphs | yes | no, ~0.05em on tall glyphs | yes | yes | yes |
| Bytes (hosted) | baseline | none | a metrics table, tens of KB | a full math font family | +380 KB Latin Modern Math |
| Code touched | none | KPress CSS | plus a generated table and an init hook | new pipeline | new pipeline, new TeX dialect |
| Print (headless Chromium) | fine | fine, same engine | fine | to verify | Chromium MathML bugs listed by Temml |
| Browser floor | any | any | any | any | Chrome 109, Firefox 149, Safari 26.2 for `math` |
| Risk | none | low; Safari and Firefox to verify | low; a KaTeX bump re-runs the generator | high | high |

## Recommendations

Route E with route G’s metrics, as a KPress feature that is on by default: a composite
family for the reading face’s letters and digits, the class rules pointed at it, inline
math at 1em, and complete metric tables for the swapped code points applied through
`katex.__setFontMetrics` before rendering.
Operators, relations, delimiters, big operators and Greek stay in the KaTeX faces.
The design and its phases are in [Math Text Face](math-text-face.plan.md).

## Methodology

Local measurement first, then prior art.
The fonts were read with fontTools 4 (`fonttools[woff]` for the woff2 decoding) directly
from the files KPress ships and from the macOS system copies of Times New Roman,
Georgia, STIX Two Math and STIX Two Text.
Glyph bounds are from a bounds pen over the outlines; stem widths are horizontal ink
spans of a flattened outline at half x-height; the operator centre is the midpoint of
the minus sign’s ink.
The variants were built by extracting a rendered page’s own inlined data URIs and
injecting extra `@font-face` and class rules before `</head>`; route G additionally
rewrote the metric table in the inlined `katex.min.js`. Screenshots came from Playwright
driving Google Chrome at device scale 3, element screenshots of the same paragraphs and
display blocks in each variant, then stacked into per-paragraph montages.
Only Chromium was inspected; Safari and Firefox are named in the plan.

The prior-art surveys were delegated to three research sub-agents working from primary
sources (CTAN documentation and TUGboat papers; the KaTeX, MathJax and Temml
repositories and docs and the MathML Core specification; the CSS Fonts 4 and 5
specifications, MDN and browser release notes), each asked to mark every claim as
verified from source or recalled.
Only verified claims are stated as fact above; the one folklore item (the origin of
KaTeX’s 1.21em) is labelled as such.
Not found by any survey: a published pairing for PT Serif, any site composing a text
face with a math face by `unicode-range`, and any rebuild of the KaTeX fonts from a
non-Computer-Modern source.

## References

KPress:

- Commit `ef3074c`, “size KaTeX to PT Serif rather than to KaTeX’s Times default”, and
  `components.css` “KaTeX sizing”.
- KaTeX 0.16.45 as vendored: the class rules in `katex.min.css` and the metric table and
  `__setFontMetrics` export in `katex.min.js`.
- PT Serif (ParaType, 2010), the Latin subset shipped as
  `pt-serif-latin-{400,700}-{normal,italic}.woff2`.

LaTeX (official documentation unless noted):

- [mathastext manual v1.4e](https://mirrors.ctan.org/macros/latex/contrib/mathastext/mathastext.pdf)
  and [README](https://mirrors.ctan.org/macros/latex/contrib/mathastext/README.md).
- [unicode-math manual](https://texdoc.org/serve/unicode-math/0) and
  [fontspec manual](https://texdoc.org/serve/fontspec/0) (`Scale=MatchLowercase`).
- [mathspec v0.2b](https://mirrors.ctan.org/macros/xetex/latex/mathspec/mathspec.pdf).
- [newtx documentation](https://mirrors.ctan.org/fonts/newtx/doc/newtxdoc.pdf);
  [cochineal](https://mirrors.ctan.org/fonts/cochineal/doc/cochineal-doc.pdf),
  [scholax](https://mirrors.ctan.org/fonts/scholax/doc/scholax-doc.pdf) and
  [newtxsf](https://mirrors.ctan.org/fonts/newtxsf/doc/newtxsf-doc.pdf) on x-height
  matching.
- [paratype](https://ctan.org/pkg/paratype) and the
  [LaTeX Font Catalogue entry](https://tug.org/FontCatalogue/paratypeserif/).
- [TeX FAQ: choice of Type 1 fonts for maths](https://texfaq.org/FAQ-psfchoice).
- Hartke,
  [A survey of free math fonts for TeX and LaTeX](https://www.tug.org/pracjourn/2006-1/hartke/)
  (2006).
- Vieth,
  [Math typesetting in TeX: the good, the bad, the ugly](https://tug.org/~vieth/papers/eurotex2001/math-good-bad-ugly.pdf)
  (2001);
  [Understanding the æsthetics of math typesetting](https://www.tug.org/~vieth/papers/bachotex2008/math-font-paper.pdf)
  (2008); [OpenType math illuminated](https://www.tug.org/tugboat/tb30-1/tb94vieth.pdf)
  (2009);
  [An updated survey of OpenType math fonts](https://tug.org/TUGboat/tb44-2/tb137vieth-otmath.html)
  (2023).
- Jackowski,
  [Appendix G illuminated](https://www.tug.org/TUGboat/tb27-1/tb86jackowski.pdf) (2006);
  Jackowski, Strzelczyk, Pianowski,
  [GUST e-foundry font projects](https://www.tug.org/TUGboat/tb37-3/tb117jackowski.pdf)
  (2016).
- [OpenType MATH table specification](https://learn.microsoft.com/en-us/typography/opentype/spec/math).
- Community discussion: tex.stackexchange
  [757669](https://tex.stackexchange.com/questions/757669) (text-italic letters into a
  math font, with the x-height scaling),
  [145522](https://tex.stackexchange.com/questions/145522),
  [364279](https://tex.stackexchange.com/questions/364279),
  [422854](https://tex.stackexchange.com/questions/422854); Weber,
  [Using the same font for numbers in math mode](https://bryanwweber.com/writing/2014-03-25-using-the-same-font-for-numbers-in-math-mode-in-latex.html)
  (2014).

Web renderers (repositories and official docs unless noted):

- KaTeX: [katex.scss](https://github.com/KaTeX/KaTeX/blob/main/src/styles/katex.scss),
  [fontMetrics.ts](https://github.com/KaTeX/KaTeX/blob/main/src/fontMetrics.ts),
  [metrics README](https://github.com/KaTeX/KaTeX/blob/main/src/metrics/README.md),
  [Font docs](https://katex.org/docs/font); issues
  [#123](https://github.com/KaTeX/KaTeX/issues/123),
  [#329](https://github.com/KaTeX/KaTeX/issues/329),
  [#1702](https://github.com/KaTeX/KaTeX/issues/1702),
  [#4119](https://github.com/KaTeX/KaTeX/issues/4119), PR
  [#4129](https://github.com/KaTeX/KaTeX/pull/4129), discussions
  [#3409](https://github.com/KaTeX/KaTeX/discussions/3409),
  [#3716](https://github.com/KaTeX/KaTeX/discussions/3716),
  [#4105](https://github.com/KaTeX/KaTeX/discussions/4105);
  [katex-fonts](https://github.com/KaTeX/katex-fonts).
- Community: Li,
  [KaTeX custom fonts](https://yingtongli.me/blog/2022/09/24/katex-custom-fonts.html)
  (2022);
  [Using KaTeX on GitHub Pages](https://blog.claude.nl/posts/using-katex-on-github-pages/)
  (2021); Serlo [#549](https://github.com/serlo/frontend/issues/549); Observable stdlib
  [#47](https://github.com/observablehq/stdlib/issues/47);
  [Distill d-math.css](https://github.com/distillpub/template/blob/master/src/styles/d-math.css).
- MathJax:
  [output options](https://docs.mathjax.org/en/latest/options/output/index.html),
  [fonts](https://docs.mathjax.org/en/latest/output/fonts.html),
  [what’s new in 4.0: fonts](https://docs.mathjax.org/en/v4.0/upgrading/whats-new-4.0/fonts.html);
  Krautzberger,
  [MathJax font matching and pairing](https://www.peterkrautzberger.org/0183/).
- Temml:
  [administration](https://github.com/ronkok/Temml/blob/main/docs/administration.md) and
  [README](https://github.com/ronkok/Temml).
- MathML Core:
  [user-agent stylesheet](https://w3c.github.io/mathml-core/#user-agent-stylesheet);
  [Chromium mathml.css](https://github.com/chromium/chromium/blob/main/third_party/blink/renderer/core/css/mathml.css);
  [Firefox mathml.css](https://github.com/mozilla-firefox/firefox/blob/main/layout/mathml/mathml.css);
  [WebKit mathml.css](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/css/mathml.css);
  Firefox [bug 947654](https://bugzilla.mozilla.org/show_bug.cgi?id=947654);
  [MathML in Chromium](https://mathml.igalia.com/).
- [ar5iv CSS](https://github.com/dginev/ar5iv-css/blob/master/css/ar5iv-fonts.css);
  [MediaWiki Math extension CSS](https://github.com/wikimedia/mediawiki-extensions-Math/blob/master/modules/ext.math.css).

CSS and fonts (specifications and browser documentation):

- [CSS Fonts 4](https://www.w3.org/TR/css-fonts-4/): `unicode-range`, composite fonts,
  the font matching algorithm, first available font.
- [CSS Fonts 5](https://www.w3.org/TR/css-fonts-5/): `size-adjust`, the metric override
  descriptors, `font-size-adjust`.
- [CSS Inline 3](https://drafts.csswg.org/css-inline-3/): ascent and descent, line box
  height, baseline alignment.
- [OpenType OS/2 table](https://learn.microsoft.com/en-us/typography/opentype/spec/os2)
  (`USE_TYPO_METRICS`).
- MDN:
  [unicode-range](https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/unicode-range),
  [size-adjust](https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/size-adjust),
  [ascent-override](https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/ascent-override),
  [font-size-adjust](https://developer.mozilla.org/en-US/docs/Web/CSS/font-size-adjust).
- Browser support: [Chrome 87](https://developer.chrome.com/blog/new-in-chrome-87/),
  [Chrome 127](https://developer.chrome.com/release-notes/127),
  [web.dev on size-adjust](https://web.dev/articles/css-size-adjust),
  [Chrome on font fallbacks](https://developer.chrome.com/blog/font-fallbacks); WebKit
  [Safari 16.4](https://webkit.org/blog/13966/webkit-features-in-safari-16-4/),
  [Safari 17.0](https://webkit.org/blog/14445/webkit-features-in-safari-17-0/),
  [bug 219735](https://bugs.webkit.org/show_bug.cgi?id=219735) (metric overrides);
  Firefox release notes
  [89](https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/89),
  [92](https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/92),
  [118](https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/118).
- Tools: [Capsize](https://github.com/seek-oss/capsize) (metric matching from font
  files);
  [fontTools woff2](https://fonttools.readthedocs.io/en/latest/ttLib/woff2.html);
  [PT Serif metadata on Google Fonts](https://github.com/google/fonts/blob/main/ofl/ptserif/METADATA.pb).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
