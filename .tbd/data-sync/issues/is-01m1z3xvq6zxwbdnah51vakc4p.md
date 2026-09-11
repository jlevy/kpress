---
type: is
id: is-01m1z3xvq6zxwbdnah51vakc4p
title: "PR #54 print sans faces: address and verify its three senior reviews before landing"
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/math-text-face.plan.md
labels:
  - print
dependencies: []
parent_id: is-01m1yxrn6e5m1ddfvc6nrcammj
created_at: 2026-09-07T23:40:48.741Z
updated_at: 2026-09-08T00:05:52.172Z
closed_at: 2026-09-08T00:05:52.162Z
close_reason: "All thirteen findings across the three reviews resolved and verified (comment 5577017556); #54 merged at aee6df7"
resolution: null
duplicate_of: null
---
Three senior reviews landed on jlevy/kpress#54 on 2026-09-07: comment 5576316368 (one Blocker, two Low: PDF export could omit text while print fonts load; fixed in 246f840, 16b2a4a, c6a6496 with the reply 5576556965), comment 5576323864 (K54-R1 to R9: the @page footer face load, a host setting only --kpress-host-font-sans, the Playwright CDP session, _rename name records, --check error handling, test gaps, out-of-subset glyphs, the push trigger, doc slips) and comment 5576343371 (one High on the generated instances' names). Main was merged into the branch at 3a831e7 with goldens refreshed; CI green. The second round is being addressed with the address-pr-review shortcut; every finding gets a disposition, anything deferred gets its own bead under kpr-b4mq, then a verification review reproduces each fix in Chromium before the PR lands, as was done for #53 and squares #114.
