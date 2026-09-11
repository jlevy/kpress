---
type: is
id: is-01m21c1f4n2vssddn9z5j2fnhe
title: RenderOptions accepted mono_weights sets config refuses
kind: bug
status: closed
priority: 1
version: 2
spec_path: docs/math-text-face.plan.md
labels:
  - typography
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-08T20:41:04.405Z
updated_at: 2026-09-09T00:08:29.714Z
closed_at: 2026-09-09T00:08:29.714Z
close_reason: "Shipped: the RenderOptions gate shipped in kpress#65; mono_weights_rejection is on main and RenderOptions calls it"
resolution: null
duplicate_of: null
---
The mono_weights synthesis gate lived only in publish/config.py, so RenderOptions(mono_weights=("regular",)) and mono_weights=() were accepted silently by the Python API. The docs said such sets are 'refused at config load', which is literally true and practically misleading: export_document, KPressRenderRequest and any embedding host build RenderOptions directly, so the /Type3 PDF the gate exists to prevent was one keyword argument away. That is how the verification pass produced its Type 3 measurements.

Fixed by extracting the refusal into format.assets.mono_weights_rejection(weights, mono_font=..., weights_setting=..., font_setting=...), which returns the message or None. publish/config.py raises KPressPublishError with it naming format.mono_weights/format.mono_font; RenderOptions.__post_init__ raises KPressInvalidRequestError with it naming mono_weights/mono_font. Nothing else in the message differs.

Tests in tests/test_mono_face.py: test_render_options_refuses_the_same_sets_the_config_refuses (six synthesizing sets refused, three admissible sets accepted, and every set accepted under mono_font=system), test_both_surfaces_refuse_in_the_same_words (the two messages are equal after replacing 'format.mono' with 'mono'), plus an unknown-style-name assertion on the Python API.

Fixed in branch squares/font-settings-fixes.
