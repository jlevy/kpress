---
type: is
id: is-01kyx9c0p8axxkdnwhsqtx9n2v
title: "PR #43 review S4: minimize README merge-to-tag window"
kind: bug
status: closed
priority: 3
version: 3
labels:
  - release-0.3.0
dependencies: []
parent_id: is-01kyx8cq65jqj03gde1081a1ym
created_at: 2026-07-31T23:50:21.127Z
updated_at: 2026-08-01T00:08:46.469Z
closed_at: 2026-08-01T00:08:46.468Z
close_reason: "Rebutted: README 0.3.0 install text intentionally staged the release candidate; tag and publication follow immediately after merge."
---
Suggestion S4 notes README/installation advertise kpress==0.3.0 before tag publication. Explicitly disposition as no code change because this is the intended release-candidate branch and tagging remains a separate immediate post-merge action; do not publish or alter the release target.
