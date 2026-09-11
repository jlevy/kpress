---
type: is
id: is-01m21ndmg1kh1zjxpw3gsp8cn1
title: Restore standalone reader scroll on reload without changing pane semantics
kind: bug
status: closed
priority: 2
version: 6
assignee: Codex font_pr_history
labels: []
dependencies: []
created_at: 2026-09-08T23:25:00.284Z
updated_at: 2026-09-09T02:34:57.020Z
closed_at: 2026-09-09T02:34:57.020Z
close_reason: "Implemented and validated in KPress PR #68 at 515f4a08aaf529f922b4380db7f7b7913b01abf5. Final CI run 34302772413 passes lint, Python 3.12-3.14, browser, and distribution; Squares PR #135 pins this exact filed-PR head."
resolution: null
duplicate_of: null
---
The standalone KPress page scrolls in its marked inner pane. history.js restores popstate but has no reload/pageshow restoration; verify with a real location.reload() regression, then preserve the existing history entry and immediate scroll position across reload and Back/Forward. Keep document-scrolling hosts native and retain host-owned history.state. Reproduction and fix are isolated in codex/reader-reload-baseline-contract.

## Notes

Hosted run 34300505621 added the missing cross-host evidence: Linux WebKit can dispatch pageshow before a deferred history module registers on a rapid pane+fragment reload. The entry retained kpressScroll=2800 but the pane stayed at zero. The final source schedules the same numeric-state, next-frame restore when pane initialization observes readyState complete; it leaves pre-pageshow binds and all document-scrolling hosts alone. Astra reviewed the repair. Local 27-unit history suite and the exact required WebKit regression pass; hosted rerun remains the release gate.
