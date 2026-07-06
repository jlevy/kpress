# Security Policy

KPress is not yet published as a standalone open-source repository.

Until a public repository and maintainer contact are chosen, report security issues to
the repository maintainers through the private project channel.
Before public distribution, replace this section with the final public reporting
process.

Security-sensitive changes should preserve these package contracts:

- The sanitizing trust modes (`sanitized-local` for dynamic embeds, `public-static` for
  static publishing and exports) sanitize author HTML with nh3 as the single authority
  on what survives: an XSS-inert allow-set plus a configurable pass-through allowlist
  (`<span>`/`<div>` plus `format.html.extra_tags`) that admits known custom tags
  carrying only `class`/`data-*`, while `style`, `on*` handlers, and unsafe-URL schemes
  are always stripped.
  See “Trust Modes and the Sanitization Threat Model” in `kpress-design.md` for the full
  threat model and mode selection.
- Dynamic host rendering uses explicit trust modes; `trusted-local` (no sanitization) is
  only for rendering the user’s own local files.
- Static publishing must not write outside the configured output tree.
- Extraction checks must fail on local path leaks, private workspace references, and
  secret-like tokens in public package files.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
