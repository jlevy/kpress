---
type: is
id: is-01kyh1nrge3scekb0ggx5n9261
title: Replace table header slugs with explicit column metadata
kind: task
status: closed
priority: 2
version: 4
spec_path: docs/publishing.md
labels:
  - tables
  - identifiers
  - breaking-alpha
dependencies:
  - type: blocks
    target: is-01kyh1p3vz1r6qaqc9693pte3d
parent_id: is-01kyh1kdvsza3f2qy8cfhhktc5
created_at: 2026-07-27T05:44:58.637Z
updated_at: 2026-07-27T06:33:51.799Z
closed_at: 2026-07-27T06:33:51.799Z
close_reason: "Implemented as specified: exact pinned fixtures/provenance, dependency-free stateful slugger, single-source heading consumers, ordinal footnote ids, and literal/indexed table metadata. Focused regressions and the complete make verify gate pass."
---
Keep the public table-column hook independent of navigation slugs. Replace the lossy ASCII header slug with data-col equal to the whitespace-normalized visible header label, HTML-escaped while preserving case, punctuation, and Unicode, and add a 1-based data-col-index to header-backed cells for unambiguous positional selection. Duplicate or empty header labels may share data-col because data-col-index is the unique key. Update the public data-attribute contract, design documentation, numeric-column processing, raw and GFM table tests, and downstream examples. Remove _slugify_column; do not call the GitHub heading slugger and do not emit the former kebab value in a compatibility attribute.

## Notes

IMPLEMENTED LOCALLY 2026-07-27: data-col now carries whitespace-normalized visible header labels (including Unicode/punctuation/duplicates/empty), data-col-index provides a 1-based positional identity, and numeric-column rewrites preserve both. Public contract and focused tests updated; docs/goldens pending.
