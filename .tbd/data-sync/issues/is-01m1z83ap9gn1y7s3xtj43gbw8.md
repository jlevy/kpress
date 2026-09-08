---
type: is
id: is-01m1z83ap9gn1y7s3xtj43gbw8
title: FontSpec defaults in theme.py disagree with the shipped font stacks
kind: bug
status: open
priority: 2
version: 1
spec_path: docs/math-text-face.plan.md
labels: []
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T00:53:42.208Z
updated_at: 2026-09-08T00:53:42.208Z
---
`src/kpress/format/theme.py:16-19` declares `FontSpec` defaults of `prose: "Georgia, 'Times New Roman', serif"` and `mono: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"`. Neither is what KPress ships any more: the prose stack now leads with the quote face and PT Serif, and the mono stack leads with the vendored Source Code Pro.

`FontSpec` is part of the public Python contract, but its fields never emit CSS, so nothing renders from them and nothing catches the drift. The result is a second, divergent statement of the font stacks that disagrees with `style-tokens.css` and with the font-role table in `kpress-design.md` on prose and on mono.

Surfaced by the senior review of PR #56 (https://github.com/jlevy/kpress/pull/56, comment 5577269395, "one thing outside this PR"), and deliberately left out of that branch as out of scope.

Decide one of three, then do it in one patch with the contract, docs and tests together:

1. Make the defaults derive from, or be checked against, the stylesheet's tokens so they cannot drift again.
2. Drop the default values (or the fields) if nothing consumes them, since a public field that emits nothing is a claim the code does not keep.
3. Keep them and document what they are for, with a test that pins them against `style-tokens.css`.

Whichever way it goes, add the check that would have caught this: something that compares `FontSpec`'s declared stacks with the tokens in `src/kpress/format/static/css/style-tokens.css`.
