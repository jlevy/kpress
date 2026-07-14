---
type: is
id: is-01kxh4adjkmxcnvqwe2q9njkf8
title: Include tooltip assets for same-document links
kind: bug
status: closed
priority: 1
version: 3
labels: []
dependencies: []
created_at: 2026-07-14T20:15:30.899Z
updated_at: 2026-07-14T20:28:06.908Z
closed_at: 2026-07-14T20:28:06.908Z
close_reason: "Tooling floor, dependency monitoring, Node action upgrade, and same-document tooltip asset closure are implemented; make verify and PR #17 CI are green."
---
The v0.2.0 asset manifest selects js/tooltips.js for footnotes but omits it for ordinary same-document hash links, causing the real-browser tooltip test to time out. Add a focused regression test and select the tooltip entry point for all supported same-document links.
