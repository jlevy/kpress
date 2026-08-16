# Supply-Chain Security

This repository hardens dependency installs against supply-chain attacks.
Read this before adding, upgrading, or running any dependency (this includes
zero-install runners like `npx`, `uvx`, `pnpm dlx`, `bunx`).

This is the project flag file.
The full policy is `tbd guidelines supply-chain-hardening` (guidebook:
<https://github.com/jlevy/supply-chain-hardening>).

## The Default: a 14-Day Cool-Off

**Never install or upgrade to a third-party package version less than 14 days old**
unless a documented exception applies.
Malicious versions are usually detected and yanked within minutes to days, so waiting
costs only slightly staler dependencies.

Enforce the cool-off at resolution time:

| Tool | Control |
| --- | --- |
| uv | `UV_EXCLUDE_NEWER="14 days"` |
| pip 26.1+ | `PIP_UPLOADED_PRIOR_TO="P14D"` |
| npm 11.10+ | `NPM_CONFIG_MIN_RELEASE_AGE=14` |
| npm (any) | `NPM_CONFIG_BEFORE=<now-14d>` (absolute ISO date) |
| pnpm 11+ | `minimumReleaseAge: 20160` in `pnpm-workspace.yaml` |
| Cargo / Go | no native gate: commit the lockfile, install `--locked` / `-mod=readonly`, human-review re-resolves |

## First-Party Exemption

**Packages we publish from our own repositories are exempt from the cool-off.** The
cool-off exists so the wider community can detect and yank malicious versions before we
adopt them; for code we author and publish ourselves, we already control and trust the
source and release pipeline, so the waiting period adds no safety.
We may adopt the latest first-party release immediately.

The exemption covers only the timing window.
First-party dependencies must still be:

- **Pinned to an exact version** (never `@latest` or an open range).
- Preferably verified against the source git tag / provenance for that version.

Current first-party dependencies (all `github.com/jlevy/*`):

| Package | Repository | Runner / install |
| --- | --- | --- |
| get-tbd (`tbd`) | <https://github.com/jlevy/tbd> | `npx get-tbd@<ver>` |
| flowmark-rs (`flowmark`) | <https://github.com/jlevy/flowmark-rs> | `uvx flowmark-rs@<ver>` |
| repren | <https://github.com/jlevy/repren> | `uvx repren@<ver>` |
| pprose (Practical Prose) | <https://github.com/jlevy/practical-prose> | `uvx pprose@<ver>` |

Anything not published from a repository we control is third-party and gets the full
cool-off.

## Other Install Rules

1. **Never install unthinkingly.** Confirm the package is needed, the name is spelled
   correctly (typosquats are common), and the version clears the cool-off (or is
   first-party, lockfile-pinned, or a documented exception).
2. **Disable install/lifecycle scripts by default:** the primary worm exfiltration
   vector (`NPM_CONFIG_IGNORE_SCRIPTS=true`; pnpm `ignoreScripts: true` + `allowBuilds`
   allowlist; `UV_NO_BUILD` / `PIP_ONLY_BINARY` to refuse sdist builds).
3. **Commit lockfiles; install frozen** (`npm ci`, `pnpm install --frozen-lockfile`,
   `--locked`). Never auto-update without reviewing the lockfile diff.
4. **Audit after every install** (`npm audit` / `pnpm audit` / `pip-audit` /
   `cargo audit` / `govulncheck`); address findings before continuing.
5. **No unpinned zero-install runners.** Always pin `@version` for `npx` / `uvx` /
   `pnpm dlx` / `bunx` and review the resolved `package@version`.
6. **No `curl | sh` from untrusted sources.** Verify the installer URL and checksums.

`devtools/check_supply_chain.py` checks the repository controls that span npm, uv, and
GitHub Actions.
The normal lint, test, audit, and build commands enforce everything owned
by their standard configuration files.

## Exception Process for Third-Party Packages

When a third-party version inside the window is genuinely needed (e.g. a same-day CVE
patch):

- State the reason on the record (CVE ID / description, `Reviewed-by:` sign-off).
- Pin the exact `package@version`; verify against OSV / GHSA / maintainer postmortem.
- Confirm afterward that the version was not subsequently yanked.

**Agents never self-approve an exception:** prepare the record; a human signs off.
The first-party exemption above is the only standing carve-out and does not require a
per-install sign-off.

### Granted Exceptions

| Package | Advisory | Published | Adopted | Reviewed-by |
| --- | --- | --- | --- | --- |
| `nanoid@3.3.18` | [GHSA-2v37-7h3g-55p8](https://github.com/advisories/GHSA-2v37-7h3g-55p8) | 2026-08-07 | 2026-08-15 (8 days old) | Joshua Levy <joshua@cal.berkeley.edu> |

`nanoid@3.3.18` is the only version that fixes GHSA-2v37-7h3g-55p8, which covers every
release below it, so `npm audit` failed the `lint` job on every pull request until it
landed. The flaw is a denial of service (CVSS 5.9, CWE-835): a custom generator loops
forever when asked for size zero.
It enters this repository only as a development dependency (`vitest` → `vite` →
`postcss` → `nanoid`), and postcss calls `nanoid(6)` with a fixed nonzero size, so the
exposure here is nil.
The alternative was to leave every pull request red until 2026-08-21, when the version
clears the cool-off on its own and this entry becomes history.

Checked against the registry before adoption: `npm view nanoid@3.3.18` returns a live
`dist.tarball` with no `deprecated` field and the version still listed, and its
published integrity hash matches the `package-lock.json` entry, so the release was not
yanked.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
