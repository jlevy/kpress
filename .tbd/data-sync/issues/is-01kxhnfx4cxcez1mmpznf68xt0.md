---
type: is
id: is-01kxhnfx4cxcez1mmpznf68xt0
title: Publish KPress v0.2.1 maintenance release
kind: task
status: closed
priority: 1
version: 6
spec_path: docs/releases/0.2.1.md
labels: []
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-15T01:15:36.460Z
updated_at: 2026-07-15T01:24:16.236Z
closed_at: 2026-07-15T01:24:16.235Z
close_reason: "KPress v0.2.1 is published and externally verified; release PR #19 is merged, all CI is green, and no review threads remain."
---
Prepare public release notes and current-version docs, run the complete release gate, merge the release-preparation PR, publish tag v0.2.1 through GitHub Trusted Publishing, verify the PyPI artifact in a clean environment, and resolve all actionable PR review threads.

## Notes

Released v0.2.1 from main merge b847ca2. PR #19 passed six checks including the full Python matrix, lint, wheel smoke, and Cursor Bugbot; thread-aware post-check sweep found zero review comments or unresolved threads. Trusted Publishing run 29381459102 succeeded. PyPI serves wheel SHA-256 5bce2c52037e9175bf707bdc18a30596a4c8e9d918042a56526402f0d7fd52be and sdist SHA-256 d13171f67d55d5d5c5338cd5eb293c72024def5468d307a552d7090d44006af1. Exact clean uvx probes report kpress 0.2.1; help and doctor passed with core render, static publish, and full optimizer available.
