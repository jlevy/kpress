---
type: is
id: is-01kxcaxbm1kwka3bz82hf6vmyj
title: Bundle complete license texts for vendored browser assets
kind: task
status: closed
priority: 1
version: 5
spec_path: TODO.md
labels: []
dependencies:
  - type: blocks
    target: is-01kxcppx52sr5t9s438qwamc62
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-12T23:34:30.784Z
updated_at: 2026-07-13T03:24:05.615Z
closed_at: 2026-07-13T03:24:05.614Z
close_reason: Added complete Lucide/Feather, KaTeX, PT Serif, and Source Sans 3 license/copyright texts under src/kpress/licenses and verified they ship in a clean-room wheel.
---
The wheel includes NOTICE.md, but the repository contains only the project AGPL LICENSE plus a short notice list. Vendored Lucide (ISC), KaTeX (MIT), PT Serif (OFL-1.1), and Source Sans 3 (OFL-1.1) do not have their full upstream license/copyright texts in the source tree or wheel, and the minified KaTeX files have no license banner. Add authoritative license files/copyright notices to the distributed artifact and verify wheel contents before public release.
