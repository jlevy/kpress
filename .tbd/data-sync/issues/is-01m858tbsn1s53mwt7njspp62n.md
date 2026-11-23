---
type: is
id: is-01m858tbsn1s53mwt7njspp62n
title: parse_markdown raises IndexError on a table in a blockquote ending with an empty quote line
kind: bug
status: open
priority: 3
version: 1
spec_path: TODO.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-11-23T22:35:54.548Z
updated_at: 2026-11-23T22:35:54.548Z
---
Found by the correctness review of PR #82, outside its scope. parse_markdown('> | a |\n> |---|\n> | b |\n> ', title='T') raises IndexError: string index out of range. Stock MarkdownIt('js-default').render of the same source raises too, so the bug is upstream in markdown-it-py's table rule (reproduced with the locked markdown-it-py).
