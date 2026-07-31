---
type: is
id: is-01kyty81qvckvd016d7xbk24na
title: Two-root Playwright sizing regression test
kind: task
status: closed
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-07-31-declarative-embedding.md
labels: []
dependencies: []
parent_id: is-01kytxz9k3cjy0drxwt3xsq9d8
created_at: 2026-07-31T01:57:27.930Z
updated_at: 2026-07-31T03:14:38.355Z
closed_at: 2026-07-31T02:13:56.045Z
close_reason: Two-root Playwright test added and verified red-then-green against the conversion.
---
New tests/test_playwright_font_sizing.py per the spec Testing Strategy: render a fixture site, drive real Chromium at two root font sizes (16px and 13px via document.documentElement.style.fontSize). Assert (a) with --kpress-host-font-size-base pinned (e.g. 17px), computed sizes of body/h1/h2/code/bullet/tooltip are identical across roots; (b) with default base, sizes scale proportionally; (c) ratio spot-checks: h2/body=1.32, code/body=0.82, bullet/body=0.9. Follow the local-HTTP-server harness pattern of test_playwright_clearance.py.
