---
type: is
id: is-01kyty8qj1bwn65xtzahcbv0rf
title: "Hygiene lint: forbid data-kpress-theme in CSS"
kind: task
status: closed
priority: 2
version: 3
spec_path: docs/project/specs/active/plan-2026-07-31-declarative-embedding.md
labels: []
dependencies: []
parent_id: is-01kytxza2a4r789k649dzrantj
created_at: 2026-07-31T01:57:50.273Z
updated_at: 2026-07-31T03:14:41.101Z
closed_at: 2026-07-31T02:35:26.391Z
close_reason: mode-keyed-css hygiene rule + tests added; shipped tree clean; lint gate green.
---
Extend the hygiene lint so no packaged stylesheet may reference data-kpress-theme (the mode attribute) — CSS keys only on data-kpress-resolved-theme. Add matching test in tests/test_public_hygiene.py.
