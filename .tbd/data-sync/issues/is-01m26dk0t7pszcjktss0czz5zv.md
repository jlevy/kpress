---
type: is
id: is-01m26dk0t7pszcjktss0czz5zv
title: Add scrollspy fallback and reconcile document styling
kind: task
status: closed
priority: 1
version: 4
labels:
  - toc
  - typography
dependencies: []
created_at: 2026-09-10T19:44:20.294Z
updated_at: 2026-09-10T20:37:35.604Z
closed_at: 2026-09-10T20:37:35.580Z
close_reason: "Implemented and verified in KPress commit 40ccb42; upstream PR #72 is open and all six exact-head CI checks pass, including Python 3.12/3.13/3.14, browser, lint, and distribution."
resolution: null
duplicate_of: null
---
Add a deterministic TOC scrollspy path for environments without IntersectionObserver, then port only generic document styling improvements identified in the Metabrowser integration. Verify the already-upstream collapsible TOC/expand control and Planetaire mono work instead of duplicating them.

## Notes

Implemented host-rewritten same-document TOC link recognition, malformed-link handling, and an IntersectionObserver-free scrollspy with passive frame coalescing, logarithmic heading lookup, resize handling, and disposal. Reconciled generic TOC wrapping/RTL insets, compact inline code, and blockquote treatment; retained KPress's border. Added browserless JS coverage for fallback/native paths, malformed/cross-document links, coalescing, performance, and cleanup; added CSS contract and regenerated reviewed asset goldens; updated design and 0.3.6 notes. Pinned v0.3.5 already contains collapseDepth, expand/collapse chevron control, and the mono size ramp; current main additionally ships Planetaire Mono Text, so none were duplicated. Local make verify passed: 754 Python passed/24 optional-engine skips, 251 JS passed, audits clean, distribution checks passed.
