---
type: is
id: is-01kyty8qj1bwn65xtzahcbv0rf
title: "Hygiene lint: forbid data-kpress-theme in CSS"
kind: task
status: open
priority: 2
version: 1
spec_path: docs/declarative-embedding.plan.md
labels: []
dependencies: []
parent_id: is-01kytxza2a4r789k649dzrantj
created_at: 2026-07-31T01:57:50.273Z
updated_at: 2026-07-31T01:57:50.273Z
---
Extend the hygiene lint so no packaged stylesheet may reference data-kpress-theme (the mode attribute) — CSS keys only on data-kpress-resolved-theme. Add matching test in tests/test_public_hygiene.py.
