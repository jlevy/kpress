---
type: is
id: is-01m8cm37jwbcp6abqvfgdkyjzq
title: "sanitize_raw_html: diagnose=False for hosts that never show what was removed"
kind: task
status: open
priority: 1
version: 1
labels: []
dependencies: []
created_at: 2026-11-26T19:07:40.507Z
updated_at: 2026-11-26T19:07:40.507Z
---
Metabrowser's Markdown diff projection discards the sanitizer's diagnostics, yet the audit and content-event parses cost ~49 of ~56 ms a side on an 85 KB document (Metabrowser mb-d1gq).
