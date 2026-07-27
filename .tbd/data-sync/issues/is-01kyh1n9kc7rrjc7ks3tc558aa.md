---
type: is
id: is-01kyh1n9kc7rrjc7ks3tc558aa
title: Replace footnote label slugs with collision-free ordinal ids
kind: task
status: open
priority: 2
version: 2
spec_path: docs/publishing.md
labels:
  - footnotes
  - identifiers
  - breaking-alpha
dependencies:
  - type: blocks
    target: is-01kyh1p3vz1r6qaqc9693pte3d
parent_id: is-01kyh1kdvsza3f2qy8cfhhktc5
created_at: 2026-07-27T05:44:43.371Z
updated_at: 2026-07-27T05:45:30.947Z
---
Decouple footnote identity from heading slug semantics. Use the parser's document-order footnote ordinal for DOM and model identity: fn-1 for the definition, fnref-1 for its first reference, and fnref-1-2 and later suffixes for repeated references. data-kpress-footnote-ref must use the same ordinal identity; authored labels remain parser input and diagnostic context only. Add coverage for Unicode labels, punctuation-only labels, distinct labels that previously collapsed to the same ASCII slug, repeated references, backrefs, tooltips, sanitization, and broken-anchor audits. Remove _footnote_ident's use of _SLUG_RE and provide no legacy label-based ids or aliases.
