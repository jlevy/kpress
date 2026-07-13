---
type: is
id: is-01kxcaxbm1kwka3bz82hf6vmyj
title: Bundle complete license texts for vendored browser assets
kind: task
status: open
priority: 1
version: 4
spec_path: TODO.md
labels: []
dependencies:
  - type: blocks
    target: is-01kxcppx52sr5t9s438qwamc62
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-12T23:34:30.784Z
updated_at: 2026-07-13T03:02:15.578Z
---
The wheel includes NOTICE.md, but the repository contains only the project AGPL LICENSE plus a short notice list. Vendored Lucide (ISC), KaTeX (MIT), PT Serif (OFL-1.1), and Source Sans 3 (OFL-1.1) do not have their full upstream license/copyright texts in the source tree or wheel, and the minified KaTeX files have no license banner. Add authoritative license files/copyright notices to the distributed artifact and verify wheel contents before public release.
