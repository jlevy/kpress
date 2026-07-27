---
type: is
id: is-01kyh111r6095nckxsmz94wddt
title: Inspect release artifacts and clean-room user workflows
kind: task
status: closed
priority: 1
version: 6
spec_path: docs/publishing.md
labels:
  - release
  - packaging
  - testing
dependencies:
  - type: blocks
    target: is-01kyh11209n4en189vpa2ag5b9
parent_id: is-01kyh0z636f2vtfzx6apaxvp2r
created_at: 2026-07-27T05:33:39.973Z
updated_at: 2026-07-27T06:47:43.397Z
closed_at: 2026-07-27T06:47:43.396Z
close_reason: "Final candidate 4c8a713 built and passed wheel/sdist content checks, packaged-license assertions, isolated install and CLI/hashed-site smoke, and all three bundled examples outside the checkout. PR #35 distribution CI is green."
---
Inspect the final wheel and sdist contents and metadata, then install the wheel outside the checkout. Run the README quickstart and all bundled static-site, wrapped-site, and single-document examples against that installed artifact; verify linked and hashed reader assets load, the new TOC/document-actions behavior is present when enabled, repository-only files do not ship, and outputs are reproducible.

## Notes

LOCAL ARTIFACT EVIDENCE GREEN 2026-07-27: canonical make verify built and inspected wheel/sdist, rejected repository-only content, installed the wheel in isolation, and passed CLI/resource/hashed-site smokes. The clean-room wheel test copies and runs all three bundled static-site, wrapped-site, and single-doc examples outside the checkout. Review found and fixed the absent packaged github-slugger ISC notice; the rebuilt wheel now contains both the internal slugger and exact license, enforced by check_distribution. Awaiting final committed candidate SHA/PR CI before closure.
