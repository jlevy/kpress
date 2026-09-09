---
type: is
id: is-01m222ps4eaf769rnsx9maadn5
title: Add close control and touch dismissal to footnote tooltips
kind: feature
status: closed
priority: 1
version: 2
labels: []
dependencies: []
created_at: 2026-09-09T03:17:11.425Z
updated_at: 2026-09-09T07:09:12.584Z
closed_at: 2026-09-09T07:09:12.574Z
close_reason: "Merged in KPress PRs #70 and #71 with touch, keyboard, Escape, focus, and timer coverage."
resolution: null
duplicate_of: null
---
Footnote and related KPress tooltips need a visible accessible × close control. On touch/mobile, tapping outside or an appropriate repeat tap must dismiss the open tooltip reliably without breaking activation of links inside the tooltip, keyboard Escape behavior, focus restoration, or desktop hover/focus behavior. Audit the existing interaction model, implement the smallest shared behavior, and add browser/DOM coverage for touch and accessibility.
