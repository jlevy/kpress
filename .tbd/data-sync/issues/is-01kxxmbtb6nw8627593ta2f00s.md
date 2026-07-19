---
type: is
id: is-01kxxmbtb6nw8627593ta2f00s
title: Restore dropped supply-chain gate checks from npm_policy consolidation
kind: chore
status: open
priority: 2
version: 2
labels: []
dependencies: []
created_at: 2026-07-19T16:46:47.142Z
updated_at: 2026-07-19T17:47:28.784Z
---
The devtools consolidation (PR #21) replaced npm_policy.py with check_supply_chain.py and dropped two enforcement checks worth restoring: (1) build-system pin verification (hatchling==1.30.1, uv-dynamic-versioning==0.14.0 exact-match against pyproject build-system.requires) — a compromised build backend could inject code into the wheel; (2) npm devDependency set identity (the old gate checked the exact reviewed dependency set; the new one only checks each entry is exact semver, so an added dependency passes unnoticed). Several softer text-invariant checks (workflow uv/node pin constants, persist-credentials:false, fetch-depth:0, uv required-version) also lost mechanical verification. Found during the v0.2.3 pre-release review; all pins are currently still correct in-repo.

## Notes

Concrete evidence for restoring the skill-pin check: tbd setup --auto (0.4.1) rewrote the SKILL.md install line to get-tbd@latest, violating the exact-pin policy; caught only by manual review in PR #27 because the old npm_policy.py skill-pin check was dropped. The restored gate should also normalize/verify the skill install-line pin.
