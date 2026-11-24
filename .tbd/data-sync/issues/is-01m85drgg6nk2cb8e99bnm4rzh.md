---
type: is
id: is-01m85drgg6nk2cb8e99bnm4rzh
title: "PR #82 I1: task-box styling depends on classes a sanitizing host strips"
kind: bug
status: closed
priority: 2
version: 3
spec_path: TODO.md
delegate: claude-code@spud10.local
labels: []
dependencies: []
parent_id: is-01m8577cwgvk6zxwrhatkd8tea
hold: null
hold_until: null
created_at: 2026-11-24T00:02:16.708Z
updated_at: 2026-11-24T02:10:26.443Z
started_at: 2026-11-24T00:02:33.283Z
closed_at: 2026-11-24T02:10:26.438Z
close_reason: "Fixed in fddc5a2 on PR #82: components.css draws the box and drops the bullet by structure inside .kpress-prose; tests/test_playwright_task_box.py compares a class-stripped list with the classed one. CI 45306732433 green on 0c0f857."
resolution: null
duplicate_of: null
---
Found integrating KPress's box into Metabrowser, whose inert hardener keeps only <input type=checkbox disabled [checked]> and no classes. components.css styles the box and hides the bullet only under li.kpress-task / .kpress-task, so in such a host the box draws as a native disabled checkbox and the bullet stays. Key the styles on structure too (li > input[type=checkbox]:first-child, li > p:first-child > input[type=checkbox]:first-child, li:has(...) for the bullet); keep the class selectors and the classed result unchanged; Playwright check that a class-free box list renders as the classed one.
