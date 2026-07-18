---
type: is
id: is-01kxvtffhjtf3jfqswgtjq7s9r
title: "PR #25 review R3: owned navigation ignores target and download anchor semantics"
kind: bug
status: open
priority: 2
version: 1
labels: []
dependencies: []
parent_id: is-01kxvtfevrqbqjb0akmd1ac1xj
created_at: 2026-07-18T23:55:09.745Z
updated_at: 2026-07-18T23:55:09.745Z
---
history.js:200-219 — plain click on a[href='#sec'][target=_blank] is intercepted instead of opening a new browsing context; download links same class. Leave download/named-target/non-_self anchors native. Tests for _blank, named target, download. (PR https://github.com/jlevy/kpress/pull/25, review comment 5013389312)
