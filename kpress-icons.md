---
title: KPress Icons
description: The shared icon set for KPress — one SVG sprite as the source of truth, the SVG contract, how server and client reference glyphs, how to add one, how to swap icon families, and the kpress<->metabrowser glyph map.
author: Claude under Levy
---
# KPress Icons

KPress draws its chrome from one icon family: [Lucide](https://lucide.dev) v1.17.0 (ISC
license). Lucide is the maintained successor to Feather Icons, same 24×24 stroke grid,
~1,600 glyphs. Picking one family with a recorded version lets us add glyphs that match
by construction and swap the whole set deliberately if we ever want a different look.

The glyphs live in a real **SVG sprite file**, not embedded in Python or JS. KPress is a
dependency-light, server-rendered Python layer whose job is document processing; the
icon artwork is front-end code and belongs in a front-end format.
We copy the few glyphs we use into the sprite and record where each came from.

## The single source of truth

[`src/kpress/format/static/icons/icons.svg`](src/kpress/format/static/icons/icons.svg)
is the one place KPress SVG geometry lives.
It is a hidden sprite — a `<svg style="display: none">` holding one
`<symbol id="kpress-icon-<name>">` per glyph.

- **Server side**, `render.py` inlines the sprite once per document (in
  `render_fragment`, via the cached `_icon_sprite()`), and its
  `_icon(name, *, css_class, attrs)` helper emits a glyph as
  `<svg …><use href="#kpress-icon-<name>"></use></svg>`.
- **Client side**, [`static/js/icons.js`](src/kpress/format/static/js/icons.js) exports
  `icon(name, className)`, which builds the same
  `<svg><use href="#kpress-icon-<name>"></svg>` reference.
  `code-copy.js` imports it for the copy/check/error glyphs.

So there is **no SVG geometry authored in Python or JS** — both sides only build a
`<use>` reference into the sprite.
`tests/test_icons.py` enforces this: it asserts the sprite defines every required symbol
and that no `<path>`/`<rect>`/`<circle>`/`<line>`/`<polygon>` markup appears in
`render.py`, `icons.js`, or `code-copy.js`.

We inline the sprite into the document rather than linking it as an external file
because external `<use href="file.svg#id">` references render blank in several engines
(notably headless Chromium and across some sandbox/CSP setups).
Inlining one hidden sprite is a few hundred bytes, deduplicated per document, and Just
Works everywhere.

## The SVG contract

Every glyph is a stroke icon on Lucide’s grid.
The wrapper attributes live on each `<symbol>` (so a `<use>` needs no attributes of its
own):

- `viewBox="0 0 24 24"`
- `fill="none"`
- `stroke="currentColor"` — the icon takes its color from CSS `color`
- `stroke-width="2"`
- `stroke-linecap="round"` `stroke-linejoin="round"`
- Size comes from CSS (`width`/`height` or the button box) on the referencing `<svg>`,
  never hard-coded per glyph.
- Accessibility: the referencing `<svg>` is decorative (`aria-hidden="true"`); the
  interactive control around it carries the `aria-label`/`title`. Icons never contain
  the visible label text.

Any glyph that satisfies this contract drops in without visual drift.
That is the whole reason to stay inside one stroke family — mixing in a filled family
(e.g. Phosphor, which uses a 256 viewBox and `fill="currentColor"`) breaks the contract
and looks inconsistent.

## Glyph map

The KPress sprite carries exactly the glyphs KPress chrome uses.
The name is the symbol id suffix (`kpress-icon-<name>`); the Lucide id it came from is
recorded so any glyph can be re-fetched or swapped without guessing.
Lucide renamed several Feather glyphs (noted), which is why an id sometimes differs from
the obvious word.

| Sprite name | Lucide id | Used for |
| --- | --- | --- |
| `settings` | `settings` | Settings-menu trigger (gear) |
| `monitor` | `monitor` | “System theme” choice |
| `sun` | `sun` | “Light theme” choice |
| `moon` | `moon` | “Dark theme” choice |
| `x` | `x` | Video / overlay close |
| `copy` | `copy` | Code-copy button (idle) |
| `check` | `check` | Code-copy button (copied) |
| `maximize` | `maximize` | Media maximize affordance |
| `external-link` | `external-link` | External-link marker |
| `list` | `list` | Collapsed TOC toggle |
| `triangle-alert` | `triangle-alert` (was Feather `alert-triangle`) | Code-copy error state |

**MetaBrowser** (an embedding host application, developed in its own repository) keeps
its own glyph set today (`metabrowser/static/icons.js` in that repo), a superset that
also has app-chrome glyphs KPress does not need (`folder`, `file`, `file-text`,
`layout-grid`, `activity`, `printer`, `box`, `chevron-right`, and the bespoke
reading-font `serif`/`sans` and viz `step` shapes).
It shares the same Lucide family and attribute signature so overlapping glyphs match
KPress. The direction (see `kpress-design.md`) is for MetaBrowser to lean on the KPress
sprite for the shared glyphs rather than keep its own copies; that move is tracked
separately and not yet done.

## How to add a glyph

1. Find it at https://lucide.dev/icons and note its id.
2. Fetch the pinned-version source rather than eyeballing the path:
   ```
   curl -fsSL https://unpkg.com/lucide-static@1.17.0/icons/<id>.svg
   ```
3. Add a `<symbol id="kpress-icon-<name>" …>` to `icons.svg`, copying only the **inner**
   elements (everything between Lucide’s `<svg …>` and `</svg>`) and giving the symbol
   the contract wrapper attributes
   (`viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"`).
4. Reference it where needed: `_icon("<name>")` in `render.py`, or `icon("<name>")` in
   client JS. Nothing else to register — the sprite is the registry.
5. Update the glyph map above (and add `<name>` to `_REQUIRED_ICONS` in
   `tests/test_icons.py` if it is part of the guaranteed set).
6. Regenerate goldens and review that the diff is icon-only:
   ```
   KPRESS_UPDATE_GOLDENS=1 uv run pytest tests/ -k golden
   ```

## How to switch icon families

The version pin and per-symbol provenance make a family swap mechanical rather than
archaeological. Because every glyph is one `<symbol>` in one file, the swap touches only
`icons.svg` (plus this doc):

1. Confirm the new family honors [the SVG contract](#the-svg-contract) — same 24×24
   stroke grid (or be ready to change `viewBox`, `fill`, and stroke attrs on the
   symbols).
2. List every glyph in use: the names in [the glyph map](#glyph-map).
3. Map each Lucide id to the new family’s equivalent (most families share obvious names;
   record any renames the way Lucide’s `triangle-alert` is recorded here).
4. Re-fetch and re-inline each glyph’s inner elements into its `<symbol>`, updating the
   family/version header comment at the top of `icons.svg` and this doc.
5. Regenerate KPress goldens and do a visual pass across the three KPress consumers
   (standalone page, static site, MetaBrowser embed) in light and dark.

## Future: pluggable icon sets in KPress

The glyphs now live in one front-end-native file with the family/version/license in the
sprite header. The remaining seam, not worth building until a consumer needs it (brand
icons, a different family for one site):

- Let `render_*` accept an optional sprite override (an alternate `icons.svg`, or a
  name→symbol map merged over the built-in set) so the default stays batteries-included
  and zero-config.
- Have MetaBrowser consume the KPress sprite for the shared glyphs instead of
  duplicating them, keeping one source of truth across the two packages.

Until there is a real second consumer, the single sprite plus this doc are the right
amount of structure.
The provenance comments are what make the eventual extraction cheap.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
