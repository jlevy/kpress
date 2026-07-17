# KPress Golden Fixtures

KPress goldens are package-owned, human-readable behavioral specifications.
Reference output from TextPress or Kash can be used while porting behavior, but CI
compares current KPress output against the accepted KPress artifacts in this directory.

Output-tree goldens use YAML written by `frontmatter-format`:

- Generated UTF-8 files are recorded in full: JSON becomes native YAML structure, while
  HTML and other text use literal blocks.
  Both forms produce ordinary line diffs.
- Package CSS, JavaScript, fonts, compressed sidecars, and other binary files are
  recorded by path, byte count, and a short SHA-256 digest.
  Their source is already visible under `src/kpress/format/static/` and covered by
  focused contract tests, so duplicating it inside every publishing scenario would hide
  useful changes in noise.
- A mode-comparison scenario keeps both output trees and their file categories in one
  artifact, making the intended differences visible together.

Update flow:

1. Regenerate only the relevant scenario, for example:

   ```bash
   KPRESS_UPDATE_GOLDENS=1 uv --config-file uv.toml run --frozen pytest tests/test_golden_publish.py -q
   KPRESS_UPDATE_GOLDENS=1 uv --config-file uv.toml run --frozen pytest tests/test_golden_readable_vs_hashed.py -q
   ```

2. Review the full artifact diff, including rendered HTML, output trees, manifests, and
   asset paths.

3. Commit changed goldens only when the behavioral change is intentional.

The helper normalizes temporary paths, sorts YAML deterministically, writes updates
atomically, and keeps update mode opt-in so CI fails on unexpected changes.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
