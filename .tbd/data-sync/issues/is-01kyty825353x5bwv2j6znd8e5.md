---
type: is
id: is-01kyty825353x5bwv2j6znd8e5
title: "Hygiene lint: forbid rem font sizes with allowlist"
kind: task
status: closed
priority: 2
version: 2
spec_path: docs/declarative-embedding.plan.md
labels: []
dependencies: []
parent_id: is-01kytxz9k3cjy0drxwt3xsq9d8
created_at: 2026-07-31T01:57:28.355Z
updated_at: 2026-07-31T02:16:21.508Z
closed_at: 2026-07-31T02:16:21.507Z
close_reason: rem font-size lint added to public_hygiene with allowlist + unit and shipped-tree tests; lint gate green.
---
Extend devtools/public_hygiene.py (run by make lint-check): fail any font-size declaration or size-token value containing rem in packaged kpress CSS, with an explicit allowlist for the documented root-relative remainder (container/media query conditions, --kpress-measure, grid tracks, tooltip width caps, page margins, radius-lg). Add matching test in tests/test_public_hygiene.py.
