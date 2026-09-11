---
type: is
id: is-01m271dbhv7qss74amrvg1wetc
title: Restore stamped pane offset after WebKit delayed fragment landing
kind: bug
status: closed
priority: 1
version: 3
labels:
  - reader
  - browser-qa
dependencies: []
created_at: 2026-09-11T01:30:46.201Z
updated_at: 2026-09-11T01:55:10.564Z
closed_at: 2026-09-11T01:55:10.563Z
close_reason: "PR #72 now restores stamped pane state on a bounded confirmation frame, aborts on intervening history-state replacement, and passes focused browserless, local WebKit, full verification, pre-push, and Linux browser CI."
resolution: null
duplicate_of: null
---
KPress main intermittently fails the real-browser pane-fragment WebKit reload case: history.state retains kpressScroll, but WebKit can apply the fragment landing after the behavior's single requestAnimationFrame restoration. Make pageshow restoration converge across the next paint without persistent scroll fighting, add a browserless timing regression, retain the real-browser assertion, and validate PR #72 across the full gate.
