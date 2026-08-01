---
type: is
id: is-01kyx9bzheqqjwyafzafyxrkvs
title: "PR #43 review R4: synchronize initial host-owned theme controls"
kind: bug
status: closed
priority: 3
version: 3
labels:
  - release-0.3.0
dependencies: []
parent_id: is-01kyx8cq65jqj03gde1081a1ym
created_at: 2026-07-31T23:50:19.949Z
updated_at: 2026-08-01T00:08:46.246Z
closed_at: 2026-08-01T00:08:46.246Z
close_reason: "Fixed in 79f611f, merged through PR #43 as d0379d2, with local and GitHub CI green."
---
R4 at settings-widget.js:80-84 and the host-integration example. Host-owned embeds stamp only resolved state, so document and test an initial theme:change announcement after mounting settings so aria-checked reflects current host mode before user input.
