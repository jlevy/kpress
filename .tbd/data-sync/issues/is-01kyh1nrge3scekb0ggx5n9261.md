---
type: is
id: is-01kyh1nrge3scekb0ggx5n9261
title: Replace table header slugs with explicit column metadata
kind: task
status: open
priority: 2
version: 2
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
updated_at: 2026-07-27T05:45:31.288Z
---
Keep the public table-column hook independent of navigation slugs. Replace the lossy ASCII header slug with data-col equal to the whitespace-normalized visible header label, HTML-escaped while preserving case, punctuation, and Unicode, and add a 1-based data-col-index to header-backed cells for unambiguous positional selection. Duplicate or empty header labels may share data-col because data-col-index is the unique key. Update the public data-attribute contract, design documentation, numeric-column processing, raw and GFM table tests, and downstream examples. Remove _slugify_column; do not call the GitHub heading slugger and do not emit the former kebab value in a compatibility attribute.
