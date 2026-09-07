---
type: is
id: is-01m1z4h0mzyhdhepp43n8z8kjn
title: Run the Playwright browser tests in CI
kind: task
status: open
priority: 2
version: 1
spec_path: docs/math-text-face.plan.md
labels: []
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-07T23:51:16.382Z
updated_at: 2026-09-07T23:51:16.382Z
---
PR #54 review K54-R8. Eleven tests/test_playwright_*.py files skip in every CI job: playwright is in the pdf extra only, make test runs uv run --frozen pytest without --all-extras, and no workflow runs playwright install. The print sans work (PR #54) is entirely browser and PDF-writer behaviour, so its two browser tests -- tests/test_playwright_print_sans_face.py and tests/test_playwright_print_pdf_fonts.py -- carry the load and never run on CI. PR #54 made the skips loud (pytest addopts = -rs) but did not add the job. Add a CI job that syncs --all-extras, runs playwright install chromium, and runs the browser tests, weighing the ~150MB Chromium download and the wall time against covering a claim (Type0 rather than Type3, and the @page footer) that nothing else in CI can check.
