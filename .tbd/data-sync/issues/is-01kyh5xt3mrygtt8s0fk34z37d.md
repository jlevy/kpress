---
type: is
id: is-01kyh5xt3mrygtt8s0fk34z37d
title: "PR #35 review KPR-REV-01: Disable collapse CSS with runtime override"
kind: bug
status: closed
priority: 2
version: 4
spec_path: docs/publishing.md
labels:
  - review
  - pr-35
  - browser
dependencies: []
parent_id: is-01kyh5xswebfjx97t88cnab498
created_at: 2026-07-27T06:59:16.723Z
updated_at: 2026-07-27T07:11:00.282Z
closed_at: 2026-07-27T07:11:00.281Z
close_reason: "KPR-REV-01 fixed in 3234dca, regression-covered, pushed to PR #35, disposition published, inline thread resolved, and final CI fully green."
---
PR #35 KPR-REV-01 at src/kpress/format/static/js/toc.js:219-259, src/kpress/format/static/css/components.css:616-636, and tests/js/toc-collapse.test.js:235-243. With server collapse markup and runtime collapseDepth: 0, remove data-kpress-toc-collapse-depth for the active binding so collapse-only clipping and transitions do not apply; restore the exact original attribute on disposal; add a red-green lifecycle regression test; run focused and full release validation.

## Notes

FIXED in 3234dca. Red-green regression: the focused TOC test first failed because the collapse activation attribute remained 1, then passed after the runtime binding began removing the attribute and restoring the exact server value on disposal. Final validation: focused TOC suite 11/11; make verify passed with 574 Python/Playwright tests and 173 Vitest assertions; all PR checks green. Inline disposition: https://github.com/jlevy/kpress/pull/35#discussion_r3655077209
