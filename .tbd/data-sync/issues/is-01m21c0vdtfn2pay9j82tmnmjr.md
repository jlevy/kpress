---
type: is
id: is-01m21c0vdtfn2pay9j82tmnmjr
title: "font_mode: system host-hook cell contradicted style-tokens.css"
kind: bug
status: open
priority: 3
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T20:40:44.217Z
updated_at: 2026-09-08T20:40:44.217Z
---
docs/kpress-design.md gave the font_mode row the host hook cell 'none: system overrides the role tokens outright'.

style-tokens.css keeps --kpress-font-mono: var(--kpress-host-font-mono, var(--kpress-mono-stack-platform)) inside the .kpress[data-kpress-fonts="system"] block on purpose, with a comment saying so: the block opts a reader out of the fonts KPress downloads and is not a statement about a face the host installed itself. Measured: a host's --kpress-host-font-mono wins under font_mode: system.

Fixed by correcting the cell to name the mono hook as still leading, with the other role tokens overridden outright.

Fixed in branch squares/font-settings-fixes.
