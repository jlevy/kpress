---
type: is
id: is-01m1z1tyn75d11my9wfb9j22db
title: "Font-chooser reload path: honour a wrapper-baked system mode and a failed storage write"
kind: bug
status: open
priority: 3
version: 1
labels:
  - typography
dependencies: []
created_at: 2026-09-07T23:04:16.280Z
updated_at: 2026-09-07T23:04:16.280Z
---
From the PR #53 verification review (comment 5576465274), after the merge to main at 0c9e251. K53-V1: fontSetSwitchNeedsReload in settings-widget.js reads only the html element, so a wrapper baked with RenderOptions.font_mode=system reloads for nothing (0.4996em, no composite, before and after); read the resolved mode the same way katex-init does (closest() from the wrapper). K53-V2: storage.set swallows a failed write while the reload is taken anyway; with Storage.prototype.setItem throwing, choosing System fonts reloads back into custom (0.5333em, composite on) and the choice is silently dropped; only reload when the write succeeded, otherwise switch in place and say so. Both need a vitest case and, for V1, a Playwright case with a wrapper-stamped mode.
