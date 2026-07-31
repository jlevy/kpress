---
type: is
id: is-01kyv0jn7ammm2v96cy369p69b
title: Base-relative container bands via em query conditions
kind: feature
status: open
priority: 3
version: 2
spec_path: docs/project/specs/active/plan-2026-07-31-declarative-embedding.md
labels: []
dependencies: []
created_at: 2026-07-31T02:38:12.713Z
updated_at: 2026-07-31T03:14:42.825Z
---
Tracked follow-up per PR #40 review finding 6: band thresholds (48/64/75rem) and --kpress-measure stay root-relative after #37, so chars-per-line and the heading step-up trigger vary with reader root preference for px-pinned hosts. Font-relative units in container query conditions resolve against the query container, so setting the container font-size to the base and using em conditions would make bands base-relative. Blast radius: test_asset_contract pinned band strings, grid tracks, tooltip caps + tooltips.js px mirrors.
