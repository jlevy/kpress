---
type: is
id: is-01m21qczew6x03azs3eaa4n1vy
title: Balance the inline code background around the baseline
kind: bug
status: in_progress
priority: 2
version: 3
labels: []
dependencies: []
created_at: 2026-09-08T23:59:35.888Z
updated_at: 2026-09-09T00:08:04.869Z
---
Squares think-y54j: user reported raised-looking Planetaire inline code. Actual glyph baselines are aligned (all eleven measured code cases are zero in screen and print); independent optical review identifies the asymmetric .25em top/.1em bottom padding around the code pill. Balance to .175em top and bottom, preserving total vertical padding, font metrics, glyph baseline and wrapping. Host keeps the retained baseline negative-control measurement.

## Notes

Regular sans prose could request 410 while its mathematics was fixed at 400. One numeric token now feeds the existing generators for the regular screen/print faces, composite descriptors, Greek scales, KaTeX metrics, font manifest, and runtime warmup descriptions. Normal and italic math use the matching generated weight; intentional medium/bold weights stay unchanged. The supported regular range is 200–500 to preserve KaTeX fallback matching. Margin-box font loading uses the same weight tokens as the printed footer and folio.

This also preserves standalone reader-pane scroll on ordinary and rapid reload through the existing history state, balances the inline-code background without moving its glyph baseline, and records the measured-strut/zero-leading contract for hosts that prepare math geometry. Native document-scrolling hosts retain browser restoration. The pane-only beforeunload listener never prompts or cancels, but can reduce Firefox bfcache eligibility.

Validation completed:

- Full Python/installed-browser suite: 774 passed; two expected publishing snapshots were refreshed and the focused 13-test rerun passed.
- 75 focused font/asset/generator tests, including changing only the token to 500 and regenerating every related surface while keeping bold metrics unchanged.
- Sans text/math/print and saved-preference browser regressions; retained footer-only PDF negative failed before the weight-aware warmup.
- 246 JavaScript tests; all 14 reload browser cases plus stricter native-host controls.
- Full lint/types, generated-asset drift checks, package audits, wheel/sdist build and isolated-wheel smoke check.

Checkpoint status: **hosted CI and final review remain pending; do not merge yet.** The requested unified typography tuning map is a separately coordinated documentation followup and is not claimed complete here. Squares host adoption/pin and final HTML/PDF checks are tracked on jlevy/squares PR135.

Tracking: kpr-3y8q (Squares think-bccr), kpr-n1j6 (reload), kpr-37if (Squares think-y54j), kpr-gj9v (prepared baseline contract). The Vitest security fix kpr-6uk0 is already on main through PR52; this branch includes that merge.

Continuation: source commit 0dd60f9eaf13c982e0d3868c086747522cc01412; isolated checkout `/private/tmp/kpress-reader-reload`, branch `codex/reader-reload-baseline-contract`. Local normal Python environment is `/private/tmp/kpress-reader-reload-py314`; use `UV_PROJECT_ENVIRONMENT` for uv commands and pass its interpreter explicitly to `uv build --no-build-isolation --python ...`. No product changes are planned unless CI/review finds a concrete defect.
