---
type: is
id: is-01kyh1p3vz1r6qaqc9693pte3d
title: Validate the anchor migration across browsers, goldens, and docs
kind: task
status: open
priority: 1
version: 2
spec_path: docs/publishing.md
labels:
  - anchors
  - browser
  - golden
  - docs
dependencies:
  - type: blocks
    target: is-01kyh1kdvsza3f2qy8cfhhktc5
parent_id: is-01kyh1kdvsza3f2qy8cfhhktc5
created_at: 2026-07-27T05:45:10.269Z
updated_at: 2026-07-27T05:45:31.559Z
---
Finish the feature as a reviewed behavioral migration. Add a real-browser scenario that clicks a Unicode TOC link, resolves the heading with getElementById, updates and restores the encoded location hash through KPress history handling, drives TOC scroll-spy, and resolves an internal-link tooltip; include duplicate headings and an authored percent-encoded fragment. Regenerate the affected HTML/tree goldens and inspect the full diffs for intentional ids only. Update kpress-design.md, validation guidance, examples, and release-note inputs to define the pinned GitHub contract, ordinal footnotes, and literal column metadata. Call out that old external deep links and host link indexes must be regenerated. Run targeted Python, DOM, and Playwright suites plus make lint-check and make test with no unexpected skips; leave the complete make verify artifact gate to the release-candidate bead.
