---
type: is
id: is-01m858sp4pnhqx3edg05najh5d
title: "PR #82 S2: sanitized <button> can submit or reset a host form"
kind: bug
status: closed
priority: 1
version: 3
spec_path: TODO.md
delegate: claude-code@spud10.local
labels: []
dependencies: []
parent_id: is-01m8577cwgvk6zxwrhatkd8tea
hold: null
hold_until: null
created_at: 2026-11-23T22:35:32.373Z
updated_at: 2026-11-23T23:42:40.893Z
started_at: 2026-11-23T22:36:03.733Z
closed_at: 2026-11-23T23:42:40.888Z
close_reason: "fixed in 342e2e8: form dropped from the global allow-list and forbidden as an extra attribute; every button is type=button via set values; verified in headless Chromium 148 (submit/reset before, neither after); tests test_a_button_can_never_submit_or_reset_a_host_form, test_no_element_keeps_form"
resolution: null
duplicate_of: null
---
Security review of PR #82, should-fix, predates the PR. form is in _GLOBAL_ATTRIBUTES (sanitize.py:93) and a <button> keeps any type, so <button form="host-form">, a bare <button> inside a host <form>, and <button type="reset" form=...> submit or reset a host form. KPress emits no form= and its only body button is type="button" (markdown.py:783-794). Fix: drop form everywhere, force type="button" on <button>.
