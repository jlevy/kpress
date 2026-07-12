---
type: is
id: is-01kxcaxbm1kwka3bz82hf6vmyj
title: Bundle complete license texts for vendored browser assets
kind: task
status: open
priority: 1
version: 1
labels: []
dependencies: []
created_at: 2026-07-12T23:34:30.784Z
updated_at: 2026-07-12T23:34:30.784Z
---
The wheel includes NOTICE.md, but the repository contains only the project AGPL LICENSE plus a short notice list. Vendored Lucide (ISC), KaTeX (MIT), PT Serif (OFL-1.1), and Source Sans 3 (OFL-1.1) do not have their full upstream license/copyright texts in the source tree or wheel, and the minified KaTeX files have no license banner. Add authoritative license files/copyright notices to the distributed artifact and verify wheel contents before public release.
