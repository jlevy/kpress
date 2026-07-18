---
type: is
id: is-01kxvr0fkx8rbyjeapfddprdwc
title: "Content-size indicators: word counts and reading time via an optional flexdoc metrics extra"
kind: feature
status: open
priority: 3
version: 1
labels: []
dependencies: []
created_at: 2026-07-18T23:12:01.148Z
updated_at: 2026-07-18T23:12:01.148Z
---
Optional off-by-default feature: document-level words + reading time and per-top-section word counts, computed from the existing heading walk with flexdoc's logical_word_count/format_read_time behind a kpress[metrics] extra. Modes off/data/on; contract-registered markup; zero drift when off. Plan: docs/content-size-indicators.plan.md
