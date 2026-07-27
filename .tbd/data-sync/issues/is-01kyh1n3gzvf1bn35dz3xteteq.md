---
type: is
id: is-01kyh1n3gzvf1bn35dz3xteteq
title: Migrate heading text extraction and every anchor consumer
kind: task
status: closed
priority: 1
version: 4
spec_path: docs/publishing.md
labels:
  - anchors
  - markdown
  - integration
dependencies:
  - type: blocks
    target: is-01kyh1p3vz1r6qaqc9693pte3d
parent_id: is-01kyh1kdvsza3f2qy8cfhhktc5
created_at: 2026-07-27T05:44:37.149Z
updated_at: 2026-07-27T06:33:51.787Z
closed_at: 2026-07-27T06:33:51.787Z
close_reason: "Implemented as specified: exact pinned fixtures/provenance, dependency-free stateful slugger, single-source heading consumers, ordinal footnote ids, and literal/indexed table metadata. Focused regressions and the complete make verify gate pass."
---
Feed the slugger the visible plain heading text required by the upstream contract. Inline emphasis, links, code, images, entities, hard or soft breaks, and raw inline HTML must contribute the same human-visible text GitHub receives; raw tag names must not leak into ids. Apply the one generated id to the rendered heading token and DocumentTree heading, then derive TOC entries and the page model from that same value. Audit history.js, toc.js, tooltips.js, broken-anchor diagnostics, sanitization, static publishing, and readable-versus-hashed output for Unicode and percent-encoded fragments. Delete obsolete paths. Do not emit legacy ids, alias anchors, redirects, data attributes with the old id, or dual TOC targets.

## Notes

IMPLEMENTED LOCALLY 2026-07-27: one GithubSlugger per parse, visible inline text excludes raw tag names while preserving entities/spaces, and one id feeds heading HTML/tree/TOC. Consumer/browser audit and comprehensive scenario remain in progress.
