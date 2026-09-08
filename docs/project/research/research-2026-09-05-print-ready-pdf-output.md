---
title: Publication-Quality PDF Output for KPress
description: Research and recommendations for deterministic, typographically excellent, print-ready PDF output from KPress HTML
author: Joshua Levy (github.com/jlevy) with LLM assistance
---
# Research: Publication-Quality PDF Output for KPress

**Date:** 2026-09-05; implementation review updated 2026-09-08

**Author:** Joshua Levy (github.com/jlevy) with LLM assistance

**Status:** Research complete.
Chromium implementation evidence updated; alternative backends and named PDF profiles
remain proposals.

## Overview

KPress already owns the inputs that make a good print pipeline possible: semantic HTML,
the complete CSS cascade, local fonts, mathematical markup, figures, and the rendering
boundary. Its current optional PDF backend asks Playwright Chromium to print that HTML.
That is a useful baseline, but it is not yet a complete contract for deterministic or
publication-quality output.

This brief asks which modern typesetting and HTML-to-PDF approaches can give KPress
clean, controlled, reliable PDF output without losing the principal advantage of KPress:
the same document can live inside an arbitrary web application.
The
[Squares explainer](https://github.com/jlevy/squares/blob/main/packing/devtools/templates/explainer-article.md)
is the motivating stress test.
It combines prose, dense mathematics, custom typography, inline SVG, large bitmap
canvases, interactive controls, and application-specific layout in one self-contained
KPress page.

The implemented path is Chromium.
The Squares acceptance work now demonstrates correct font embedding, repeatable export,
and stable mathematical layout in that path.
A static **print artifact contract** remains the proposed boundary for other engines; it
must not impose publication-time browser preparation on ordinary KPress HTML. The
proposed PDF profiles are:

1. **Chromium reader PDF** as the broadly compatible, web-faithful baseline.
2. **Prince publication PDF** as the first commercial candidate to evaluate for
   sophisticated paged typography and standards-based press output.
3. **WeasyPrint as the leading open-source publication-backend candidate**, gated on a
   real KPress/Squares bakeoff rather than assumed compatible from feature lists.

Typst is the strongest modern greenfield alternative to TeX for print-first documents,
but it is not a renderer for KPress output.
Adopting it for KPress would create a second document model, template system, math path,
and graphics path. That may be reasonable for a separate print-first product, but it is
the wrong default for arbitrary KPress-backed web applications.

## Questions to Answer

1. What does “print-ready” mean for KPress, and which guarantees can be made honestly?
2. How far can current browser printing go when KPress controls the HTML, CSS, assets,
   and browser invocation?
3. What do dedicated CSS paged-media engines such as Prince, Antenna House, PDFreactor,
   and WeasyPrint add?
4. What do modern TeX successors and reimplementations such as Typst, SILE, Tectonic,
   and ConTeXt do better, and can those advantages be used without duplicating KPress?
5. How should math, SVG, canvas, interactive components, fonts, headers, footers,
   margins, color, accessibility, and commercial-press requirements be handled?
6. What architecture and validation process would make PDF a reliable KPress feature
   instead of a best-effort screenshot of a web page?

## Scope

This research covers:

- PDF generated from a KPress standalone page or a host-provided KPress print artifact;
- Chromium and browser-side paged-media layers;
- dedicated HTML/CSS formatters;
- modern document typesetters and TeX successors as architectural alternatives;
- mathematical typography, vector graphics, pagination, accessibility, color, and
  reproducibility;
- local and CI/server production rather than only an interactive browser print dialog.

It does not select a commercial license, promise identical pagination across different
engines, or claim a press profile without a printer’s delivery specification.
No cross-engine rendering bakeoff was performed for this brief.
Feature comparisons are based primarily on official specifications and engine
documentation, then checked against the current KPress and Squares implementations.
The recommended bakeoff is therefore a decision gate, not optional polish.
The engine survey below preserves the September 5 assessment; the implementation
evidence and decisions below incorporate the subsequent font and PDF work.

## Implementation Evidence and Decisions

The shared
[font and math loading architecture](../architecture/arch-2026-09-08-font-and-math-loading.md)
and [host math API](../../math-rendering-api.md) define the current contract.
The following findings change the implementation priorities without establishing an
unmeasured advantage for a different PDF engine.

### Font composition, readiness, and preparation are separate

KPress supplies CSS composite families over the shipped PT Serif, Source Sans, and KaTeX
files, together with generated matching KaTeX metric tables.
Latin letters and digits follow the prose or sans context; mathematical symbols and
explicit alphabets retain their appropriate KaTeX faces.
These are separate font assets, not physically merged font binaries.
An additional formula does not require rebuilding the font assets or adding a new
browser build dependency to KPress HTML generation.

Embedding bytes removes network retrieval, but font decoding and client layout still
take time. The shared `render()` and `hydrate()` methods hide each formula until native
load promises for its actual glyphs and individual font families settle successfully.
They also handle superseded input and required-font failure.
Neither a successful `FontFaceSet.check()` nor a page-wide preload of every declared
face is the rendering contract.
Broad warmup remains explicit; an unused face must not delay an otherwise ready formula.
These distinctions are covered by KPress’s
[real-browser loading controls](../../../tests/test_playwright_math_loading.py).

For a host requiring stable space before decoding, Squares implements an optional
publication pass: measure each unbreakable KaTeX base, reserve its dimensions, and
hydrate the matching prepared markup.
Saved custom/system and serif/sans preferences select matching geometry before paint.
Ordinary client rendering remains available for new formulas and changed input.
A prepared host keeps selectable KaTeX HTML as its no-JavaScript fallback; ordinary
KPress keeps semantic MathML.

Reservation correctness includes the actual baseline, not only width and height.
The final Squares correction preserves the ordinary measurement and gives the base’s
existing strut the same measured height and negative depth as its reservation, with zero
leading on the prepared carriers and base.
That prevents a font-dependent line box from shifting the glyphs within an otherwise
correct reservation.
This measured host requirement extends the architecture’s print-equivalence rule to
short punctuation, zero-height native struts, and independent adjacent-text baseline
checks.

### Typography and PDF evidence is source-qualified

Squares sets both inline and display math to the surrounding text size, including sans
captions and every supported saved font profile.
This is a host typography policy; it does not change KaTeX’s internal script and
operator ratios or assert that equal CSS sizes give every glyph equal optical height.
Its macOS screen policy uses native hinted rendering after checking linear advances;
print and other platforms retain the geometric-precision policy needed for stable
advances. The observed lighter PT Serif rendering was addressed at that rendering-policy
boundary, without substituting an older font or applying synthetic bold.
The exact policy and its guards live in the
[Squares shell](https://github.com/jlevy/squares/blob/a10569d1/packing/devtools/templates/explainer-shell.html)
and
[typography inspector](https://github.com/jlevy/squares/blob/a10569d1/packing/devtools/inspect_explainer_typography.py).

For print, KPress supplies static Source Sans instances so Chromium can embed font
programs at the required weights.
The original stem-width and viewer-smoothing measurements remain in the
[print sans research](research-2026-09-07-print-sans-faces.md); they are a separate
result from the screen hinting issue.
The PDF backend now waits for print faces and explicitly requests margin-box fonts after
switching media, with
[real PDF tests](../../../tests/test_playwright_print_pdf_fonts.py) for owned embedded
faces. This is narrower than a general host completion protocol.

The retained
[Squares Pages run 34288782889](https://github.com/jlevy/squares/actions/runs/34288782889)
tested a tree identical to source `a10569d1` on Linux.
Its PDF had 17 pages and 20 embedded fonts, with no page font drawn as outline paths;
two exports agreed after the project’s PDF metadata normalization.
All 13 inline caption formulas had a measured 0 CSS-pixel baseline offset in screen and
print, at both checked viewport/theme settings.
The
[original prepared-caption regression](https://github.com/jlevy/squares/blob/a10569d1/packing/tests/test_font_provenance.py)
was a −0.21875 CSS-pixel print offset; the retained original-strut and raised-glyph
controls reject that failure mode.
Nine edge formulas include punctuation, fractions, radicals, limits, `\quad`, and
`\smash{x}`. These results certify that source and environment, not arbitrary PDFs or
future renderer revisions.
They do not establish PDF/UA or PDF/X conformance.

Latency is measured separately from artificially delayed-font correctness.
The
[retained startup campaign](https://github.com/jlevy/squares/tree/dfa0a422/packing/benchmarks/math-startup)
accepted 12 paired runs per width for source `dab2a381`: desktop parameter readiness
medians changed from 465.9 to 401.55 ms, and mobile from 469.8 to 320.85 ms.
The accepted records and complete receipts were committed later, at `dfa0a422`. Those
observations support the combined host revision, which includes narrower waits and
prioritized, bounded submission of math work; they do not isolate any one edit’s effect.
They are not timings for the later caption correction or a claim that all remaining
startup time is unavoidable font decoding.

### What remains a proposal

The current KPress backend has not become a general static-artifact publisher, a
host-task registry, or a strict PDF preflight system.
Its font wait has a bounded recovery timeout; a returned PDF is not proof that every
host task or asset succeeded.
The Squares exporter supplies additional application-specific settlement, typography,
font-provenance, layout, and reproduction checks.
Generalizing those boundaries is useful future work, but should reuse the shared math
runtime rather than create a second font gate.

Prince, WeasyPrint, cross-engine print stylesheets, and standards-based output profiles
remain unevaluated on this corpus.
Nothing in the font corrections requires another typesetter, merged font binaries, or a
per-formula asset build.

## Define the Output Before Selecting the Renderer

“Print-ready PDF” is ambiguous.
KPress should name three different products because their acceptance criteria differ:

| Profile | Intended use | Required properties |
| --- | --- | --- |
| **Reader** | Download, review, office printing, archival attachment | Correct page size and margins; no browser-added URL/date; embedded fonts; live links; selectable text; stable math and figures; useful outline and tags |
| **Publication** | Reports, white papers, manuals, books, client delivery | Reader requirements plus controlled running matter, strong page breaking, footnotes and cross-references, named pages, deliberate recto/verso behavior, and editorial page QA |
| **Press** | Commercial print production | A printer-agreed PDF/X profile, trim and bleed boxes, marks when requested, embedded fonts, output intent and color policy, image-resolution checks, and formal preflight |

A PDF that looks attractive in Preview is not necessarily accessible, archival, or
acceptable to a commercial printer.
Conversely, most KPress documents do not need CMYK conversion, crop marks, or PDF/X.
Making those constraints the default would remove live links, transparency, or other
useful reader-PDF behavior without benefiting ordinary users.

The renderer is only one part of each profile.
High-quality output also depends on source closure, font and asset control, print CSS,
component fallbacks, engine pinning, readiness, metadata, and validation.

## Findings

### The Current KPress Baseline Is Useful but Underspecified

The current [`kpress.format.pdf`](../../../src/kpress/format/pdf.py) backend:

1. writes or opens the rendered HTML;
2. launches Playwright’s bundled Chromium;
3. navigates to a `file:` URL and waits for `networkidle`;
4. switches to print media;
5. forces print layout, waits for its fonts, and requests margin-box families; and
6. calls `page.pdf()` with a named paper format and background printing enabled.

The existing [`print.css`](../../../src/kpress/format/static/css/print.css) already does
substantial work: it establishes page-margin content, forces a light paper palette,
re-roots the type scale at 11pt, removes interactive chrome, releases the KPress scroll
container, repeats table headers, wraps code, avoids breaks in several figures and
blocks, simplifies footnotes, and applies widows, orphans, justification, and
hyphenation. The default footer is a public CSS token in
[`style-tokens.css`](../../../src/kpress/format/static/css/style-tokens.css), so
“Formatted by KPress” is KPress-owned generated content rather than Chromium’s automatic
URL/date footer.

The gaps are important:

- `networkidle` and the print-font wait do not settle future or queued host work,
  diagrams, custom elements, or canvas redraws.
  The 15-second font-wait ceiling and caught margin-font errors permit recovery rather
  than certify successful preflight.
- The backend does not seal or reject network requests and does not report missing or
  substituted assets.
- The CSS does not declare `@page size`, while Playwright’s `preferCSSPageSize` defaults
  to false; the API paper format therefore owns sizing and may scale CSS content.
- `displayHeaderFooter`, scale, tagged PDF, and outline behavior are left implicit or at
  their defaults instead of forming a tested KPress profile.
- The [PDF contract tests](../../../tests/test_pdf_contract.py) mock browser calls,
  while [real PDF tests](../../../tests/test_playwright_print_pdf_fonts.py) now check
  font embedding, slow print faces, margin text, and owned glyph provenance.
  They do not yet form a general acceptance suite for tags, links, page boxes, complete
  visual pages, and repeatability across arbitrary hosts.
- The public design identifies a browser-backed PDF path, but does not specify separate
  input, layout, and byte-repeatability guarantees for a tested export profile.

Playwright documents that `page.pdf()` uses print CSS, that `printBackground` defaults
to false, that `preferCSSPageSize` defaults to false and otherwise scales content to the
API paper size, and that both `tagged` and `outline` default to false.
These are not bugs in Playwright; they are choices KPress needs to make explicitly in
its own contract.

### Squares Is the Right Acceptance Fixture

Squares is representative because it has both a deterministic document build and content
that is difficult to freeze for print.
Its renderer inlines KPress CSS, KPress fonts, KaTeX, and application code into one HTML
file, and its Pages workflow renders twice to catch byte drift.
The document includes:

- mathematical prose and display equations rendered with KaTeX plus MathML fallback;
- inline SVG that can remain vector in PDF;
- three large canvases whose state and colors are produced by JavaScript;
- controls and selectable certificate views that have no direct printed equivalent;
- a dense one-hundred-cell atlas where raster downscaling quickly makes labels
  illegible; and
- a custom reading shell that must preserve both browser navigation and print flow.

The original Squares fixture exposed two host responsibilities a generic renderer cannot
infer:

1. KPress released `.kpress-viewport` for pagination, but the consuming page kept
   `html, body` at fixed height with hidden overflow.
   Without a host override, Chromium printed one page and omitted most of the report.
   Squares now uses document scrolling and verifies full pagination; the historical
   failure remains a useful host-shell regression.
2. Canvas is a bitmap. Print CSS cannot recolor or vectorize it, so Squares listens for
   print media and `beforeprint` to redraw in the light palette.
   Its exporter now settles host math and redraw work after changing media, but the
   figures are still raster graphics.
   A future publication profile needs an explicit vector alternative where the source
   geometry permits one.

The same stylesheet records a third, subtler problem: unbreakable figures that are too
tall create large regions of premature whitespace.
This is not solved by adding more `break-inside: avoid`; it requires sizing rules,
alternative figure compositions, or a better paginator.

Squares also demonstrates the preferred solution for graphics that have a geometric
source of truth. Its known-best atlas is generated as SVG and converted to vector PDF
with CairoSVG; the project notes that the selected conversion emits no timestamps and
can be checked byte-for-byte.
KPress should generalize that pattern: interactive canvas may remain the screen
representation, but a print-quality component should expose SVG, PDF, or another
explicit static representation whenever its underlying data is vector.

### CSS Paged Media Is the Shared Language, Not a Shared Implementation

The W3C [CSS Paged Media Level 3](https://www.w3.org/TR/css-page-3/) draft defines page
size and orientation, margins, page selectors, sixteen margin boxes, page counters,
running matter, named pages, bleed, and marks.
[Generated Content for Paged Media](https://www.w3.org/TR/css-gcpm-3/) adds mechanisms
such as named strings, running elements, footnotes, and page-aware cross-references.

These drafts give KPress a sensible authoring model, but conformance is not uniform.
A rule that parses in several engines may paginate differently, and a browser can
support `@page` margins while omitting footnotes or target page counters.
KPress therefore needs:

- a conservative portable print layer;
- backend-specific capability layers; and
- fixtures that test observed output, not just whether CSS parsed.

### Chromium Is the Best Web-Fidelity Baseline

Chromium has one decisive advantage: it renders the actual KPress application stack.
Modern CSS, KaTeX, custom JavaScript, canvas, SVG, web fonts, and host layout run in the
same engine used for screen acceptance.
That makes it the lowest-friction backend for arbitrary applications and the most
faithful option for Squares today.

Browser paged-media support has improved.
Chrome added generated content in `@page` margin boxes in Chrome 131, including page
counters. Its own
[print-margin documentation](https://developer.chrome.com/blog/print-margins) also
identifies the remaining boundary: named strings for changing running heads,
`target-counter()` page references, and CSS footnotes are not implemented.
Chromium pagination still needs author-supplied break and sizing rules, and its ordinary
line breaking does not become a book typesetter simply because the result is a PDF.

There are two distinct Chromium workflows:

- **Interactive `window.print()`.** Useful as a convenience action, but the user
  controls paper, scale, margins, and whether the browser adds its own URL/date headers
  and footers. A page cannot guarantee the result.
- **Programmatic `page.pdf()`.** Suitable for a supported KPress artifact because KPress
  can pin the engine and explicitly set paper, scale, backgrounds, header/footer
  behavior, tags, and outline.
  Playwright’s
  [`page.pdf()` contract](https://playwright.dev/docs/api/class-page#page-pdf) exposes
  those controls.

Programmatic Chromium should therefore remain supported, but it should be described as
the reader/web-fidelity profile rather than the ceiling of KPress typography or press
production.

### Browser Paged-Media Layers Add Features and Moving Parts

[Paged.js](https://pagedjs.org/en/about/) is an open-source JavaScript polyfill for the
W3C paged-media modules.
It paginates and rewrites the DOM in a browser, provides lifecycle hooks, and can be
driven with a headless-browser CLI. It is valuable for browser preview, experimentation,
and publications committed to its DOM model.
For KPress it adds another transformation and readiness layer on top of Chromium, which
makes failures harder to attribute and does not remove Chromium’s environment pinning.

[Vivliostyle CLI](https://docs.vivliostyle.org/en/cli/getting-started/) is a more
complete open-source publication workflow around a browser-based paged-media engine.
It supports HTML and Markdown inputs, browser preview, themes, and PDF generation.
Its
[press-ready mode](https://docs.vivliostyle.org/en/cli/special-output-settings/#generating-print-ready-pdf-pdfx-1a-format)
uses Docker and post-processing to produce PDF/X-1a. That is a useful precedent for
environment capture and explicit preflight, but it is a larger toolchain and PDF/X-1a is
not a universal press target.

Both deserve a bakeoff lane.
Neither should be inserted into KPress’s default pipeline before it demonstrates a
material result that hardened Chromium or a dedicated formatter cannot provide more
directly.

### Dedicated CSS Formatters Best Preserve KPress’s Single Source of Truth

Dedicated formatters consume HTML and print CSS but implement pagination as their main
job rather than as a secondary browser feature.
They are the most promising route to publication quality because they preserve KPress’s
semantic HTML and most of its styling model.

#### Prince

Prince is a dedicated formatter; the September 5 survey identified Prince 16.2, released
in January 2026. Its [paged-media documentation](https://www.princexml.com/doc/paged/)
covers named and selected pages, running matter, footnotes, sidenotes, page floats, page
groups, recto/verso layouts, counters, and detailed break control.
Its [PDF output documentation](https://www.princexml.com/doc/prince-output/) covers
tagged PDF, bookmarks, PDF/A, PDF/UA, and PDF/X profiles, including production
requirements such as embedded fonts and output intents.

That feature set makes Prince the best first commercial backend to prototype.
It is mature, scriptable, available as a CLI and container, and close to KPress’s
existing HTML/CSS boundary.

The caveat is crucial for Squares and arbitrary web applications.
[Prince scripting](https://www.princexml.com/doc/javascript/) is disabled by default and
implements most of ECMAScript 5 with incomplete ES6 support, not a current browser
runtime.
KPress cannot hand an arbitrary interactive page to Prince and assume its KaTeX,
modules, custom elements, or application canvas code will run.
Prince should consume a static, already-materialized print artifact.

Prince is commercial software.
If the prototype passes, it should remain an optional adapter and documented production
path rather than a mandatory runtime dependency or silent replacement for Chromium.

#### WeasyPrint

WeasyPrint is the strongest open-source candidate for a Python-native publication
backend. Its current
[feature reference](https://doc.courtbouillon.org/weasyprint/stable/api_reference.html#css-paged-media-module-level-3)
documents page selectors, margin boxes, size, bleed, marks, named pages, running
elements, footnotes, fragmentation control, custom properties, modern color, and
hyphenation. It preserves SVG as vector output, embeds and subsets fonts, and exposes
PDF/A, PDF/UA, and PDF/X variants.

It is not a browser and does not execute application JavaScript.
It uses Pango and system libraries for shaping and layout; its own documentation notes
limits in grid, flex, columns, and other browser-oriented CSS. It also warns that
requested PDF/A or PDF/UA output is not guaranteed valid and must be checked.
That combination makes WeasyPrint appealing but not drop-in compatible with arbitrary
KPress screen CSS.

The right question is empirical: can a deliberately conservative KPress print artifact
and print stylesheet render the KPress fixture set and Squares correctly in a frozen
WeasyPrint environment?
If yes, it should become the open-source publication profile.
If not, KPress should document it as an external integration rather than expanding its
public support surface.

#### Antenna House Formatter

[Antenna House Formatter](https://www.antenna.co.jp/AHF/help/en/ahf-about.html) is an
enterprise formatter for HTML/CSS and XSL-FO. It offers broad multilingual hyphenation,
native vector SVG and MathML, tagged PDF, PDF/UA, PDF/A, and PDF/X. It is a credible
alternative where multilingual, XSL-FO, or enterprise support needs dominate.

Its own
[technical notes](https://www.antenna.co.jp/AHF/help/en/ahf-tech.html#formatting-html)
make the integration cost explicit: browser-designed HTML rarely produces the best
result without a print-specific stylesheet, and browser CSS behavior differs.
That is exactly why KPress needs a static print contract and conservative print CSS.

#### PDFreactor

[PDFreactor](https://www.pdfreactor.com/product/doc_html/manual-lib.html) is another
commercial dedicated formatter with paged CSS, JavaScript support, vector SVG, color
management, PDF/A, PDF/UA, PDF/X, and optional conformance validation.
Its compatibility table includes current KaTeX, which makes it especially interesting
for mathematical KPress documents.
Its SVG handling can preserve text and CMYK or spot colors as vector content, while
documented effects may trigger controlled rasterization.

PDFreactor belongs in the commercial bakeoff with Prince and Antenna House.
Prince is the recommended first prototype because it has the clearest fit with KPress’s
current CLI-style optional backend and paged-media goals, not because the other two are
categorically incapable.

### Modern Typesetters Solve a Different Problem Well

Modern successors and reimplementations improve the authoring and build experience of
TeX-class documents.
Their best features should inform KPress’s quality bar, but they do not consume a live
KPress DOM.

#### Typst

Typst is the most compelling modern, print-first alternative in this comparison.
It provides a coherent markup and programming model, native mathematical typesetting,
OpenType math fonts, vector graphics, and whole-paragraph optimized line breaking for
justified text. Its [PDF exporter](https://typst.app/docs/reference/pdf/) tags output by
default and supports a range of PDF versions plus PDF/A and PDF/UA-1. Its document
metadata API explicitly supports byte reproducibility by requiring the creation date to
be fixed or omitted rather than left at its default current time.

Those are excellent design precedents for KPress: optimize paragraphs deliberately, make
accessibility structural, expose standards as profiles, and control metadata.

Typst is not an output backend for KPress.
The [Typst HTML exporter](https://typst.app/docs/reference/html/) is itself experimental
and explains why print layout and semantic HTML cannot be perfectly interchangeable.
Going from KPress HTML back into Typst would require a lossy translator or a parallel
Typst template. Raw HTML, modern CSS, JavaScript components, canvas behavior, and
host-specific layout would not survive automatically.

Typst should be recommended for greenfield, print-first documents whose authors accept
Typst as the source language.
It should not become a hidden second implementation of every KPress component.

#### Tectonic, ConTeXt, and LuaLaTeX

[Tectonic](https://tectonic-typesetting.github.io/en-US/) modernizes TeX operation
rather than replacing the TeX document model.
It packages a self-contained XeTeX/TeX Live engine, Unicode and OpenType support,
automatic multipass processing, and reproducible support bundles.
LuaLaTeX plus mature LaTeX packages remains a high bar for mathematical typography,
bibliographies, microtypography, and long-form publishing.
[ConTeXt LMTX](https://wiki.contextgarden.net/LMTX) offers another deeply programmable,
integrated TeX lineage.

All are strong when TeX or ConTeXt is the authored source.
For KPress they require Markdown/HTML-to-TeX conversion, a second template and style
system, and explicit translations for every custom component.
Pandoc can orchestrate that route, but the conversion boundary remains.

#### SILE and the Long Tail

[SILE](https://sile-typesetter.org/) is a programmable modern typesetter with
sophisticated line breaking, shaping, hyphenation, bibliographies, and indexing.
[SATySFi](https://github.com/gfngfn/SATySFi) and
[Patoline](https://github.com/patoline/patoline) explore typed or functional document
programming. These systems are valuable evidence that excellent typography no longer
implies a classic LaTeX installation.
They have smaller ecosystems and the same fundamental KPress mismatch: none is a
browser-compatible HTML/CSS/JavaScript renderer.

### Pandoc and Quarto Are Orchestrators, Not Rendering Engines

Pandoc’s [PDF engine list](https://pandoc.org/MANUAL.html#option--pdf-engine) is a
useful precedent: one document pipeline can expose TeX, ConTeXt, Typst, WeasyPrint,
Prince, and Paged.js as explicit engines.
[Quarto](https://quarto.org/docs/output-formats/pdf-basics.html) similarly routes
different formats to explicit backends.

KPress should borrow the explicit-backend idea, not add Pandoc as an intermediate step
after it has already produced the richer HTML DOM. Converting KPress HTML through a
generic document AST would discard the very component and host integration information
the PDF path must preserve.

## Comparison Matrix

The ratings below describe fit for **KPress output**, not the intrinsic quality of each
project.
“Strong” means the capability is native and plausible for the target role; it is
not a substitute for the proposed bakeoff.

| Engine | Reuses KPress HTML/CSS | Runs arbitrary web JS | Advanced paged media | PDF standards and press | Operational shape | Best KPress role |
| --- | --- | --- | --- | --- | --- | --- |
| Chromium/Playwright | Strongest screen fidelity | Strong | Basic to moderate | Tagged PDF available; not a complete press workflow | Open source; browser binary must be pinned | Default reader PDF |
| Prince | Strong with print-specific CSS | Limited, non-browser JS | Strong | Strong PDF/A, PDF/UA, PDF/X, color controls | Commercial CLI/container | First commercial publication/press prototype |
| WeasyPrint | Moderate; requires conservative print CSS | None | Strong declared coverage | PDF/A, PDF/UA, PDF/X options; external validation required | Open source Python plus native libraries | Open-source publication candidate |
| Antenna House | Moderate to strong with print CSS | Not a browser-app runtime | Strong | Strong enterprise and multilingual production features | Commercial | Enterprise adapter candidate |
| PDFreactor | Strong with compatibility work | Broader scripted-document support | Strong | Strong profiles and optional conformance validation | Commercial Java/service integrations | Commercial bakeoff candidate |
| Paged.js | Strong browser input, transformed DOM | Runs in browser | Adds many missing browser features | Relies on browser PDF and downstream tooling | Open source JS plus Chromium | Preview and experimental backend |
| Vivliostyle | Strong for publication-oriented HTML | Browser-dependent | Strong publication layer | Docker PDF/X-1a post-processing | Open source Node/browser/container stack | Experimental publication/press lane |
| Typst | No; requires source translation | No | Native print layout rather than CSS | Strong PDF/A/UA; no arbitrary KPress DOM | Open source standalone compiler | Separate greenfield print-first workflow |
| Tectonic/LaTeX/ConTeXt | No; requires source translation | No | Excellent document-native pagination | Mature PDF workflows; profile handling varies | TeX toolchain or frozen bundle | Separate TeX-authored workflow |
| SILE/SATySFi/Patoline | No; requires source translation | No | Document-native | Varies | Smaller ecosystems | Research reference, not initial backend |

## Key Insights

### One Source of Content Does Not Imply One Layout Engine

KPress can keep one semantic content/print artifact while permitting backend-specific
pagination. Trying to make Chromium, Prince, and WeasyPrint produce the same line and
page breaks is not a useful goal; font metrics, layout algorithms, and CSS coverage
differ. The supported contract should instead require each engine to meet the same
semantic and profile-specific acceptance criteria.

### A Static Print Artifact Is More Important Than a Renderer Abstraction

Prince and WeasyPrint cannot reliably execute an arbitrary web application.
Chromium can, but a `networkidle` event is not an application readiness protocol.
An external formatter therefore needs a static, self-contained print representation in a
known state. Browser export needs an explicit completion boundary even when it does not
serialize a separate static artifact.
Neither requirement means every ordinary KPress HTML build must launch a browser.

Serializing the post-JavaScript DOM is helpful but not sufficient.
Canvas pixels do not survive HTML serialization, shadow DOM and adopted styles require
special handling, and a user’s last interactive choice is not necessarily the canonical
printed choice. Custom components must participate explicitly.

### Determinism Has Three Levels

Any PDF repeatability claim should distinguish three guarantees:

1. **Input determinism:** identical semantic HTML, print CSS, fonts, images, component
   state, metadata, and asset bytes.
2. **Layout determinism:** identical visible pages in an exact engine and environment.
3. **Byte determinism:** identical PDF bytes, including object ordering, IDs, compressed
   streams, creation dates, and producer metadata.

The first two are required for every supported profile.
Byte identity is valuable and should be tested where an engine supports it, but it
should be an additional capability rather than a proxy for visual, semantic, or
standards correctness.

### Vector and Accessibility Are Source Responsibilities Too

No renderer can recover vectors from an already-painted canvas or infer a meaningful
natural-language description of a mathematical proof figure.
The host or component must retain the geometric data, semantic label, and canonical
print state. The renderer can then preserve SVG and tags instead of flattening them.

## Options Considered

### Option A: Harden Chromium Only

Keep one backend and make its invocation, readiness, assets, print CSS, metadata, and
validation explicit.

**Advantages:**

- Best compatibility with arbitrary KPress hosts and modern web components.
- One layout engine for screen and reader PDF.
- Open source and already integrated.
- Lowest implementation and support cost.

**Disadvantages:**

- Missing CSS footnotes, page-aware cross-references, and changing running heads.
- Weaker publication pagination than dedicated formatters.
- No complete, native commercial-press workflow.

**Decision:** Retain as the supported default.
Another backend should earn support by meeting a demonstrated publication requirement
that this path does not satisfy.

### Option B: Add a Dedicated CSS Formatter

Materialize a static KPress print artifact, then render it with Prince and possibly
WeasyPrint or other adapters.

**Advantages:**

- Preserves HTML/CSS as the content boundary.
- Unlocks footnotes, running matter, cross-references, page floats, named pages, and
  stronger production PDF profiles.
- Lets users choose commercial or open-source operational tradeoffs.

**Disadvantages:**

- Requires conservative and backend-specific print CSS.
- Requires a static materialization path for math, diagrams, and app components.
- Adds version matrices, licenses or native dependencies, and more golden output.

**Decision:** Recommended architecture, beginning with a Prince prototype and a
Prince/WeasyPrint bakeoff.

### Option C: Translate KPress into Typst or TeX

Convert Markdown or an intermediate semantic model into Typst, LaTeX, or ConTeXt and
maintain a print-specific template.

**Advantages:**

- Highest ceiling for print-first paragraph, math, bibliography, and page design.
- Strong reproducibility and PDF-standard tooling in several engines.

**Disadvantages:**

- Does not render KPress output; it creates a parallel product.
- Raw HTML, CSS, application components, canvas, and host layout require explicit
  reimplementation.
- Screen and print designs can drift silently.

**Decision:** Do not make this a core KPress backend.
Document it as an advanced escape hatch for projects whose source model is intentionally
print-first.

### Eliminated as Default Backends

- **Interactive browser print:** retained as a convenience action, but user-controlled
  headers, margins, scale, paper, and state prevent production guarantees.
- **[wkhtmltopdf](https://github.com/wkhtmltopdf/wkhtmltopdf):** the upstream repository
  is archived and its legacy browser engine is incompatible with KPress’s modern CSS and
  JavaScript expectations.
- **Screenshot-to-PDF:** rasterizes text and vector graphics, harms search and
  accessibility, and cannot satisfy publication or press requirements.
- **Generic PDF post-processing as the primary renderer:** useful for a narrowly defined
  profile, but cannot repair bad page breaks, missing content, substituted fonts, or
  rasterized source graphics.
  It may also damage tags or links.

## Recommendations

### 1. Introduce Explicit PDF Profiles and Backends

The following is proposed configuration, not a supported API:

```yaml
pdf:
  profile: reader          # reader | publication | press
  backend: chromium        # chromium | prince | weasyprint | external
  page:
    size: Letter
    margin: 0.7in
  metadata:
    creation_date: source-date-epoch
```

The actual public API should follow a separate design issue, but the semantics should be
fixed now:

- profiles state desired guarantees;
- backends state the renderer actually used;
- unsupported profile/backend combinations fail clearly;
- a missing optional engine never silently falls back;
- the report records profile, engine and version, browser revision or container digest,
  source revision, font manifest, page count, warnings, and validation results;
- use Git for repository identity and integrity; reserve artifact digests for external
  inputs, retained binary comparisons, and distribution boundaries.

### 2. Define a KPress Print Artifact Contract

The input to every production backend should be a closed artifact with:

- semantic HTML in a canonical print state;
- all CSS, fonts, images, SVG, and supporting data local and pinned, with an explicit
  asset manifest and external-input provenance;
- a declared document language for shaping and hyphenation;
- fixed page metadata and a canonical timezone/locale;
- no required network access;
- no unresolved math, diagram, image, or custom-component work;
- an explicit light/print color state;
- a stable default for tabs, disclosures, filters, and other interactive choices;
- static print alternatives for components that cannot serialize themselves; and
- diagnostics proving those conditions, rather than a delay chosen by guesswork.

For browser materialization, extend the existing math completion contract to the other
components and registered host work.
Successful image decoding, diagram completion, queued work, and print-triggered redraws
need explicit settlement.
Use the shared math runtime’s per-formula promises; `document.fonts.ready` alone cannot
account for a font request that future work has not issued.
Margin-box fonts also require explicit requests because they are outside the ordinary
document tree. A host-facing hook could conceptually be
`kpress.registerPrintTask(promise)` or a single `preparePrint()` callback.
These names are proposals.
The exact API needs design, including a distinction between successful completion and
bounded failure recovery, component names, and actionable failure output.
Switching to print must invoke the completion path for that media; an initial
screen-ready marker is insufficient.

From navigation onward, the browser should reject network access and allow only declared
artifact, `data:`, and intentionally produced `blob:` resources.
External formatters should receive equivalent no-network/no-undeclared-file policies.
Remote URLs, font substitution, console errors, failed resources, and unresolved custom
elements should fail the artifact rather than merely warn in a debug log.

### 3. Add a Print Representation Contract for Custom Components

Define three levels:

1. **CSS-only component:** the same semantic DOM prints with portable CSS.
2. **Materialized component:** browser code produces a static semantic DOM or inline SVG
   before the print artifact is sealed.
3. **Alternate component:** the host supplies an explicit `.kpress-print-only`
   representation and the interactive form is `.kpress-no-print`.

Canvas should require level 2 or 3 for the publication profile.
A reader PDF may permit a pinned-resolution raster canvas if its dimensions and color
state pass checks, but KPress should never call it vector or press quality.

For Squares, the canonical publication representation should be generated SVG for all
geometric figures whose data is already available.
Controls should be removed, the initial certificate should be fixed independently of
user history, captions should remain semantic, and every meaningful figure should carry
an accessible description.
The screen canvas remains free to optimize interaction.

### 4. Make Print CSS Portable by Construction

Split the styling responsibility into:

- `print.css`: conservative cross-backend rules, paper palette, semantic visibility,
  sizing, basic breaks, font policy, and fallback running matter;
- `print-chromium.css`: Chromium-specific limitations and workarounds;
- `print-prince.css`: richer page groups, footnotes, running strings, cross-references,
  and PDF production extensions; and
- a future `print-weasyprint.css` only if the bakeoff earns support.

Select the layer with an injected backend data attribute or explicit stylesheet rather
than assuming `@supports` can identify paged-media behavior reliably.
Every host must be able to add print CSS after KPress defaults.

Set paper size and margins in exactly one authoritative place.
The preferred design is for KPress to inject a literal
`@page { size: ...; margin: ... }` rule and call Chromium with `preferCSSPageSize: true`
and scale 1. Avoid a CSS variable in `size` until every supported backend proves it
works.

Make generated running matter configurable and default-safe:

- explicitly disable Chromium’s header/footer templates;
- distinguish browser UI headers from KPress CSS margin boxes;
- permit no footer, document title, section title where supported, and page `n` or
  `n / total`;
- keep URLs out of prose margins unless the author opts in; and
- test first, blank, left, and right pages separately.

Use print-safe sRGB fallbacks for modern screen color functions even when an engine
claims Color 4 support.
For a press profile, use an explicit output intent and backend-supported CMYK policy
rather than visually converting colors by hand.

### 5. Harden the Chromium Reader Backend First

Before adding another engine, make the existing path reliable:

- explicitly set print media, backgrounds, scale 1, CSS page-size preference, no browser
  header/footer templates, tagged output, and document outline;
- retain page-level shell release and test host `html/body` overflow so it cannot
  truncate the document;
- extend the implemented math and print-font waits into the proposed host-readiness and
  closed-asset protocol;
- make browser console errors, page errors, failed requests, and font fallback visible
  in `PdfReport` and fatal under strict mode;
- record the exact Playwright version and Chromium revision;
- run production exports in a pinned container or otherwise frozen OS/font stack;
- control title, author, subject, language, creation/modification time, locale, and
  timezone; and
- expand the existing real-font PDF tests into complete artifact checks, using the
  Squares exporter and its retained controls as evidence for the host boundary.

This work alone should produce a recommended, dependable KPress process for most users.

### 6. Prototype Prince, Then Run a Measured Bakeoff

Build a thin Prince adapter around the same print artifact.
Do not expose a broad stable API until it has rendered:

- a KPress typography and pagination torture document;
- the Squares explainer;
- long tables, code, footnotes, links, nested lists, RTL and non-Latin samples;
- missing-font and missing-asset negative controls; and
- reader, publication, and one agreed press fixture.

Run the same corpus through Chromium, Prince, and WeasyPrint.
Add PDFreactor, Antenna House, Paged.js, or Vivliostyle when licensing and setup permit.
Score observed results on:

- content and DOM fidelity;
- paragraph color, hyphenation, math, and font shaping;
- page breaking, floats, footnotes, cross-references, and running matter;
- SVG/vector preservation and raster resolution;
- links, outline, text extraction, tag tree, and reading order;
- PDF/A, PDF/UA, or PDF/X validation where claimed;
- cold/warm build time and memory;
- same-environment repeatability;
- diagnostics, sandboxing, and operational complexity; and
- license and distribution constraints.

Prince should become the recommended publication backend only after it wins that
measured corpus. WeasyPrint should become a supported backend only if its browser-CSS
differences can be contained in an understandable print layer.

### 7. Validate Artifacts at Multiple Levels

For every supported backend, validation should include:

1. **Build closure:** no undeclared URL or file access; all expected fonts and assets
   present; no unresolved component state.
2. **PDF structure:** expected page count and dimensions, trim/bleed boxes when
   relevant, embedded fonts, links, outline, metadata, language, and tags.
3. **Semantic extraction:** headings, prose, math alternatives, captions, and reading
   order remain usable.
4. **Visual regression:** render pages with a pinned PDF rasterizer and compare selected
   pages or regions with controlled tolerances.
5. **Repeatability:** render twice in the same frozen environment; compare structural
   reports and page images, then bytes when the backend promises byte stability.
6. **Standards validation:** use [veraPDF](https://docs.verapdf.org/validation/) for
   machine-checkable PDF/A and PDF/UA claims.
   Use the formatter’s conformance checks and a production preflight tool for PDF/X and
   printer-specific policy.
7. **Human proof:** inspect the full document at normal zoom and print representative
   pages. Automated conformance cannot judge typographic rhythm or whether a proof figure
   is intelligible.

Do not normalize every output through an unconditional Ghostscript pass.
Post-processing must be profile-specific and revalidated because it can change color,
fonts, transparency, links, tags, metadata, and byte identity.

### 8. Use Squares as a Release-Gate Corpus, Not a One-Off Demo

A supported implementation should make these Squares assertions reproducible:

- the full report paginates; fixed-height page shells cannot truncate it;
- the printed certificate and all interactive defaults are canonical, not user-history
  dependent;
- all math is complete before pagination and remains selectable or meaningfully tagged;
- inline and display math obey the host’s surrounding-size policy in prose and sans
  contexts; actual inline caption baselines agree with adjacent text;
- prepared geometry covers all supported saved font settings, preserves inline wrapping,
  and matches final print dimensions and baselines;
- geometric figures remain vector where a vector source exists;
- any permitted raster canvas has a declared effective DPI at final print size;
- dark-mode screen state cannot leak into paper output;
- controls and hover-only explanations are absent or replaced with static prose;
- captions stay with figures without creating pathological blank regions;
- dense atlas labels remain legible at final size;
- fonts are embedded without unexpected substitution;
- URLs, page numbers, and KPress branding appear only when configured; and
- two builds in the reference environment have identical content, layout report, and
  rendered-page images, with byte identity recorded separately.

## Proposed Delivery Sequence

Parts of the Chromium baseline and optional host preparation are implemented, as
distinguished above.
These phases describe the remaining generic PDF work; they do not create a new mandatory
font, formula, or browser build step.

### Phase 1: Honest Chromium Baseline

- Define reader/publication/press terminology in the public design.
- Complete Chromium options, host readiness, asset closure, metadata, diagnostics, and
  artifact tests beyond the implemented print-font checks.
- Add a generic full-page host-shell print fixture and the Squares truncation case.
- Document a pinned local/CI process.

### Phase 2: Static Print Artifact and Component Hooks

- Specify materialization and readiness hooks.
- Reuse KPress math fallback and hydration; add the missing static export contracts for
  diagrams, tabs, disclosures, and custom graphics.
- Produce SVG print alternatives for the Squares canvases.
- Emit a machine-readable artifact and engine manifest.

### Phase 3: Publication Backend Bakeoff

- Implement a private Prince adapter and a WeasyPrint spike.
- Render the shared corpus and publish the comparison report and sample PDFs.
- Choose supported backend names and capability boundaries from observed results.

### Phase 4: Production Profiles

- Add Prince as an optional supported publication backend if it passes.
- Add WeasyPrint only if the compatibility and maintenance budget is acceptable.
- Define PDF/A/UA claims and validation gates.
- Add a press profile only alongside an actual printer specification and end-to-end
  PDF/X preflight.

## Next Steps

- [x] Reconcile the research with implemented KPress math/print-font behavior and
  source-qualified Squares startup, layout, baseline, and PDF evidence (`kpr-i91n`).
- [ ] Open a design bead for the three PDF profiles and print artifact contract.
- [ ] Scope the remaining Chromium reader work against existing PDF font tests and host
  export checks.
- [ ] Create the KPress paged-media torture fixture and import or invoke Squares as an
  external acceptance fixture.
- [ ] Design the print readiness and custom-component representation hooks.
- [ ] Create vector print representations for the Squares canvas figures.
- [ ] Run the Chromium/Prince/WeasyPrint bakeoff and retain the engine manifests,
  structural reports, visual comparisons, and sample PDFs.
- [ ] Decide whether Prince and WeasyPrint earn stable backend status.
- [ ] Specify tested input, layout, and byte-repeatability guarantees in
  `kpress-design.md` for each supported export profile.
- [ ] Define PDF/A, PDF/UA, and any PDF/X validation policy only after the backend
  decision.

## Methodology and Confidence

The September 5 engine survey combined:

- direct inspection of KPress’s PDF implementation, print CSS, tests, design, and host
  integration documentation;
- direct inspection of the Squares explainer templates, renderer, print workarounds,
  deterministic Pages workflow, and vector atlas generation;
- W3C paged-media drafts;
- current official documentation for each engine; and
- cross-checking orchestration choices against Pandoc’s supported PDF engines.

The September 8 reconciliation additionally inspected KPress `4a868bb`, the shared math
runtime and architecture, the static print-font path, and the retained Squares reports
linked above.
It preserves the original font measurements in their research documents and
keeps each startup or PDF result attached to its tested source.
No new engine bakeoff or performance measurement was run for this revision.

The architectural conclusions have high confidence: arbitrary web applications require a
browser-compatible path, dedicated formatters require static inputs, and Typst/TeX
translation creates a second rendering system.
Prince’s first-prototype priority is an architectural recommendation.
The relative rendering quality and compatibility of Prince and WeasyPrint on KPress
remain unmeasured. Vendor documentation establishes available controls, not the quality
of a specific KPress document.

## References

### KPress and Squares

- [KPress PDF backend](../../../src/kpress/format/pdf.py)
- [KPress print stylesheet](../../../src/kpress/format/static/css/print.css)
- [KPress design: print and PDF](../../kpress-design.md#print-and-pdf)
- [KPress operations and host integration](../../kpress-operations-and-host-integration.md)
- [Font and math loading architecture](../architecture/arch-2026-09-08-font-and-math-loading.md)
- [Host math API](../../math-rendering-api.md)
- [Print sans measurements](research-2026-09-07-print-sans-faces.md)
- [KPress real PDF font tests](../../../tests/test_playwright_print_pdf_fonts.py)
- [Squares retained startup campaign for dab2a381](https://github.com/jlevy/squares/tree/dfa0a422/packing/benchmarks/math-startup)
- [Squares caption-baseline and PDF acceptance at a10569d1](https://github.com/jlevy/squares/actions/runs/34288782889)
- [Squares explainer article](https://github.com/jlevy/squares/blob/main/packing/devtools/templates/explainer-article.md)
- [Squares explainer shell and print adaptations](https://github.com/jlevy/squares/blob/main/packing/devtools/templates/explainer-shell.html)
- [Squares deterministic render workflow](https://github.com/jlevy/squares/blob/main/.github/workflows/pages.yml)
- [Squares vector atlas generator](https://github.com/jlevy/squares/blob/main/packing/devtools/build_known_best_atlas.py)
- [Squares vector atlas PDF conversion](https://github.com/jlevy/squares/blob/main/packing/devtools/render_composite_pdf.py)
- [Squares rendering dependencies and PDF reproducibility note](https://github.com/jlevy/squares/blob/main/packing/pyproject.toml)

### Standards and Browser Rendering

- [W3C CSS Paged Media Module Level 3](https://www.w3.org/TR/css-page-3/)
- [W3C CSS Generated Content for Paged Media Module](https://www.w3.org/TR/css-gcpm-3/)
- [Chrome: page-margin content for printing](https://developer.chrome.com/blog/print-margins)
- [Playwright `page.pdf()`](https://playwright.dev/docs/api/class-page#page-pdf)
- [Paged.js overview](https://pagedjs.org/en/about/)
- [Paged.js developer documentation](https://pagedjs.org/devdocs/)
- [Vivliostyle CLI](https://docs.vivliostyle.org/en/cli/getting-started/)
- [Vivliostyle special output settings](https://docs.vivliostyle.org/en/cli/special-output-settings/)

### Dedicated Formatters

- [Prince 16 release notes](https://www.princexml.com/releases/16/)
- [Prince paged media](https://www.princexml.com/doc/paged/)
- [Prince PDF output](https://www.princexml.com/doc/prince-output/)
- [Prince scripting](https://www.princexml.com/doc/javascript/)
- [WeasyPrint API and supported features](https://doc.courtbouillon.org/weasyprint/stable/api_reference.html)
- [Antenna House Formatter overview](https://www.antenna.co.jp/AHF/help/en/ahf-about.html)
- [Antenna House HTML formatting notes](https://www.antenna.co.jp/AHF/help/en/ahf-tech.html#formatting-html)
- [PDFreactor manual](https://www.pdfreactor.com/product/doc_html/manual-lib.html)

### Modern Typesetters and Orchestration

- [Typst PDF export](https://typst.app/docs/reference/pdf/)
- [Typst paragraph line breaking](https://typst.app/docs/reference/model/par/#parameters-linebreaks)
- [Typst math](https://typst.app/docs/reference/math/)
- [Typst document metadata](https://typst.app/docs/reference/model/document/#parameters-date)
- [Typst experimental HTML export](https://typst.app/docs/reference/html/)
- [Tectonic](https://tectonic-typesetting.github.io/en-US/)
- [ConTeXt LMTX](https://wiki.contextgarden.net/LMTX)
- [SILE](https://sile-typesetter.org/)
- [SATySFi](https://github.com/gfngfn/SATySFi)
- [Patoline](https://github.com/patoline/patoline)
- [Pandoc PDF engine selection](https://pandoc.org/MANUAL.html#option--pdf-engine)
- [Quarto PDF basics](https://quarto.org/docs/output-formats/pdf-basics.html)
- [veraPDF validation](https://docs.verapdf.org/validation/)

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
