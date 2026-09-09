---
type: is
id: is-01m21xejc3j2s1a3309ndenmqt
title: Repair PR 68 browser CI dependency and 410 metric assertion
kind: bug
status: closed
priority: 1
version: 4
labels:
  - ci
  - typography
dependencies: []
created_at: 2026-09-09T01:45:19.478Z
updated_at: 2026-09-09T02:34:57.047Z
closed_at: 2026-09-09T02:34:57.047Z
close_reason: "Implemented and validated in KPress PR #68 at 515f4a08aaf529f922b4380db7f7b7913b01abf5. Final CI run 34302772413 passes lint, Python 3.12-3.14, browser, and distribution; Squares PR #135 pins this exact filed-PR head."
resolution: null
duplicate_of: null
---
PR 68 hosted CI exposed two release blockers: the dedicated browser job selected the pdf extra without the optimize extra required by Brotli during browser-test collection, and the generated 410 sans instance advances the digit 1 at 0.498em while a stale assertion expected 0.497em at the tolerance boundary. Keep CI dependency selection consistent across sync, browser installation, and test execution; update the assertion to the generated metric and verify the focused browser case.

## Notes

Run 34300505621 cleared dependency collection and all three Python jobs; browser reached 56/57. The remaining failure was the existing reload bead kpr-n1j6: on Linux WebKit, the rapid pane+fragment reload dispatched pageshow before the deferred history module registered, leaving state.kpressScroll=2800 but pane scrollTop=0. The minimal repair schedules the existing guarded restore once when a pane behavior initializes after document.readyState is complete; a real later pageshow cancels/replaces it, document hosts are unchanged, and disposal still cancels the frame. Astra reviewed this mechanism and found it reasonable. Local evidence: 27 history unit tests pass; exact required WebKit pane-fragment case passes.
