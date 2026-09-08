---
type: is
id: is-01m1yxrwafhzmry1p7c7wrmr9h
title: Vendor Planetaire Mono Text as the mono face at 0.87 of the prose size, replacing the interim Source Code Pro
kind: feature
status: in_progress
priority: 1
version: 6
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies:
  - type: blocks
    target: is-01m1yxry1tpettdccn905znand
  - type: blocks
    target: is-01m1z831f7394cx7ayh9qkkp5s
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-07T21:53:14.059Z
updated_at: 2026-09-08T01:15:51.680Z
---
Decision (owner, 2026-09-08): no Source Code Pro. The interim Source Code Pro vendored on squares/font-consistency (PR #56, commit d80dbaf and the mono parts of the review fixes) is backed out so #56 lands with the system mono stack unchanged (ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; --kpress-font-size-mono stays 0.82), keeping the rest of that branch (box list marker, KPress Quotes, the weight tokens, the fonts README and licences for the faces that stay, the system-mode override covering mono). Planetaire Mono Text then lands as its own pull request: vendored from a pinned planetaire commit or release that includes the OS/2 vertical-metrics fix (the shipped build reports Hack's sxHeight 0.547 and sCapHeight 0.729 while the outlines draw 0.560 and 0.760; a fix PR is in progress on that repo), as latin subsets of regular and bold only by default (the other styles opt in through kpr-hqrr's weights setting), the source sha256, the subsetting command and the B612 OFL, Hack and Planetaire licences recorded in static/fonts/README.md and NOTICE.md; the mono size token 0.87 of the prose size (ink x-height 0.560 em puts code's x-height at 97% of PT Serif's 0.500, about 85 columns at the 45em measure), with the rationale beside it; together with the on/off and weights settings of kpr-hqrr in the same PR or the one after. Chosen by the owner from a four-way comparison (Menlo, Source Code Pro, Hack v3.003, Planetaire) beside PT Serif at 18px, sized from the outlines' ink x-heights with a slider per face.
