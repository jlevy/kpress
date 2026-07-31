---
type: is
id: is-01kyty8q78gkqp1y8e7pz8rcn4
title: Playwright theme coherence tests
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-07-31-declarative-embedding.md
labels: []
dependencies: []
parent_id: is-01kytxza2a4r789k649dzrantj
created_at: 2026-07-31T01:57:49.928Z
updated_at: 2026-07-31T03:14:40.652Z
closed_at: 2026-07-31T02:34:27.476Z
close_reason: Theme coherence Playwright test added, red-checked against old CSS, green on new grammar.
---
Real-browser tests per the spec: element-scoped dark inside a root-level light page renders coherently dark with computed color-scheme dark (and the reverse direction); a non-:root host-wrapper scope carrying data-kpress-resolved-theme works; standalone toggle + pre-paint bootstrap still pass existing suites. Follow the test_playwright_clearance.py harness pattern.
