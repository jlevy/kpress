---
type: is
id: is-01m2103wzwqjgtz4ed3qdnthah
title: Preserve print emulation across browser font probes
kind: bug
status: closed
priority: 2
version: 5
labels: []
dependencies: []
created_at: 2026-09-08T17:12:41.208Z
updated_at: 2026-09-08T17:54:16.021Z
closed_at: 2026-09-08T17:54:16.019Z
close_reason: "Implemented and independently reviewed in KPress PR #63 (adbe9a3); required local gates and all six hosted CI jobs pass. PR intentionally left open for review."
resolution: null
duplicate_of: null
---
Upstream assessment of jlevy/squares#131 found that list-marker and sans-math browser probes still detach CDP between samples. Chromium resets emulated print media on detach, so later marker samples and sans print retries can measure screen fonts. Keep sessions attached through each measurement block, assert the observed media, and check marker shape and visibility in print as well as screen. The source CSS and 650 font assets already exist upstream; no runtime port is needed.

## Notes

Completed in https://github.com/jlevy/kpress/pull/63 at adbe9a39a21fb03e1143742d01f5d8f08947005e; PR remains open and unmerged.

All six GitHub CI jobs passed (browser, distribution, lint, and Python 3.12/3.13/3.14 tests), confirmed by the completed gh pr checks --watch final summary. Local make lint-check/audit pass; make test passes 724 Python + 228 JS tests; make test-browser passes 22 tests with no skips. Independent final code review found no actionable issues.

New media assertions reproduce both baseline CDP defects. Print-only tall, absent, and zero-area marker controls are rejected, as is a nested print marker reset to unprotected currentColor under forced colors. Removing only the dedicated nested print forced-colors block is benign on the tested Chromium because the shared rule still protects it; that deletion is not claimed as a reproduced defect. Missing Chromium fails in required mode.

All changes are isolated upstream test/Makefile changes. Squares owns its centering override and font-pruning correction; KPress already includes all sans math slots and the portable font-advance helper.
