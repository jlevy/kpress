---
type: is
id: is-01kxcaxb6mm170gqj4a6zk5p4b
title: Implement or remove nonfunctional CLI and export options
kind: bug
status: open
priority: 1
version: 4
spec_path: TODO.md
labels: []
dependencies:
  - type: blocks
    target: is-01kxcppx52sr5t9s438qwamc62
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-12T23:34:30.355Z
updated_at: 2026-07-13T03:02:15.211Z
---
The public CLI parses --show (format/render), --plaintext/--show (paste), and --all (files) but handlers never read them. export --pdf silently emits the default minimal one-line placeholder/truncated PDF rather than browser output; export --docx has no implementable optional extra and only returns a diagnostic. docs/kpress-design.md also advertises check, seal, pdf, rerun, refetch, and strict surfaces that are absent. Make every shipped option functional and tested, or remove it and align docs before first release.
