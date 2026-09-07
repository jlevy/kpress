---
type: is
id: is-01m1yxrwafhzmry1p7c7wrmr9h
title: Vendor a mono face and lead the mono stack with it (Source Code Pro static 400 and 700)
kind: feature
status: in_progress
priority: 1
version: 3
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies:
  - type: blocks
    target: is-01m1yxry1tpettdccn905znand
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-07T21:53:14.059Z
updated_at: 2026-09-07T22:15:28.015Z
---
kpress ships no mono face; --kpress-font-mono is ui-monospace, SFMono-Regular, Menlo, Consolas, monospace, so code is a different font on every machine and Menlo in a Mac-made PDF. Vendor Source Code Pro (the companion of Source Sans 3, OFL) as static latin woff2 at 400 and 700 from a pinned fontsource release (@fontsource/source-code-pro, exact version, 14-day cool-off, sha256 recorded), named source-code-pro-latin-{400,700}-normal.woff2 beside the other faces; declare them in style-tokens.css; lead the stack with "Source Code Pro" ahead of the system monos. Static faces embed in print, so no print-fonts instance is needed. Re-tune --kpress-font-size-mono (now 0.82 of base, set by eye for system monos) by measurement: Source Code Pro x-height 480/1000 against PT Serif 500 and Source Sans 3 486, so code's x-height sits with the prose it is inlined in, and record the numbers beside the token. Add a fonts README (static/fonts/README.md) recording provenance and license for every vendored face, PT Serif and Source Sans 3 included, which is missing today. Asset contract, goldens, docs. The final choice of mono face is tracked separately; keep this one until that closes.
