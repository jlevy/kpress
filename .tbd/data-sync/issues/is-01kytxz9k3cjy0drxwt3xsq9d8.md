---
type: is
id: is-01kytxz9k3cjy0drxwt3xsq9d8
title: "Root-independent sizing via --kpress-font-size-base (issue #37)"
kind: feature
status: open
priority: 1
version: 1
spec_path: docs/declarative-embedding.plan.md
labels: []
dependencies: []
parent_id: is-01kytxyzcd4wk87syn1t3naxhg
created_at: 2026-07-31T01:52:41.058Z
updated_at: 2026-07-31T01:52:41.058Z
---
Phase 1 of the declarative-embedding spec: add --kpress-font-size-base (reading --kpress-host-font-size-base, default 1rem) on the four token scopes; convert every font-size token/literal and the bullet geometry to calc(base * R); route print through the base (fixes in-repo print ratio drift); contract + hygiene lint + two-root Playwright test + asset-contract strings + goldens + docs. GitHub: https://github.com/jlevy/kpress/issues/37
