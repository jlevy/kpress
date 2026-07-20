---
type: is
id: is-01ky05xhf7n1a51vecbza0d2qt
title: Tighten narrow-screen (phone-width) reading gutters further
kind: task
status: closed
priority: 2
version: 2
labels: []
dependencies: []
created_at: 2026-07-20T16:32:02.534Z
updated_at: 2026-07-20T16:41:27.189Z
closed_at: 2026-07-20T16:41:27.189Z
close_reason: "Shipped in 7c06b91 on feat/toc-collapse (PR #30): Expand/Collapse TOC tooltip+aria pair, drawer-toggle title, phone band drops the toggle-clearance reservation (0.5rem gutter); clearance smoke pins the split contract."
---
Review feedback on a real long report: left/right margins at iPhone widths still read too large after the presentation-polish tightening. Shrink the narrow-width inline gutters only (wide layout unchanged). The floating TOC toggle's translucent fill makes slight text overlap acceptable, so the gutter does not need to clear it.
