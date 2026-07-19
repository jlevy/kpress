---
title: Content-Size Indicators
description: Optional document-level and per-section word counts and reading time via a flexdoc metrics extra
author: Joshua Levy (with Claude)
---
# Feature: Content-Size Indicators (Word Counts and Reading Time)

**Date:** 2026-07-18

**Author:** Joshua Levy (with Claude)

**Status:** Draft (possible future enhancement)

**Tracking:** `kpr-lrfg`.

## Overview

An optional feature that annotates a rendered document with content-size indicators at
two grains:

- **Document level:** total word count and estimated reading time (e.g. “4,200 words ·
  19 min read”), rendered after the document title.
- **Top-section level:** a word count on each top-level body section — the headings the
  TOC lists at depth 1, which is H2 in the common one-H1-title document shape.

Counts use **flexdoc’s normalized logical-word calculation**
([github.com/jlevy/flexdoc](https://github.com/jlevy/flexdoc), the `TextUnit.words`
semantics), not naive whitespace splits, so prose, code, and wide/CJK scripts measure
consistently and the numbers agree with other flexdoc-based tooling.
Reading time derives from the same count via flexdoc’s `format_read_time` (225 wpm
default).

The feature is off by default, enabled through the typed config/render-options surface,
with flexdoc as a new optional dependency extra.
Hosts style or reposition the indicators through the design-system seams, or take the
counts as data and render their own presentation.

## Goals

- Opt-in with a hard zero-drift guarantee: byte-identical output when disabled, and no
  new install weight for hosts that don’t enable it.
- Word counts computed from the Markdown source with flexdoc’s logical-word metric;
  section counts roll up subsections (the slice from a top-level heading to the next
  top-level heading).
- Reading time derived from the same counts via flexdoc’s `format_read_time`.
- Indicators rendered as contract-registered structural markup with `data-kpress-*`
  attributes, styleable through the token system; hosts can restyle or hide either grain
  without forking.
- Computed counts also exposed as data (on the parsed tree and in the page model) so
  hosts can render their own presentation instead of the built-in markup.
- Works identically across the static publish path, fragment rendering, and the
  dynamic-host path.

## Non-Goals

- No counts at deeper grains (H3+ sections, paragraphs).
- No LLM-token estimates or other `TextUnit`s in the UI.
- No per-section reading-progress or scroll-linked UI.
- No configurable words-per-minute knob initially (flexdoc’s 225 wpm default; add a
  config field later if a host needs it).

## Background

- **flexdoc provides the calculations.** `flexdoc.util.word_count.logical_word_count` is
  the documented, validated logical-word metric (clamped average word length, 0.5-weight
  wide characters); `flexdoc.util.read_time.format_read_time` formats reading time from
  it (`DEFAULT_WORDS_PER_MINUTE = 225`, with a minimum-time threshold that returns `""`
  for content too short to warrant a label).
  Both are lightweight (stdlib + prettyfmt).
  flexdoc’s full `FlexDoc` model also offers `sections()` with
  `Section.size(unit, subtree=True)` rollups, but KPress does not need the second parser
  (see Approach).
- **Release dependency.** The logical-word metric landed on flexdoc `main` after the
  `v0.3.0` release (`v0.3.0` still has the older rough `words` count).
  Shipping this feature requires a flexdoc release containing `logical_word_count`,
  which the `metrics` extra then exact-pins.
  flexdoc is first-party (`github.com/jlevy/*`), so the supply-chain cool-off does not
  delay adoption once released.
- **KPress’s HTML is flat.** Headings render as bare `<h2 id="…">` siblings inside one
  `.kpress-prose` stream — there are no per-section wrapper elements.
  Section indicators are therefore injected adjacent to headings, not into containers.
  KPress already has the authoritative heading walk (`_add_heading_ids`,
  `format/markdown.py`) and the structural-depth-normalized TOC builder (`_toc_entries`,
  `format/markdown.py`) over markdown-it tokens.
- **Config precedent.** Feature flags live on `FormatConfig` (`publish/config.py`) and
  `RenderOptions` (`format/model.py`) — cf.
  `show_doc_header`, `show_frontmatter`, and the `TocMode` on/off/auto enum.
  A new YAML key must also be added to `_KNOWN_FORMAT_KEYS`, `load_config()`, and the
  config→`RenderOptions` threading in `publish/build.py`.
- **Contract registry.** New `kpress-*` classes, `data-kpress-*` attributes, and
  page-model keys must be registered in `src/kpress/contract.py` (`PUBLIC_CSS_CLASSES`,
  `PUBLIC_FRAGMENT_CSS_CLASSES`, `PUBLIC_DATA_ATTRIBUTES`, `PUBLIC_PAGE_MODEL_KEYS`);
  the contract tests enforce this.
- **Dependency rules.** `kpress.format` must import without `kpress.publish` and without
  heavy optional machinery at import time (`docs/kpress-design.md`, dependency rules);
  optional capability ships as an extra with a deterministic
  `KPressMissingOptionalDependencyError` (the `kpress[pdf]`/`kpress[optimize]` pattern).
  A new packaging tier requires a design-doc update and an issue before implementation.
  The supply-chain policy exempts first-party `github.com/jlevy/*` packages from the
  14-day cool-off but requires exact pins and listing in the first-party table
  (`SUPPLY-CHAIN-SECURITY.md`); flexdoc qualifies but is not yet listed.
- **Style precedent.** `.kpress-source-meta` (`document.css`) is the existing muted
  metadata-label idiom: sans family, `--kpress-doc-muted`, small size tokens
  (`--kpress-font-size-smaller`).

## Design

### Approach

**Compute in KPress’s own parse, with flexdoc as the metric.** KPress already walks the
markdown-it token stream to assign heading ids and build the normalized TOC. The feature
reuses that walk: slice the body Markdown source between consecutive top-level headings
(via markdown-it `token.map` line ranges) and measure each slice — and the whole body —
with flexdoc’s `logical_word_count`. Reading time comes from `format_read_time`.

This was chosen over parsing the document a second time with the full `FlexDoc` model
because a dual parse risks section-attribution mismatches between two parsers’ heading
views (setext headings, HTML headings, level normalization), carries flexdoc’s heavier
model dependencies for no gain, and the section slices are equivalent: a top-level
section’s slice runs to the next top-level heading, which is exactly flexdoc’s subtree
rollup, and both measure the slice text as a whole with the same word function.
The section set that gets indicators is *defined* as the headings the rendered TOC lists
at depth 1, so indicators can never disagree with the displayed structure.

Semantics:

- **Document count:** the whole body Markdown (frontmatter is already separated upstream
  and never counted; preamble before the first heading and the title line are included).
- **Section count:** from the section’s heading line through the line before the next
  same-depth-or-shallower heading (i.e. subsections included).
- **Reading time:** `format_read_time(words)`; when it returns `""` (below the
  minimum-time threshold) the time part is omitted and the indicator shows words only.
- Zero-word documents or sections emit no indicator.

### Components

- **Optional extra `kpress[metrics]`** — `flexdoc==<exact version>` in
  `[project.optional-dependencies]` (first release containing `logical_word_count`).
  Lazy import inside the enabled code path only; enabling the feature without the extra
  raises `KPressMissingOptionalDependencyError` with the standard deterministic message.
  Add flexdoc to the first-party exemption table in `SUPPLY-CHAIN-SECURITY.md` and
  update the packaging-tier section of `docs/kpress-design.md`.

- **`format/model.py`**
  - `ContentSizeMode = Literal["off", "data", "on"]` — `off` (default): no computation,
    byte-identical output; `data`: compute and expose counts, no markup; `on`: compute,
    expose, and render indicators.
  - `RenderOptions.content_size: ContentSizeMode = "off"`.
  - `DocumentTree.content_size: ContentSizeInfo | None` — dataclass with `words: int`,
    `read_time: str` (empty when below threshold), and
    `sections: list[SectionContentSize]` (`heading_id`, `words`, `read_time`), populated
    when mode ≠ `off`; available to `transform_tree` hooks and hosts.

- **`format/markdown.py`** — computation beside the existing heading walk: derive
  top-level section spans from the same token positions `_add_heading_ids` visits, slice
  the source by `token.map`, and measure with `logical_word_count`. In `on` mode, inject
  each section’s indicator element immediately after its heading’s closing tag (renderer
  rule on the already-walked tokens, mirroring how heading ids are attached):

  ```html
  <h2 id="market-context">Market Context</h2>
  <div class="kpress-section-size" data-kpress-words="1240">1,240 words</div>
  ```

- **`format/render.py`** — the document-level indicator, emitted after the document
  title in `_render_document`: after the `kpress-doc-header` when that renders, else
  injected after the lone leading body `<h1>` (the `_body_h1_is_title` case), so
  fragment hosts that splice their own metadata after the title keep a stable anchor:

  ```html
  <div class="kpress-content-size" data-kpress-words="4200">
    4,200 words · 19 min read
  </div>
  ```

  Also publish the counts in the page model (`build_page_model`) under a new
  `contentSize` key.

- **`contract.py`** — register `kpress-content-size` and `kpress-section-size`
  (`PUBLIC_CSS_CLASSES` + `PUBLIC_FRAGMENT_CSS_CLASSES`), `data-kpress-words`
  (`PUBLIC_DATA_ATTRIBUTES`), and `contentSize` (`PUBLIC_PAGE_MODEL_KEYS`).

- **CSS (`static/css/document.css`, `print.css`)** — both classes follow the
  `.kpress-source-meta` idiom: `var(--kpress-font-sans)`, `var(--kpress-doc-muted)`,
  `var(--kpress-font-size-smaller)`. The section indicator sits tight under its heading
  (reduced top margin).
  Hidden in print by default (navigation aids, not document content) — revisit if print
  copies should carry counts.

- **`publish/config.py` + `publish/build.py`** —
  `FormatConfig.content_size: ContentSizeMode = "off"`, YAML key in
  `_KNOWN_FORMAT_KEYS`, `_checked_choice` loading in `load_config()`, validation with
  the closed value set, and threading into `RenderOptions` in `build_site()`.
  Per-document frontmatter opt-out `content_size: off` read via the `_meta_value`
  pattern (mirrors `thumbnail_url`), so one short page in a site can drop its
  indicators.

- **Dynamic path (`models.py`, `runtime.py`)** — `KPressRenderRequest.content_size`
  mapped into `RenderOptions` in `render_view`, like `show_doc_header`.

### Host adoption

- **Static sites:** set `content_size: on` in the format config (YAML or
  `FormatConfig`); per-page opt-out via frontmatter.
- **Fragment hosts:** set `RenderOptions.content_size` when calling `render_fragment`.
  Hosts that render their own metadata strip (byline, dates) can use `data` mode and
  present `DocumentTree.content_size` / the `contentSize` page-model entry themselves
  instead of taking the built-in markup.
- **Styling:** the two classes are pinned fragment contract surface; hosts restyle or
  hide them with ordinary CSS against the token seams, no fork needed.

### API Changes

New `RenderOptions.content_size` and `FormatConfig.content_size` fields (default
`"off"`), new `DocumentTree.content_size` data, new page-model key `contentSize`, new
contract-registered classes/attribute, new `metrics` extra.
All additive; no existing surface changes.

## Shippability Checklist

What “shippable inside KPress” requires, per the repo’s own gates:

- [ ] flexdoc release containing `logical_word_count` published; exact pin in the
  `metrics` extra; first-party table entry in `SUPPLY-CHAIN-SECURITY.md`; lock and
  clean-room wheel test green.
- [ ] Packaging-tier update in `docs/kpress-design.md` (required before a new extra
  ships) and deterministic `KPressMissingOptionalDependencyError` coverage.
- [ ] Contract registrations plus passing contract tests (`test_public_contract.py`,
  asset/fragment parity suites).
- [ ] Off-mode zero-drift proven by the existing golden scenarios rendering
  byte-identical; on-mode covered by a new golden scenario (`KPRESS_UPDATE_GOLDENS=1` to
  accept).
- [ ] Unit tests for slice/count semantics: preamble, skipped levels, no headings,
  CJK/code-heavy content, short-doc read-time suppression, frontmatter opt-out.
- [ ] Dynamic-path parity (`KPressRenderRequest`) and docs
  (`kpress-operations-and-host-integration.md`, README feature list).
- [ ] Backlog hygiene: `kpr-lrfg` tracks the work; TODO.md capability matrix updated
  when it ships.

## Open Questions

- Section-level display: words only (current design), or also per-section reading time?
  Words-only keeps the heading line quiet; the data attribute carries the count either
  way.
- Should the TOC panel show the document total in its header?
- Should `data-kpress-read-time` also be emitted as an attribute (currently only the
  formatted text carries it)?

## References

- [flexdoc](https://github.com/jlevy/flexdoc) — `docs/flexdoc-spec.md` ("Sizes and
  `TextUnit`") defines the logical-word semantics; `flexdoc/util/word_count.py` and
  `flexdoc/util/read_time.py` are the functions used here.
- [`kpress-design.md`](kpress-design.md) — dependency rules, packaging tiers, public
  contract.
- [`kpress-operations-and-host-integration.md`](kpress-operations-and-host-integration.md)
  — host integration surfaces.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
