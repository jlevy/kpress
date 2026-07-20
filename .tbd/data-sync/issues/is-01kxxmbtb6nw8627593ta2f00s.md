---
type: is
id: is-01kxxmbtb6nw8627593ta2f00s
title: Restore dropped supply-chain gate checks from npm_policy consolidation
kind: chore
status: open
priority: 2
version: 3
labels: []
dependencies: []
created_at: 2026-07-19T16:46:47.142Z
updated_at: 2026-07-19T17:54:19.632Z
---
The devtools consolidation (PR #21) replaced npm_policy.py with check_supply_chain.py and dropped two enforcement checks worth restoring: (1) build-system pin verification (hatchling==1.30.1, uv-dynamic-versioning==0.14.0 exact-match against pyproject build-system.requires) — a compromised build backend could inject code into the wheel; (2) npm devDependency set identity (the old gate checked the exact reviewed dependency set; the new one only checks each entry is exact semver, so an added dependency passes unnoticed). Several softer text-invariant checks (workflow uv/node pin constants, persist-credentials:false, fetch-depth:0, uv required-version) also lost mechanical verification. Found during the v0.2.3 pre-release review; all pins are currently still correct in-repo.

## Notes

Correction to the earlier note: skill-pin enforcement was NOT fully dropped — tests/test_public_hygiene.py::test_agent_skill_runners_use_exact_versions pins exact get-tbd/repren versions and rejects @latest, and the codex/claude hook-anchoring tests pin the anchored command forms; CI (PR #27) caught the tbd 0.4.1 generator regressions exactly as designed. Still open from the devtools consolidation: build-system pin verification (hatchling/uv-dynamic-versioning vs pyproject build-system.requires) and npm devDependency SET identity (format-only check today). Consider also asserting uv.toml required-version.
