---
type: is
id: is-01m21c1qr59taehjhfg8j0540e
title: CLI exposes none of the five font settings
kind: bug
status: open
priority: 3
version: 1
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T20:41:13.220Z
updated_at: 2026-09-08T20:41:13.220Z
---
kpress render has no font flags and calls emit_standalone_assets with the defaults (cli.py:73-97), so a mono_font: system document can only be produced through kpress build --config, KPressExportRequest, or RenderOptions. The settings table did not say so, which read as a third surface that agrees when there are only two.

Decision: document the asymmetry rather than add the flags.

Reasoning. No per-document CLI command exposes ANY RenderOptions field beyond --output and --asset-mode: there is no --theme, --palette, --content-card or --no-toc either, so font flags on render would be the single exception. Adding them to render alone leaves format and export behind, which moves the asymmetry rather than removing it, and pinning five new flags in kpress.contract commits the project to a CLI surface on the strength of one feature. That is a design decision for the maintainer, not a defect fix.

Fixed by a new 'The CLI Is Not a Font Surface' subsection in docs/kpress-design.md, linked from the settings table, saying what the three carrying surfaces are and that they agree.

Follow-up worth deciding separately: whether render, format and export should all grow --font-mode, --prose-font, --math-text-font, --mono-font and --mono-weights as one coherent set, pinned in kpress.contract with goldens. Not done here.

Documented in branch squares/font-settings-fixes.
