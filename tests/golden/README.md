# KPress Golden Fixtures

KPress goldens are package-owned acceptance artifacts.
Reference output from TextPress or Kash can be used while porting behavior, but normal
CI compares current KPress output against the accepted KPress artifacts in this
directory.

Update flow:

1. Run the relevant tests with `KPRESS_UPDATE_GOLDENS=1`.
2. Review the full artifact diff, including rendered HTML, output trees, manifests, and
   asset paths.
3. Commit changed goldens only when the behavioral change is intentional.

The helper normalizes temp paths and keeps update mode opt-in so CI fails on unexpected
changes.

<!-- This document follows std-doc-guidelines.md.
Review guidelines before editing.
-->
