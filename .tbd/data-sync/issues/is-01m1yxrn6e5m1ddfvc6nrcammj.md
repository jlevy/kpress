---
type: is
id: is-01m1yxrn6e5m1ddfvc6nrcammj
title: "[epic] Every glyph from a shipped face, on screen and in print"
kind: epic
status: open
priority: 1
version: 22
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
child_order_hints:
  - is-01m1ywfjt036hrzk0tk8p9je6v
  - is-01m1yxrwafhzmry1p7c7wrmr9h
  - is-01m1yxry1tpettdccn905znand
  - is-01m1yxs06avbwn98cb4v2n7f3h
  - is-01m1yxs24czqc8y3zz1n6q9709
  - is-01m1ymqzc9eyan1n7yg2gzewad
  - is-01m1yffqyysqevrgj22mvy6keg
  - is-01m1z1st1e16fv3dac88902wgm
  - is-01m1z2gzgnz8nk8tc7vd2y6xen
  - is-01m1z3xvakyjevkv745b4nmym0
  - is-01m1z3xvq6zxwbdnah51vakc4p
  - is-01m1z4h0mzyhdhepp43n8z8kjn
  - is-01m1z4h8rj102y46mjzan6pxcv
  - is-01m1z5brtdfe25898yb3mafb03
  - is-01m1z743jtmn911ekdsga2pevj
  - is-01m1z831f7394cx7ayh9qkkp5s
  - is-01m1z83ap9gn1y7s3xtj43gbw8
  - is-01m1z83xj86jfm721scrcm718x
  - is-01m1z8drasjh3hct7hke23s0kj
  - is-01m1z8edra0hm7txfrmzpa9ahr
  - is-01m1z8feedrzwyhq44z84qenh3
created_at: 2026-09-07T21:53:06.765Z
updated_at: 2026-09-08T01:00:19.268Z
---
Rule: a kpress document resolves every text run to a face kpress ships (PT Serif, Source Sans 3 variable on screen and static in print, the KaTeX faces and KPress Math Text composite, and a shipped mono), never to whatever the reader's or the renderer's machine has. Measured on the squares explainer PDF (946 KB): the sans was 345 KB of Type3 paths (kpr-w0s9), inline code was Menlo from the system (56 KB embedded), the list bullet U+25AA fell through PT Serif to Georgia (16 KB), and quotation marks come from Georgia on screen via LocalPunct. Children: kpr-w0s9 (print sans), the mono face, the list marker, LocalPunct, and the composite subsets (kpr-hhdc).
