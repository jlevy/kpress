---
type: is
id: is-01kxe7jbyecw6bjcwxk8khpwtf
title: "PR #13 review S1: reject empty normalized page content"
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01kxe7j0pb94ny5by7jq9e8tzg
created_at: 2026-07-13T17:14:33.805Z
updated_at: 2026-07-13T17:21:33.474Z
closed_at: 2026-07-13T17:21:33.474Z
close_reason: Fixed in fe13b97; local and GitHub CI are green
---
Formal review suggestion S1, tests/test_golden_readable_vs_hashed.py:72. Add a focused invariant preventing readable-vs-hashed equivalence from passing vacuously if normalization strips all page content.
