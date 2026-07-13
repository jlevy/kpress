---
type: is
id: is-01kxcppxcf27r7ekbbxes2nk2r
title: Complete real-browser reader and print acceptance
kind: task
status: open
priority: 2
version: 3
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-13T03:00:42.510Z
updated_at: 2026-07-13T05:00:26.414Z
---
Run and record representative desktop, narrow, light/dark, print, and no-console/no-network checks across TOC, settings, tooltips, tables, code copy, tabs, video popovers, math, and long-form documents. Keep automated Playwright smoke focused; store human visual observations in the public runbook.

## Notes

2026-07-12 PR #11 review evidence at head after R2 fix: rendered tests/e2e/docs/index.md with linked assets, served on 127.0.0.1:9050, opened Settings, selected Dark theme, and verified the menu remained visible and aria-expanded=true, focus remained on the Dark theme control, aria-checked=true, root theme/resolved-theme=dark, and no browser console warnings or errors. This covers the targeted settings interaction only; the full desktop/narrow/print matrix remains open.
