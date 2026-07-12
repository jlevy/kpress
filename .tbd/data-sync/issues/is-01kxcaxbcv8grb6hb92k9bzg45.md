---
type: is
id: is-01kxcaxbcv8grb6hb92k9bzg45
title: Make full optimizer bootstrap deterministic and preflight real readiness
kind: bug
status: open
priority: 1
version: 1
labels: []
dependencies: []
created_at: 2026-07-12T23:34:30.555Z
updated_at: 2026-07-12T23:34:30.555Z
---
The optional full optimizer's cold cache starts with npm install because no lockfile is shipped; only later runs use npm ci. _npm_env sets NPM_CONFIG_MINIMUM_RELEASE_AGE=20160, which is the pnpm-style variable/value rather than the repository's npm NPM_CONFIG_MIN_RELEASE_AGE=14 policy. Doctor/preflight only check npx presence, --allow-network is ignored, and code actually invokes npm. build_site creates/purges output before the first real cache install, so a network/install failure can destroy the prior build. Ship/use a reviewed lockfile, apply the correct npm age control, probe/install before output mutation, and test cold/offline/error paths.
