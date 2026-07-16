---
type: is
id: is-01kxp0dfjqbryv0htytctsnht3
title: Simplify repository tooling policy into focused behavioral checks
kind: task
status: in_progress
priority: 1
version: 3
labels: []
dependencies: []
created_at: 2026-07-16T17:43:29.111Z
updated_at: 2026-07-16T17:56:36.498Z
---

## Notes

Implemented without commit or push. Replaced the 279-line npm_policy.py with a 132-line project-agnostic check_supply_chain.py limited to cross-file supply-chain invariants. Removed duplicated project and version constants plus docs, Makefile, Lefthook, Copier, skill, ratchet, and workflow-implementation scans. Added four focused supply-chain tests and moved two distribution hygiene tests to test_distribution.py. Updated Makefile, Lefthook, AGENTS, development and operations docs, validation runbook, and supply-chain policy references. Validation: pinned Node 24.18.0 make format passed; six targeted tests passed; targeted Ruff and BasedPyright clean; make verify passed with 530 Python tests, one skip, 120 Vitest tests, all lint and type gates, npm and uv audits, builds, and isolated distribution smoke.
