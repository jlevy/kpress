---
type: is
id: is-01kxhrdthhtkzq4jcj3mavtzqa
title: Allow hosts to export supplied source text
kind: feature
status: closed
priority: 1
version: 4
labels:
  - api
  - export
dependencies: []
created_at: 2026-07-15T02:06:54.000Z
updated_at: 2026-07-15T02:15:48.749Z
closed_at: 2026-07-15T02:15:48.749Z
close_reason: "Shipped in KPress v0.2.2 via PR #20. Trusted Publishing succeeded; PyPI wheel SHA256 46c3e9f0496f30d7e5c19c08c38a96634bee257af15124da0795fa267e9698e1 and sdist SHA256 475f78dde2cd762f40add1351e3ca49b6c186182b2ef6fe1f8069182e14fb2cc were verified, and an isolated registry install exposed source_text on KPressExportRequest."
---
Add an optional source_text field to KPressExportRequest. When supplied, export_document must render that text while retaining request.path as the logical source path for title and relative-asset resolution. Preserve path-reading behavior when omitted. This unblocks gzip-transparent host exports without temporary source files.

## Notes

Added optional KPressExportRequest.source_text and taught publish export to use host-decoded text while retaining path as logical identity and relative-asset base. Existing path-read behavior remains unchanged when omitted. Regression proves a nonexistent logical source can export supplied Markdown and copy a sibling relative asset. Prepared public 0.2.2 docs. Complete make verify: 525 Python tests and 120 JS tests; Ruff/BasedPyright/Biome/TypeScript/Flowmark/public hygiene clean; frozen audits clean; wheel/sdist and clean-room install checks passed.
