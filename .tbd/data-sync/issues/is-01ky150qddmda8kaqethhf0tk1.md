---
type: is
id: is-01ky150qddmda8kaqethhf0tk1
title: Provide expand-all chrome when JS config enables TOC collapse
kind: bug
status: open
priority: 2
version: 1
labels:
  - toc
  - javascript
  - host-api
dependencies: []
parent_id: is-01ky147hh0nbx9vhjphw3fabn3
created_at: 2026-07-21T01:35:32.780Z
updated_at: 2026-07-21T01:35:32.780Z
---
The documented behaviors.configure('toc', {collapseDepth: N}) path can enable collapse on server output that was rendered with collapse off. toc.js then collapses deep rows, but the server emitted no data-kpress-toc-expand-all control, leaving no way to expand all. Make the JS override path create/activate equivalent chrome or constrain/document the API so it cannot produce inaccessible collapsed content; test against true collapse-off server markup without a dormant button.
