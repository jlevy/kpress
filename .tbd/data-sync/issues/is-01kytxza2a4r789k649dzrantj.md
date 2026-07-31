---
type: is
id: is-01kytxza2a4r789k649dzrantj
title: "Single-scope symmetric theming, theme-agnostic fragment SSR (issue #38)"
kind: feature
status: closed
priority: 1
version: 12
spec_path: docs/done/declarative-embedding.plan.md
labels: []
dependencies: []
parent_id: is-01kytxyzcd4wk87syn1t3naxhg
child_order_hints:
  - is-01kyty8pj56bv51ej8mjr3c2wn
  - is-01kyty8pwqgtgwprxy3p2p2hnc
  - is-01kyty8q78gkqp1y8e7pz8rcn4
  - is-01kyty8qj1bwn65xtzahcbv0rf
  - is-01kyty8qwmms8t029r8xs6ya1k
  - is-01kyx2e4pq85s0fm0vek4ptvye
created_at: 2026-07-31T01:52:41.545Z
updated_at: 2026-07-31T23:28:40.261Z
closed_at: 2026-07-31T23:28:40.260Z
close_reason: "Issue #38 theming phase and its #42 host-safety follow-up are implemented, documented, contract-pinned, and validated in the v0.3.0 release candidate."
---
Phase 2 of the declarative-embedding spec: CSS keys only data-kpress-resolved-theme with two symmetric selector forms (ancestor :where() + element; element wins); color-scheme co-located with palette blocks; fold theme-light/theme-dark.css into style-tokens.css; stop baking theme/palette attrs on the article so fragment renders are byte-identical across themes; contract/goldens/tests + embedder-contract docs. GitHub: https://github.com/jlevy/kpress/issues/38
