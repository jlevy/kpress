---
type: is
id: is-01m1yxrwafhzmry1p7c7wrmr9h
title: Vendor Planetaire Mono Text as the mono face at 0.87 of the prose size, replacing the interim Source Code Pro
kind: feature
status: in_progress
priority: 1
version: 5
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
updated_at: 2026-09-08T00:53:32.774Z
---
Decision (owner, 2026-09-08, from a comparison page of Menlo, Source Code Pro, Hack v3.003 and Planetaire Mono Text beside PT Serif at 18px, sized from the outlines' ink x-heights with a slider per face): Planetaire Mono Text (github.com/jlevy/planetaire, B612 Mono letterforms with Hack's punctuation and symbols) at a mono size token of 0.87 of the prose size. With its ink x-height of 0.560 em that sets code's x-height at 97% of PT Serif's 0.500 and gives about 85 columns at the 45em measure (advance 0.602 em). Vendor it from a pinned planetaire commit or release that includes the OS/2 vertical-metrics fix (the shipped build reports Hack's sxHeight 0.547 and sCapHeight 0.729 while the outlines draw 0.560 and 0.760; a fix PR is in progress on that repo), as a latin subset like the other vendored faces (regular and bold, italic if the reader uses it; the full Text woff2 files are 51 to 58 KB each and the subset should be far smaller), with the source sha256, the subsetting command and the B612 OFL, Hack and Planetaire licences recorded in static/fonts/README.md and NOTICE.md. Replace the interim Source Code Pro vendored on squares/font-consistency (PR #56) and retune the mono size token from 0.925 to 0.87 with the rationale beside it. Companion: the standard on/off setting (see the sibling bead) so a host can drop the face for page weight.
