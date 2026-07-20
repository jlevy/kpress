---
type: is
id: is-01ky05xh7dxfea7ny3m2m9gghf
title: Explanatory tooltips on all icon chrome controls (Expand/Collapse TOC label pair)
kind: task
status: closed
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-07-18-collapsible-toc.md
labels: []
dependencies: []
parent_id: is-01kxvtjgzee34yvykhc06e775z
created_at: 2026-07-20T16:32:02.283Z
updated_at: 2026-07-20T16:41:27.171Z
closed_at: 2026-07-20T16:41:27.170Z
close_reason: "Shipped in 7c06b91 on feat/toc-collapse (PR #30): Expand/Collapse TOC tooltip+aria pair, drawer-toggle title, phone band drops the toggle-clearance reservation (0.5rem gutter); clearance smoke pins the split contract."
---
Every icon-only operation control carries an explanatory tooltip (title) matching its aria-label, per the icon-only affordance primitive. TOC expand-all: title/aria-label become 'Expand TOC' / 'Collapse TOC' (server initial state + toc.js swap). Audit toc drawer toggle, code-copy, video-close (settings gear + chooser segments already have titles). Extend tests to pin titles.
