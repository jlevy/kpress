---
type: is
id: is-01kyh1mgqdqtezed0cda8qm03h
title: "Add red parity and rendered-anchor tests for GitHub #33"
kind: task
status: open
priority: 1
version: 2
spec_path: docs/publishing.md
labels:
  - anchors
  - tests
  - tdd
dependencies:
  - type: blocks
    target: is-01kyh1mtcjvq2v0s4fs62y1jsp
parent_id: is-01kyh1kdvsza3f2qy8cfhhktc5
created_at: 2026-07-27T05:44:17.899Z
updated_at: 2026-07-27T05:45:29.280Z
---
Start with tests that fail against the current implementation. Run the full upstream fixture sequence through one stateful slugger and add focused regressions for Figma's Share Price -> figmas-share-price, S&P 500 -> sp-500, Café Notes -> café-notes, repeated Summary -> summary and summary-1, pre-existing suffix collisions, emoji, Cyrillic plus Han, leading and trailing spaces, punctuation-only empty output, and inline raw HTML whose visible text is the slug input. Add an end-to-end Markdown assertion that heading tag ids, Heading.id, TocEntry.href, rendered TOC links, the JSON page model, encoded and unencoded internal-link diagnostics, and generated fragment links all carry the same target. Prove the tests are red for the specific old behaviors before implementation.
