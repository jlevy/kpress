---
type: is
id: is-01m1z4h0mzyhdhepp43n8z8kjn
title: Run the Playwright browser tests in CI
kind: task
status: open
priority: 2
version: 2
spec_path: docs/math-text-face.plan.md
labels: []
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-07T23:51:16.382Z
updated_at: 2026-09-08T09:44:31.553Z
---
PR #54 review K54-R8. Eleven tests/test_playwright_*.py files skip in every CI job: playwright is in the pdf extra only, make test runs uv run --frozen pytest without --all-extras, and no workflow runs playwright install. The print sans work (PR #54) is entirely browser and PDF-writer behaviour, so its two browser tests -- tests/test_playwright_print_sans_face.py and tests/test_playwright_print_pdf_fonts.py -- carry the load and never run on CI. PR #54 made the skips loud (pytest addopts = -rs) but did not add the job. Add a CI job that syncs --all-extras, runs playwright install chromium, and runs the browser tests, weighing the ~150MB Chromium download and the wall time against covering a claim (Type0 rather than Type3, and the @page footer) that nothing else in CI can check.

## Notes

Partially addressed by merged PR #59 (a265d553). CI now installs the locked Playwright
Chromium revision and runs the three math browser files in required mode, so missing
Playwright or Chromium fails the job. PR #60 extends that job's regression coverage.

Keep this bead open: the original print/PDF coverage remains outside the dedicated job,
including test_playwright_print_sans_face.py and test_playwright_print_pdf_fonts.py.
The broader reader browser suite also still needs explicit hosted coverage.
