---
type: is
id: is-01m85g3nz60jj7gc4gw8e4n83v
title: "PR #82 N3: the audit reads <![CDATA[ to ]]> where html5ever ends it at the first >"
kind: bug
status: in_progress
priority: 2
version: 2
spec_path: TODO.md
delegate: claude-code@spud10.local
labels: []
dependencies: []
parent_id: is-01m8577cwgvk6zxwrhatkd8tea
hold: null
hold_until: null
created_at: 2026-11-24T00:43:19.851Z
updated_at: 2026-11-24T00:43:49.443Z
started_at: 2026-11-24T00:43:49.441Z
---
Re-review of 5c60a81 (Low, predates the PR for other content): HTMLParser reads <![CDATA[...]]> as one section, html5ever ends it at the first > outside SVG/MathML, so tags inside go unaudited and the catch-all can stay silent (<b onclick=x>b</b><svg><input disabled type=checkbox></svg><![CDATA[x><input type=text name=q onfocus=x>]]>). Fix what is cheap so the report is right.
