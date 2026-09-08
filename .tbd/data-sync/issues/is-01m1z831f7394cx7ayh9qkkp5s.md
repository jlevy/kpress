---
type: is
id: is-01m1z831f7394cx7ayh9qkkp5s
title: A standard kpress setting turns the shipped mono face off, falling back to the system mono stack
kind: feature
status: open
priority: 1
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T00:53:32.774Z
updated_at: 2026-09-08T00:53:32.774Z
---
Owner (2026-09-08): Planetaire is a good default, but a document must be able to turn the shipped mono off through standard kpress settings when it does not want the page weight (a single-file page inlines every face it declares). Follow the math_text_font pattern: a RenderOptions field mono_font with values planetaire (default) and system, the format.mono_font config key, a data attribute (data-kpress-mono-font) stamped by the render, a CSS switch under it that makes --kpress-font-mono the system stack (ui-monospace, SFMono-Regular, Menlo, Consolas, monospace) and leaves the Planetaire faces undeclared or unreachable, the public names pinned in kpress.contract with tests and goldens in the same commit, docs in kpress-design.md and the operations doc (including what a host that inlines assets should prune when the setting is system), and a note that hosted pages pay nothing for an unused @font-face while inlined pages pay its bytes, which is what the setting is for.
