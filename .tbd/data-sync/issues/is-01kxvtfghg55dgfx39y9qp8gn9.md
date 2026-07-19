---
type: is
id: is-01kxvtfghg55dgfx39y9qp8gn9
title: "PR #25 review R7: history plan doc still documents the superseded navigation owner"
kind: bug
status: closed
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01kxvtfevrqbqjb0akmd1ac1xj
created_at: 2026-07-18T23:55:10.767Z
updated_at: 2026-07-19T00:04:19.561Z
closed_at: 2026-07-19T00:04:19.560Z
close_reason: "In 0fac777. R7 fixed: plan Design section rewritten to document owned section fragments vs native bare-# Contents"
---
docs/history-navigation.plan.md:58-66 — says TOC navigation stays native and CSS supplies the glide; PR does the opposite for non-empty fragments. Rewrite subsection: bare-# native vs owned section links, incl. reduced-motion. (PR https://github.com/jlevy/kpress/pull/25, review comment 5013389312)
