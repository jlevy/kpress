# Security Policy

KPress is not yet published as a standalone open-source repository.

Until a public repository and maintainer contact are chosen, report security issues to
the repository maintainers through the private project channel.
Before public distribution, replace this section with the final public reporting
process.

Security-sensitive changes should preserve these package contracts:

- Public-static rendering sanitizes untrusted HTML.
- Dynamic host rendering uses explicit trust modes.
- Static publishing must not write outside the configured output tree.
- Extraction checks must fail on local path leaks, private workspace references, and
  secret-like tokens in public package files.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
