---
type: is
id: is-01kxcaxbcv8grb6hb92k9bzg45
title: Make full optimizer bootstrap deterministic and preflight real readiness
kind: bug
status: closed
priority: 1
version: 5
spec_path: TODO.md
labels: []
dependencies:
  - type: blocks
    target: is-01kxcppx52sr5t9s438qwamc62
parent_id: is-01kxcpnre3k47pw88htva8xt0d
created_at: 2026-07-12T23:34:30.555Z
updated_at: 2026-07-13T03:24:05.433Z
closed_at: 2026-07-13T03:24:05.432Z
close_reason: Shipped a reviewed optimizer package-lock, enforced npm ci with the correct age policy, implemented real doctor network semantics, and moved cold-cache bootstrap before any output mutation with cold/offline/error tests.
---
The optional full optimizer's cold cache starts with npm install because no lockfile is shipped; only later runs use npm ci. _npm_env sets NPM_CONFIG_MINIMUM_RELEASE_AGE=20160, which is the pnpm-style variable/value rather than the repository's npm NPM_CONFIG_MIN_RELEASE_AGE=14 policy. Doctor/preflight only check npx presence, --allow-network is ignored, and code actually invokes npm. build_site creates/purges output before the first real cache install, so a network/install failure can destroy the prior build. Ship/use a reviewed lockfile, apply the correct npm age control, probe/install before output mutation, and test cold/offline/error paths.
