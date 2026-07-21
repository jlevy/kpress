---
type: is
id: is-01ky111vjv1brrt7qyp5n6rxkf
title: "doc-actions widget: opt-in Export PDF / View as Markdown text badges"
kind: feature
status: in_progress
priority: 2
version: 3
labels: []
dependencies: []
created_at: 2026-07-21T00:26:15.514Z
updated_at: 2026-07-21T00:35:28.381Z
---
Chrome widget (off by default, format.widgets: {doc-actions: on}) rendering PDF (browser print dialog over print.css) and MD (Markdown twin via the .md-twin URL convention, markdownTwinUrl pinned export, markdown_url override). Hand-drawn type badges: format letters one notch below the TOC Contents label in a 1px currentColor frame; host-tunable badge size/radius tokens (--kpress-doc-actions-badge-size/-radius); card-corner placement with fixed inset-token fallback. Branch feat/doc-actions-widget (stacked on feat/toc-collapse, PR pending); consumed by finterm-site as the vendored pin. Downstream tracking: finterm fin-ubxu.

## Notes

PR jlevy/kpress#31 open (stacked on feat/toc-collapse, PR #30): single squashed commit a698550. Full release gate green locally (make install/lint-check/test/audit + build with explicit interpreter + distribution checks; the plain 'make build' failure here is a local uv interpreter-discovery quirk — CI's make build is green on the base). Repo CI runs on this PR automatically once #30 merges and the PR retargets to main. finterm-site pins a698550 (finterm-main edb5252b, CI green).
