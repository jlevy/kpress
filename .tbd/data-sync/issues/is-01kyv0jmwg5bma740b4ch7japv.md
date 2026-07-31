---
type: is
id: is-01kyv0jmwg5bma740b4ch7japv
title: "PR #40 review F1/F4/F6: spec record, migration table, print-path guidance"
kind: task
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-07-31-declarative-embedding.md
labels: []
dependencies: []
parent_id: is-01kytxyzcd4wk87syn1t3naxhg
created_at: 2026-07-31T02:38:12.368Z
updated_at: 2026-07-31T03:14:42.529Z
closed_at: 2026-07-31T02:45:40.677Z
close_reason: "Theming embedder contract documented across design/host/skill docs; 0.3.0 migration table added; spec record corrected per PR #40 review; cache-key fix landed separately (cb752ca)."
---
Reframe the metabrowser baseline: the em bridge lives on metabrowser#16 (type-scale branch, pinned kpress==0.2.2 where bullet was 0.8rem/top 0.25rem) — version skew, not issue errors; update References + Rollout (migration = collapse the whole bridge). Add release-notes migration table rows: wide-band step-up reappears in embedded panes; baked-attr downstream assertions break. Document the print divergence between hook path and redeclare path. Document wrapper-scope portal caveat (stamp :root too). Add lint test case proving rem fallback literals are caught. Verify fragment render-cache key excludes theme/palette.
