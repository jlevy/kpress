---
type: is
id: is-01kxvrx5czn927pn4fyf6a27my
title: Harden test_playwright_history against traversal/stamp timing races
kind: task
status: open
priority: 3
version: 1
labels: []
dependencies: []
created_at: 2026-07-18T23:27:40.958Z
updated_at: 2026-07-18T23:27:40.958Z
---
test_hash_history_and_viewport_restoration_in_real_browser failed once in a full-suite run immediately after the fix/toc-toggle-clearance rebase onto main (post-PR-#24 history rework), then passed in 4 consecutive re-runs (isolated and full-suite); the failure detail was not captured.

Hypothesized mechanism: the test's settle-detection (two equal scrollTop polls) can complete before/after the 200ms debounced history.state stamp lands, so scripted go_back/go_forward can race the stamp on a cold browser start. Harden by making the waits deterministic — e.g. wait for history.state.kpressScroll to be present (or explicitly absent) before traversing, instead of relying only on scroll settle — and capture failure artifacts (page URL, scrollTop, history.state) on assertion failure.
