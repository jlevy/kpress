---
type: is
id: is-01m1z5brtdfe25898yb3mafb03
title: "Print sans follow-ups from the #54 verification: doc count, a stale contract string, migration note, the slow-asset PDF test"
kind: chore
status: open
priority: 3
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - print
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T00:05:53.099Z
updated_at: 2026-09-08T00:05:53.099Z
---
Four Low items from the PR #54 verification review (comment 5577017556), none blocking, after the merge to main at aee6df7: the operations doc says Four consequences over five bullets; contract.py line ~377 still says Source Sans 3 where the print family is now KPress Print Sans; the rename is documented as provenance but not as a migration for hosts that instanced their own faces under the old family name; and the slow-asset PDF test lacks the /Type3 assertion its sibling carries. Also noted: test_each_request_lands_on_its_instance was added alongside the self-referential landing test rather than replacing it.
