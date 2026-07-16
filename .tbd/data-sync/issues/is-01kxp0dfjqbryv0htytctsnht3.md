---
type: is
id: is-01kxp0dfjqbryv0htytctsnht3
title: Simplify repository tooling policy into focused behavioral checks
kind: task
status: closed
priority: 1
version: 5
labels: []
dependencies: []
created_at: 2026-07-16T17:43:29.111Z
updated_at: 2026-07-16T18:40:21.455Z
closed_at: 2026-07-16T18:40:21.454Z
close_reason: Implemented, independently reviewed, and fully verified.
---

## Notes

Completed in 08a9ba9. Replaced the 279-line npm policy monolith and mixed tests with the shared 144-line cross-file supply-chain checker, five focused tests, and separate distribution hygiene tests. Removed four npm pass-through wrappers and dead lifecycle configuration; aligned Make, CI, Lefthook, formatting, linting, testing, audits, builds, and docs with MetaBrowser. Vitest now belongs to make test, CI no longer duplicates distribution smoke, and distribution checks reuse public-hygiene logic. The checker is byte-identical to MetaBrowser and covers npm >=11.10 release-age enforcement, exact direct npm specs, lock registry/integrity, matching nvm/fnm pins, uv cool-off, immutable GitHub and Docker actions, and trusted publishing. Independent review findings were fixed. Final make -j4 verify: 531 tests passed, one skipped; 120 Vitest tests passed; lint, strict types, Biome, tsc, Flowmark, public hygiene, supply-chain checks, npm/uv audits, build and isolated wheel smoke all passed.
