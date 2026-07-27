---
type: is
id: is-01kyh1t58cvap810dnkb7av02g
title: Refresh stale tbd managed agent integrations
kind: chore
status: open
priority: 3
version: 1
spec_path: TODO.md
labels:
  - tooling
  - tbd
dependencies: []
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-27T05:47:22.762Z
updated_at: 2026-07-27T05:47:22.762Z
---
tbd doctor reports stale managed copies of .agents/skills/tbd/SKILL.md, .claude/skills/tbd/SKILL.md, and .codex/hooks.json while AGENTS.md and all repository health checks remain current. Run the documented tbd setup refresh for the portable, Claude, and Codex surfaces, inspect every generated diff, verify no project-specific instructions are lost, then run the relevant documentation/lint checks. This is agent-tooling housekeeping, not a KPress v0.2.4 package or publication blocker.
