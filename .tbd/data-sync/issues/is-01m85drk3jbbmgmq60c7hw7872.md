---
type: is
id: is-01m85drk3jbbmgmq60c7hw7872
title: "PR #82 I2: KPress-added task classes cannot be told from author classes in the token stream"
kind: bug
status: closed
priority: 2
version: 3
spec_path: TODO.md
delegate: claude-code@spud10.local
labels: []
dependencies: []
parent_id: is-01m8577cwgvk6zxwrhatkd8tea
hold: null
hold_until: null
created_at: 2026-11-24T00:02:19.254Z
updated_at: 2026-11-24T02:10:25.074Z
started_at: 2026-11-24T00:02:36.774Z
closed_at: 2026-11-24T02:10:25.072Z
close_reason: "Fixed in 45d27cd on PR #82: list_item_open and the list's open token record the classes KPress appended in meta['kpress_classes']; HTML unchanged. CI 45306732433 green on 0c0f857."
resolution: null
duplicate_of: null
---
_add_token_classes writes kpress-task task-list-item and contains-task-list into the li/list open tokens' class attr, the same place attribute syntax ({.cls}) puts author classes, so a consumer of the token stream cannot separate them. Record the classes KPress added (meta on the open tokens), keep the rendered HTML byte-identical, document it in the design doc's task-list contract and the release notes, test it.
