---
type: is
id: is-01kxe7javkh6abp2f9z5ca73xr
title: "PR #13 review R1: remove duplicated normalization logic"
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01kxe7j0pb94ny5by7jq9e8tzg
created_at: 2026-07-13T17:14:32.690Z
updated_at: 2026-07-13T17:21:33.452Z
closed_at: 2026-07-13T17:21:33.451Z
close_reason: Fixed in fe13b97; local and GitHub CI are green
---
Formal review R1 (Low), tests/test_golden_readable_vs_hashed.py:29. Choose and document whether to reuse equivalence_helpers.normalize_document_surface or retain the stricter local normalizer; prevent drift without hiding meaningful readable-vs-hashed differences.
