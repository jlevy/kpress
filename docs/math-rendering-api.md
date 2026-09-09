# Rendering Mathematics in a Host

The
[font and math loading architecture](project/architecture/arch-2026-09-08-font-and-math-loading.md)
explains the publication and runtime phases, their ownership, and the layout guarantees.
This reference defines the host-facing methods and attributes.

Use `globalThis.kpressMathText.render()` for mathematics rendered by an embedding
application. It selects the metric tables, renders hidden markup, and restores the
default tables synchronously, then awaits the matching fonts before revealing the
result. The native KPress initializer uses the same runtime.

## Assets and First Paint

Load these classic scripts in order:

1. `katex/katex.min.js`
2. `katex/katex-text-metrics.js`
3. `katex/katex-math-runtime.js`

KPress includes the runtime in `KATEX_JS_ASSETS`, before `katex-init.js`. A host with
its own render loop can omit `auto-render.min.js` and `katex-init.js`. Include both
stylesheets in `KATEX_CSS_ASSETS`. When inlining their fonts, resolve each relative URL
against its stylesheet directory.

The existing `js/theme-bootstrap.js` runs in the head before content is parsed.
It temporarily hides native MathML while JavaScript enhancement is pending, retaining
its layout space. Call `complete()` when the initial render batch has settled.
A three-second watchdog restores the native fallback if enhancement never starts.
With JavaScript disabled, MathML remains visible.

## Rendering a Formula

```javascript
const node = document.querySelector("#formula");
await kpressMathText.render("x^2 + 1", node, { throwOnError: false });
```

The node must be attached to the document so its CSS context can be resolved.
The promise resolves with a `status` of `ready`, `superseded`, or `unavailable` when the
browser has no font loading API. A parse error rejects when `throwOnError` is enabled;
with `throwOnError: false`, KaTeX renders its error markup.
A required font that fails or exceeds the three-second wait rejects the promise.
A native KPress formula then keeps its semantic MathML; a host should provide its own
readable fallback:

```javascript
try {
  await kpressMathText.render(source, node, { throwOnError: false });
} catch {
  node.textContent = source;
}
```

Each call enforces readiness, including calls from early resize observers or user
events.
Calls for the same node follow the latest request: an older pending call resolves
as `superseded` and cannot replace the newer formula.
Metric installation, KaTeX rendering, and metric restoration run synchronously together
as soon as the call starts.

The runtime renders with visibility suppressed, reads the font descriptions and
characters of the resulting HTML, and awaits a separate native `document.fonts.load()`
promise for each family in the computed fallback list.
Each request uses the rendered run’s style, weight, size and characters.
An empty result means that family has no matching declared face; the following families
are still awaited independently.
This also covers large operators, delimiters, AMS symbols and explicit math alphabets.
Decoded faces and resolved requests reuse their cached results; families, styles and
weights absent from the rendered requests do not delay a formula.

If the selected composite family has no registered font declarations, the runtime uses
stock KaTeX families and their original metric tables for that formula.
This covers a missing composite stylesheet as well as an omitted family; another
composite family can still render normally.
Declared faces that fail to load still follow the required-face error handling above.

## Hydrating Prepared Geometry

A host can prepare KaTeX markup and reserve its exact geometry during publication, then
call `hydrate()` to await its glyph fonts without replacing that markup:

```javascript
await kpressMathText.hydrate(source, node, { displayMode: false }, context);
```

The runtime does not measure or reserve initial geometry itself.
Plain KaTeX HTML still takes its text widths from the browser’s current fonts, so a host
that needs stable space before font decoding must reserve measured widths, heights and
baselines in its publication output.
Keeping reservations per unbreakable KaTeX `.base` preserves the formula’s line-breaking
opportunities. This optional publication step does not add a browser dependency to
ordinary KPress HTML generation.

For absolutely positioned bases, the visible glyphs must share the reservation’s
baseline. The
[preparation contract](project/architecture/arch-2026-09-08-font-and-math-loading.md#publication-preparation-and-hydration)
describes copying the ordinary measured height and depth onto each existing KaTeX strut
and using zero line height on prepared bases and their inline carriers.
Validate actual baseline alignment at screen and print sizes; `hydrate()` preserves host
markup but does not verify or repair its geometry.

`render()` stamps the following metadata on its target:

| Attribute | Value |
| --- | --- |
| `data-kpress-math-source` | The exact TeX string passed to the runtime |
| `data-kpress-math-display` | `inline` or `display` |
| `data-kpress-math-profile` | `prose`, `sans` or `katex` |

After reserving geometry, the host adds `data-kpress-math-prepared="true"`. `hydrate()`
retains the DOM only when all four attributes match the request and its resolved
profile, and a `.katex` descendant exists.
A changed source, display mode, sans context, stock opt-out or missing composite family
causes normal rendering, which removes the prepared mark and replaces the old geometry.
The host must supply the same KaTeX bundle, generated metrics, math styles, remaining
rendering options and macros used at publication.
`render()` always replaces markup; it never reuses prepared content implicitly.

Hydration uses the same actual-glyph font checks, three-second deadline and
latest-request handling as rendering.
Screen and print font requests are cached separately.
The host controls initial visibility before its scripts run and may reveal each prepared
target when its hydration promise succeeds.
It should retain a readable no-JavaScript fallback and handle a rejected hydration just
like a rejected render.

## Sans Contexts and Opt-Outs

The runtime recognizes KPress captions, tables, footnotes and other sans roles.
A host can extend that decision with a callback:

```javascript
const context = {
  isSansContext: node => Boolean(node.closest(".my-figure-readout")),
};
await kpressMathText.render(source, node, { displayMode: false }, context);
```

The callback adds sans contexts to KPress’s own roles.
Both the metric table and the `data-kpress-math-face="sans"` attribute come from this
decision. Re-rendering a node in prose removes a stale sans mark.

The existing `data-kpress-math-text="katex"`, `data-kpress-fonts="system"` and
`data-kpress-font-set="system"` opt-outs take precedence, including on the node itself.
The generated metrics asset retains the original tables under `katex`, so an opted-out
formula can use stock metrics after another formula used the custom face.
The runtime marks that node `data-kpress-math-face="katex"` so its CSS families also
revert inside a wrapper that otherwise uses the custom face.
When the whole document opts out before any custom rendering, the runtime leaves KaTeX’s
existing metric tables untouched, including a host’s experimental replacements.

## Preparing a Batch

`ready(nodes, context)` explicitly warms the selected composite slots and KaTeX Main and
Math families before rendering a batch.
It initializes the tables independently of the native initializer and returns a promise
with status `ready`, `empty`, `error`, `timeout` or `unavailable`. The diagnostic
`globalThis.kpressMathFaceWait` lists the individual requests and outcomes.
Neither `render()`, `hydrate()` nor native enhancement calls `ready()` automatically.
An unused warmup failure does not discard a formula whose own glyph faces load.

```javascript
await kpressMathText.ready(nodes, context);
await Promise.all(formulas.map(({ source, node }) =>
  kpressMathText.render(source, node, { throwOnError: false }, context)
));
kpressMathText.complete();
```

A host that embeds a deliberately pruned set of fonts can pass
`{ ...context, allEmbeddedFonts: true }` to prepare all of its declared font faces.
This option applies only to `ready()` and is intended for self-contained documents.
It would download unused faces if enabled on an ordinary site with the complete KPress
font set.

For synchronous measurements after preparation, `installTablesFor(node, context)`
returns `prose`, `sans`, `katex` or `null`, and `restore()` reinstalls the default serif
tables. If tables have already been installed but the next selected set is unavailable,
`installTablesFor()` throws before rendering can use mismatched metrics.
These methods do not wait for fonts; application rendering should use `render()` or
`hydrate()`.

The composite fonts are CSS families over separate PT Serif, Source Sans and KaTeX font
files. They are not merged font binaries.
Their layout metrics are generated ahead of time, but each browser still has to decode
the selected font faces.
Inlining the bytes removes a network request; the readiness contract also covers
decoding.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
