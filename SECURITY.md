# Security Policy

## Supported versions

Security fixes are provided for the current `0.1.x` alpha line.
Upgrade to the newest patch before reporting a defect that may already be fixed.

## Report a vulnerability

Do not open a public issue for a suspected vulnerability.
Use
[GitHub private vulnerability reporting](https://github.com/jlevy/kpress/security/advisories/new)
so the maintainers can investigate and coordinate a fix.
Include the KPress and Python versions, the affected entry point and trust mode, a
minimal reproducer, the impact you observed, and whether the report may be shared with
upstream dependencies.

Security-sensitive changes should preserve these package contracts:

- The `sanitized` trust mode (used by dynamic embeds, static publishing, and exports)
  sanitizes author HTML with nh3 as the single authority on what survives: an XSS-inert
  allow-set plus a configurable pass-through allowlist (`<span>`/`<div>` plus
  `format.html.extra_tags`) that admits known custom tags carrying only `class`/`data-*`
  and host-declared inert `format.html.extra_attributes` (validated semantic names such
  as `kind`; never `on*`, `style`, URL-bearing, or DOM-identity attributes), while
  `style`, `on*` handlers, and unsafe-URL schemes are always stripped.
  See “The Document Dialect and Trust Modes” in `docs/kpress-design.md` for the full
  threat model and mode selection.
- Rendering uses explicit trust modes; `trusted` (no sanitization) is only for rendering
  the user’s own local files.
- Sanitization removes disallowed markup; it does not authenticate authorship or make
  surviving user-controlled content unforgeable.
  Hosts must not treat sanitized labels, classes, or `data-*` values as privileged
  identity or authorization signals.
- Static publishing must not write outside the configured output tree.
- Extraction checks must fail on local path leaks, private workspace references, and
  secret-like tokens in public package files.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
