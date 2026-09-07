---
type: is
id: is-01m1z4h8rj102y46mjzan6pxcv
title: Check the reserved-name position of the vendored variable sans subsets
kind: task
status: open
priority: 3
version: 1
spec_path: docs/math-text-face.plan.md
labels: []
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-07T23:51:24.690Z
updated_at: 2026-09-07T23:51:24.690Z
---
Raised while addressing PR #54's second review (comment 5576343371), which found that the generated static print instances presented the OFL reserved name 'Source'. That is fixed: the derived family is now KPress Print Sans. The same question is open one level up and predates PR #54. src/kpress/format/static/fonts/source-sans-3-latin-wght-{normal,italic}.woff2 are Latin subsets of Source Sans 3, not the upstream files: their name tables still read 'Source Sans 3' (name ID 1 'Source Sans 3 ExtraLight'), and OFL 1.1 condition 3 treats a subset as a Modified Version. Establish where the subsets came from (Google Fonts' own build, fontsource, or a local subsetting run), whether that origin carries permission, and either record the provenance in NOTICE.md or rename as the static set was renamed. Same question applies to the PT Serif subsets under the same directory.
