---
type: is
id: is-01kxvn84q60n6ht4cxm7z6kbt5
title: "History-aware section navigation: TOC hash entries + viewport scroll restoration"
kind: feature
status: closed
priority: 2
version: 2
labels: []
dependencies: []
created_at: 2026-07-18T22:23:46.405Z
updated_at: 2026-07-18T22:35:08.356Z
closed_at: 2026-07-18T22:35:08.356Z
close_reason: "Implemented on feature/history-navigation, PR #24 (CI green): native TOC hash navigation, 'history' behavior with viewport scroll restoration, realm-safe viewport resolution, docs + goldens. Merge pending review."
---
TOC clicks previously suppressed native navigation (no hash, no history entry); and the [data-kpress-viewport] pane is invisible to browser history scroll restoration, so Back after a section-link jump reverted the URL but left the pane in place. Feature: toc.js leaves navigation native (CSS scroll-behavior smooth with reduced-motion opt-out), and a new registered 'history' behavior stamps the pane offset into entry state (click capture + debounced scroll) and restores it on popstate with a fragment-target fallback. Realm-safe node checks in viewport.js. Plan: docs/history-navigation.plan.md
