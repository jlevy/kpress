---
type: is
id: is-01m8508mmhvek09jsx2kfr3hhv
title: Draw task-list boxes from a KPress token, and admit input only as a disabled checkbox when sanitized
kind: feature
status: closed
priority: 2
version: 3
delegate: claude-code@spud10.local
labels: []
dependencies: []
hold: null
hold_until: null
created_at: 2026-11-23T20:06:25.168Z
updated_at: 2026-11-23T20:42:53.230Z
started_at: 2026-11-23T20:06:29.307Z
closed_at: 2026-11-23T20:42:53.230Z
close_reason: Task-list box drawn from the kpress_task_checkbox token; sanitized <input> kept only as a disabled checkbox (commit 92ef5ad, branch claude/task-list-checkboxes).
resolution: null
duplicate_of: null
---
A GitHub task list box (- [ ] / - [x]) reached MarkdownIt as an html_inline token holding raw <input> HTML from mdit_py_plugins.tasklists, so a token consumer (Metabrowser's rendered diff) had to match that HTML to find the box and its state. KPress now owns the box: its own core rule inserts a kpress_task_checkbox token (tag input, markup is the source marker, meta checked is True or False) drawn by a KPress renderer rule, and sets the item and list classes on their tokens. The sanitized profile admits <input> only as that inert box: a disabled checkbox keeping class and checked; any other raw input loses its other attributes and becomes a disabled checkbox, with diagnostics.
