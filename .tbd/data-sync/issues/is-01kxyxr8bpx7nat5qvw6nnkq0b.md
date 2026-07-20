---
type: is
id: is-01kxyxr8bpx7nat5qvw6nnkq0b
title: "Settings plumbing: toc_collapse_depth and toc_expand_on_scroll end to end"
kind: task
status: closed
priority: 2
version: 4
spec_path: docs/project/specs/active/plan-2026-07-18-collapsible-toc.md
labels: []
dependencies:
  - type: blocks
    target: is-01kxyxr8kj6s9ev21asbwbpehg
parent_id: is-01kxvtjgzee34yvykhc06e775z
created_at: 2026-07-20T04:50:06.325Z
updated_at: 2026-07-20T06:07:40.145Z
closed_at: 2026-07-20T06:07:40.145Z
close_reason: "Implemented on feat/toc-collapse: sprite glyphs + icon contract (6ffebdf), settings plumbing + cache-key fix (8107930); full pytest suite green."
---
RenderOptions.toc_collapse_depth (int|None, default None, validated >=1) and toc_expand_on_scroll (bool, default True) in format/model.py; mirror on FormatConfig with YAML keys in _KNOWN_FORMAT_KEYS, load_config validation, threading in publish/build.py; dynamic-path mapping on KPressRenderRequest in runtime.py (like show_doc_header). Unit tests for validation and default-off behavior. Mirrors the toc_min_headings precedent. Spec: Design > Settings.
