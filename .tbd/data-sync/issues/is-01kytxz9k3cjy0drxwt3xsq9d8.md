---
type: is
id: is-01kytxz9k3cjy0drxwt3xsq9d8
title: "Root-independent sizing via --kpress-font-size-base (issue #37)"
kind: feature
status: closed
priority: 1
version: 11
spec_path: docs/done/declarative-embedding.plan.md
labels: []
dependencies: []
parent_id: is-01kytxyzcd4wk87syn1t3naxhg
child_order_hints:
  - is-01kyty6newbj90y6j0ab8y01vn
  - is-01kyty81qvckvd016d7xbk24na
  - is-01kyty825353x5bwv2j6znd8e5
  - is-01kyty82gxnmdx4dz28hassyba
  - is-01kyv0jmhxzvnv00kgpkkh7tz4
created_at: 2026-07-31T01:52:41.058Z
updated_at: 2026-07-31T23:28:40.027Z
closed_at: 2026-07-31T23:28:40.026Z
close_reason: "Issue #37 root-independent sizing phase is implemented, documented, contract-pinned, and validated in the v0.3.0 release candidate."
---
Phase 1 of the declarative-embedding spec: add --kpress-font-size-base (reading --kpress-host-font-size-base, default 1rem) on the four token scopes; convert every font-size token/literal and the bullet geometry to calc(base * R); route print through the base (fixes in-repo print ratio drift); contract + hygiene lint + two-root Playwright test + asset-contract strings + goldens + docs. GitHub: https://github.com/jlevy/kpress/issues/37
