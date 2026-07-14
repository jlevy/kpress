---
type: is
id: is-01kxgzfp9c3v9nkpndh1t89p1s
title: Expose the Finterm host asset and fragment contract
kind: feature
status: closed
priority: 1
version: 3
labels: []
dependencies: []
created_at: 2026-07-14T18:51:00.779Z
updated_at: 2026-07-14T23:23:27.925Z
closed_at: 2026-07-14T23:23:27.924Z
close_reason: "Completed in PR #16 and published as GitHub/PyPI v0.2.0. The typed host asset contract, public materializer, asset policies, and pinned fragment hooks shipped; external registry smokes passed; PR #18 recorded publication status with green main CI."
---
Implement the first-party KPress changes required by Finterm static publishing: return a complete typed per-render package AssetManifest, add a public materializer shared by rendering/publishing/examples, replace include_assets with none/auto/all inclusion policy, pin the public fragment HTML/CSS host contract, and prepare a reviewed release. Main-repo tracking: fin-q77b, fin-neaa, fin-esdz, fin-ginq, fin-mncm.
