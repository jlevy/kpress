---
type: is
id: is-01kyty82gxnmdx4dz28hassyba
title: Sizing docs and changelog
kind: task
status: closed
priority: 2
version: 4
spec_path: docs/done/declarative-embedding.plan.md
labels: []
dependencies: []
parent_id: is-01kytxz9k3cjy0drxwt3xsq9d8
created_at: 2026-07-31T01:57:28.732Z
updated_at: 2026-07-31T23:21:06.034Z
closed_at: 2026-07-31T02:18:07.841Z
close_reason: Sizing docs in kpress-design (done in core patch), host-integration doc, using-kpress skill (both trees), and 0.3.0 release notes.
---
Document the sizing policy per the spec: kpress-design.md sizing-policy section (contract: ratios are design, units are the host's choice; no internal font-size rule may reference rem; root-relative remainder listed), embedder guidance in kpress-operations-and-host-integration.md and the using-kpress skill (set --kpress-host-font-size-base once; never override individual sizes; hosts set base, not normal), changelog entry noting the print-output ratio fix.
