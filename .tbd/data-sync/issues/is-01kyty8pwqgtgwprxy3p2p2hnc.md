---
type: is
id: is-01kyty8pwqgtgwprxy3p2p2hnc
title: Theme-agnostic fragment SSR
kind: task
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-07-31-declarative-embedding.md
labels: []
dependencies:
  - type: blocks
    target: is-01kyty8q78gkqp1y8e7pz8rcn4
  - type: blocks
    target: is-01kyty8qwmms8t029r8xs6ya1k
parent_id: is-01kytxza2a4r789k649dzrantj
created_at: 2026-07-31T01:57:49.591Z
updated_at: 2026-07-31T03:14:40.212Z
closed_at: 2026-07-31T02:32:19.036Z
close_reason: Article theme/palette attrs removed from fragment SSR with byte-identical test; page shell unchanged; goldens regenerated; full suite + lint green.
---
render.py stops baking data-kpress-theme, data-kpress-resolved-theme, and data-kpress-palette on the article element; the page shell keeps stamping <html> from the template + pre-paint bootstrap (unchanged). RenderOptions fields keep their meaning for page shell/bootstrap/widget/asset selection. Update test_document_contract.py expectations; add pytest asserting light-vs-dark and neutral-vs-warm fragment renders are byte-identical; regenerate goldens.
