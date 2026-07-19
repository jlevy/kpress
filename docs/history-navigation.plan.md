---
title: History-Aware Section Navigation
description: Native hash history for TOC links and viewport-aware scroll restoration on Back/Forward
author: Joshua Levy (with Claude)
---
# Feature: History-Aware Section Navigation

**Date:** 2026-07-18

**Author:** Joshua Levy (with Claude)

**Status:** In Review

**Tracking:** `kpr-als7`.

## Overview

A KPress document scrolls inside one `[data-kpress-viewport]` pane, and browsers persist
and restore only the *document* scroller’s position across same-document history
traversal. Two reader-visible gaps followed:

1. **TOC links created no history at all.** The TOC behavior suppressed native
   navigation (`preventDefault` + `scrollIntoView`), so clicking an entry scrolled the
   pane but never wrote the hash: no history entry, no shareable mid-document URL, and
   Back left the page.
2. **Section links pushed history, but Back could not restore scroll.** Ordinary
   `<a href="#section">` anchors navigate natively, but on traversal the browser
   restores only the window scroller — the pane stayed where it was, so Back reverted
   the URL without moving the view.

This feature closes both gaps with a registered `history` behavior that records and
replays the pane offset through session-history entry state.
The behavior also owns plain section-link navigation: Chromium scrolls a non-root pane
instantly on fragment navigation (the pane’s CSS `scroll-behavior` is not consulted), so
the behavior pushes the entry itself and glides to the target.
Footnote references keep their popover owner, and modified or already-handled clicks
stay native.

## Goals

- TOC clicks produce real hash history entries and shareable URLs.
- Back and Forward return the reader to the pane position they navigated away from.
- Smooth section scrolling respects `prefers-reduced-motion`.
- One host-neutral behavior across standalone pages and injected fragments, registered,
  disposable, and overridable like every built-in.
- No new Python config surface; no bundler; no host wiring required.

## Non-Goals

- No SPA router or cross-page history management; scope is same-document hash navigation
  only.
- No change to the pane-scrolling architecture itself.
- The separate touch-navigation suppression in the tooltip module is tracked
  independently.

## Design

**Section navigation is owned by the history behavior; bare-`#` stays native.** Chromium
performs fragment navigation with an instant scroll when the scroller is a non-root pane
(the pane’s CSS `scroll-behavior: smooth` is not consulted), so CSS alone cannot supply
the glide. Plain clicks on non-empty section fragments are therefore owned by
`history.js`: the eligibility predicate admits an unclaimed, unmodified primary-button
click on a same-document fragment link with default anchor semantics (no `download`, no
non-`_self` `target`, not a footnote reference) whose target lives inside the pane; the
behavior then pushes the entry the browser would have pushed (no push when the
destination URL is already current, matching native re-activation), moves the sequential
focus-navigation starting point to the target (temporary `tabindex="-1"`,
`preventScroll`), and glides via `scrollIntoView` — instant under
`prefers-reduced-motion: reduce`. Everything failing the predicate stays fully native.
The `toc.js` link-click handler keeps only the drawer-close and active-highlight logic.
The “Contents” (top) link remains native bare-`#` navigation: the browser owns the URL
and the entry, and the TOC handler closes the drawer and scrolls the pane (the browser
scrolls just the *document* for an empty fragment).

**A `history` behavior (`history.js`).** Registered as `history` in `kpress.behaviors`
(bind returns a disposer), it owns viewport scroll restoration:

- A capture-phase click listener on hash anchors (bare `#` included, for the Contents
  link) stamps the pane’s `scrollTop` into the *current* entry via
  `history.replaceState` just before native navigation pushes the next entry.
  Stamping is harmless when a later handler cancels the navigation.
- The stamp respects host-owned entry state: it writes only when the state is `null` or
  a plain record without a conflicting non-numeric `kpressScroll` key.
  Any other shape (`Date`, `Map`, array, class instance, or a host-owned `kpressScroll`)
  is left exactly as stored — spreading it would change its type and discard data — and
  traversal for that entry uses the fragment fallback.
- A debounced scroll listener (`HISTORY_STAMP_DEBOUNCE_MS`) keeps the current entry’s
  stamp fresh, so Forward restores too, without hammering `replaceState`.
- On `popstate`, a finite stamped offset is replayed instantly (explicit
  `behavior: "instant"`, bypassing the pane’s CSS smooth scroll, matching the browser’s
  own restore semantics).
  Without a stamp — first forward visit into a hash entry, or an entry predating the
  behavior — it falls back to scrolling the fragment target into view; a fragmentless or
  bare-`#` entry gets document-top semantics.
  Fragment decoding never throws: a malformed percent-encoding falls back to the raw
  fragment text.
- The window’s `history.scrollRestoration` is untouched; the window never scrolls on
  these pages.

**Realm-safe viewport resolution (`viewport.js`).** `resolveKpressViewport` now checks
`nodeType` instead of `instanceof Element/Document`, so hosts may hand over a node from
another frame (or a DOM emulation) without silently falling back to the document
scroller.

**Wiring.** `js/history.js` ships as an entry point whenever the page has in-document
hash navigation (a TOC or same-document links); it is pinned in `PUBLIC_BEHAVIORS`,
`PUBLIC_JS_EXPORTS` (`initKpressHistory`), `DEFAULT_JS_ASSETS`, and the package
dependency map (`runtime.js`, `viewport.js`).

## Verification

- Browserless Vitest: stamp-on-click (state preserved additively), non-hash and bare-`#`
  anchors ignored, popstate restore, fragment fallback, debounced re-stamp, disposer
  teardown, and registry binding.
  The TOC suite asserts the drawer still closes on link clicks; section-link navigation
  is owned by the `history` behavior (pushState + smooth in-pane scroll).
- Python goldens: the new script entry on TOC/tooltip pages and the changed asset hashes
  are reviewed and accepted.
- Real-browser QA (host-side): section-link click → Back restores the pane position; TOC
  click updates the URL; Forward returns; reduced-motion disables the glide.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
