---
type: is
id: is-01kytxza2a4r789k649dzrantj
title: "Single-scope symmetric theming, theme-agnostic fragment SSR (issue #38)"
kind: feature
status: open
priority: 1
version: 1
spec_path: docs/declarative-embedding.plan.md
labels: []
dependencies: []
parent_id: is-01kytxyzcd4wk87syn1t3naxhg
created_at: 2026-07-31T01:52:41.545Z
updated_at: 2026-07-31T01:52:41.545Z
---
Phase 2 of the declarative-embedding spec: CSS keys only data-kpress-resolved-theme with two symmetric selector forms (ancestor :where() + element; element wins); color-scheme co-located with palette blocks; fold theme-light/theme-dark.css into style-tokens.css; stop baking theme/palette attrs on the article so fragment renders are byte-identical across themes; contract/goldens/tests + embedder-contract docs. GitHub: https://github.com/jlevy/kpress/issues/38
