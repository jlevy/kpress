---
type: is
id: is-01m21ndmg1kh1zjxpw3gsp8cn1
title: Restore standalone reader scroll on reload without changing pane semantics
kind: bug
status: in_progress
priority: 2
version: 4
assignee: Codex font_pr_history
labels: []
dependencies: []
created_at: 2026-09-08T23:25:00.284Z
updated_at: 2026-09-09T00:17:38.661Z
---
The standalone KPress page scrolls in its marked inner pane. history.js restores popstate but has no reload/pageshow restoration; verify with a real location.reload() regression, then preserve the existing history entry and immediate scroll position across reload and Back/Forward. Keep document-scrolling hosts native and retain host-owned history.state. Reproduction and fix are isolated in codex/reader-reload-baseline-contract.

## Notes

Regular sans prose could request 410 while its mathematics was fixed at 400. One numeric token now feeds the existing generators for the regular screen/print faces, composite descriptors, Greek scales, KaTeX metrics, font manifest, and runtime warmup descriptions. Normal and italic math use the matching generated weight; intentional medium/bold weights stay unchanged. The supported regular range is 200–500 to preserve KaTeX fallback matching. Margin-box font loading uses the same weight tokens as the printed footer and folio.

This also preserves standalone reader-pane scroll on ordinary and rapid reload through the existing history state, balances the inline-code background without moving its glyph baseline, and documents the measured-strut/zero-leading contract for hosts that prepare math geometry. The unified typography tuning map is complete in `docs/kpress-design.md`, including font roles, replacement inputs, authored serif versus generated sans CSS, baseline acceptance, and exact regression tests.

Companion host work: [Squares PR #135](https://github.com/jlevy/squares/pull/135). KPress owns reusable font generation, readiness, reader-pane history, and baseline contracts. Squares owns prepared publication geometry, saved-setting variants, interactive scheduling, host proportions, and its macOS rendering policy.

### Source and review map

- `src/kpress/format/static/css/style-tokens.css`: authoritative `--kpress-font-weight-sans-regular: 410`; the older light token aliases it. Main's merged PR66 sets the mono ramp to 0.82; this PR preserves that choice.
- `devtools/instance_sans.py`: reads the token through `REGULAR_WEIGHT`; writes static instances, print CSS, and generated asset entries. `devtools/katex_text_metrics.py` writes both metric sets and the bounded sans CSS block; serif CSS and its checked scale constants remain authored.
- `src/kpress/format/static/katex/`: matching composite face descriptors, metric tables, and generated warmup descriptions. The existing actual-required-face readiness/failure contract is preserved.
- `src/kpress/format/pdf.py` and `static/css/print.css`: matching weight-aware footer and folio requests. `static/css/document.css` balances inline-code padding at `0.175em 0.2em`, preserving total padding and glyph baseline.
- `src/kpress/format/static/js/history.js`, `tests/js/history.test.js`, and `tests/test_playwright_history.py`: pane-only departure flush and cancellable pageshow restoration; strict browser target includes these cases.
- `docs/kpress-design.md`, `docs/math-rendering-api.md`, `docs/kpress-operations-and-host-integration.md`, and `docs/project/architecture/arch-2026-09-08-font-and-math-loading.md`: tuning map, host ownership, measured struts, zero-leading carriers, and actual surrounding-text baseline acceptance.

The pane-only `beforeunload` listener never prompts or cancels, but can reduce Firefox bfcache eligibility; this tradeoff was reviewed and accepted. Document-scrolling hosts retain native restoration and receive no new lifecycle hooks. Native-host controls prove KPress does not scroll them. Unchanged WebKit can prefer a real fragment to its saved native offset; that native behavior is checked without imposing pane restoration on document hosts.

### Validation and checkpoint

At product commit `0dd60f9eaf13c982e0d3868c086747522cc01412`:

- Full Python/installed-browser suite: 774 passed; two expected publishing snapshots were refreshed and the focused 13-test rerun passed.
- 75 focused font/asset/generator tests, including changing only the token to 500 and regenerating related surfaces while keeping bold metrics unchanged.
- Sans text/math/print and saved-preference browser regressions; retained footer-only PDF negative failed before weight-aware warmup.
- 246 JavaScript tests; all 14 reload browser cases plus stricter native-host controls.
- Full lint/types, generated-asset drift checks, package audits, wheel/sdist build, and isolated-wheel smoke check.

The docs-only follow-up `125bada18418c563bf614e071379059b62d0b0c3` passed pinned Flowmark 0.3.2, codespell, and whitespace checks. Final integration `9a24c2bbe688360b6d6d15ac0a069a43ac306f5e` merges main `d201627` (PR66); only two generated asset snapshots conflicted. They were regenerated from the combined source, the map was aligned to the merged 0.82 mono ratio, and all 47 affected publishing/mono/asset-contract tests passed in 3.25s. No broad suite rerun is claimed for this final merge.

**Hosted CI and final review remain pending; do not merge yet.** The previously empty check list was caused by a main-branch merge conflict. That conflict is resolved: GitHub reports the final head mergeable, and all six jobs started in [CI run 34294273884](https://github.com/jlevy/kpress/actions/runs/34294273884). No merge, deployment, or final cross-repository acceptance is claimed.

Tracking: kpr-3y8q (Squares think-bccr), kpr-n1j6 (reload), kpr-37if (Squares think-y54j), kpr-gj9v (prepared baseline contract), and kpr-6q53 (typography map, Squares think-vunf). These remain in progress pending acceptance. The Vitest security fix kpr-6uk0 is already merged through PR52 and closed. Current npm/Python audits pass; GitHub still printed a default-branch security-alert banner, so its scanner state is not claimed resolved.

### Next-agent continuation

The current pushed head is `9a24c2bbe688360b6d6d15ac0a069a43ac306f5e`, branch `codex/reader-reload-baseline-contract`, isolated checkout `/private/tmp/kpress-reader-reload`. The local normal Python 3.14.7 environment is `/private/tmp/kpress-reader-reload-py314`; use `UV_PROJECT_ENVIRONMENT` for uv commands and pass that interpreter explicitly to `uv build --no-build-isolation --python ...`.

The source and tuning-map work are committed; no local test process remains running. Complete final review and the existing hosted run, fixing only concrete findings. Coordinate the final pin and HTML/PDF checks with Squares PR135, then merge in the reviewed upstream-to-host order and close/sync the corresponding beads. The PR bodies and the committed architecture/API/design docs carry the handoff; no new font framework or product expansion is planned.
