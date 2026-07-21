---
type: is
id: is-01ky13bkphhm54fwrr3mcycrap
title: "PR #31 R2: keep doc-actions fixed when content card is off"
kind: bug
status: closed
priority: 1
version: 4
labels: []
dependencies: []
parent_id: is-01ky12h9ncf417yfvz67jzps92
created_at: 2026-07-21T01:06:32.272Z
updated_at: 2026-07-21T01:14:30.557Z
closed_at: 2026-07-21T01:14:30.556Z
close_reason: "Fixed and regression-tested in 6ac0b89; merged through PR #31."
---
Review finding R2: doc-actions relocates into .kpress-long-text even when data-kpress-card=off because the class exists in both modes. Gate relocation on data-kpress-card=on and add card-on/card-off lifecycle coverage.

## Notes

Resolved in 6ac0b89. Relocation now requires data-kpress-card=on; Vitest covers both on/off states.
