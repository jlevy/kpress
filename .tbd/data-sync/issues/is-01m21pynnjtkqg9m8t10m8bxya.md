---
type: is
id: is-01m21pynnjtkqg9m8t10m8bxya
title: "npm audit fails the lint job: GHSA-82fw-gwwq-j7x9 in @vitest/mocker"
kind: bug
status: closed
priority: 1
version: 2
labels:
  - supply-chain
dependencies: []
created_at: 2026-09-08T23:51:47.120Z
updated_at: 2026-11-16T23:17:51.023Z
closed_at: 2026-11-16T23:17:51.022Z
close_reason: "Fixed on main: vitest is pinned at 5.0.3, past the advisory's range, and npm audit passes in CI at af8f3f1."
resolution: null
duplicate_of: null
---
`npm audit --audit-level=moderate` reports GHSA-82fw-gwwq-j7x9, a path traversal /
arbitrary file read in `@vitest/mocker` covering vitest 2.1.0 through 4.1.10, so
`make audit` exits non-zero and the CI `lint` job fails on every branch.

Not caused by any branch. main's own CI passed at 4a868bb on 2026-09-08 at 20:50Z and
the same audit failed at 23:47Z on a tree whose `package.json` and `package-lock.json`
are byte-identical to main's, so the advisory was published between those two times.
It reproduces locally on an unmodified lockfile.

The fix is `vitest@4.1.11`, published 2026-08-18 -- 21 days old, so it clears the
14-day cool-off in SUPPLY-CHAIN-SECURITY.md and needs no granted exception. The pin in
`package.json` is exact (`4.1.9`), so the bump is a one-line change plus the lockfile.

Left undone deliberately: the bump was not folded into the 0.82 mono-ratio branch
(PR #66). It is a supply-chain change unrelated to that PR's subject, and the sandbox
declined the dependency write, which is the right default for an unrequested dependency
change. Needs the owner's go-ahead, then: bump the pin, `npm install --ignore-scripts`,
re-run `npm audit` and `make test`.
