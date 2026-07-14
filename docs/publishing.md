# Publishing KPress Releases

KPress releases are built from a published GitHub release and uploaded to PyPI through
OIDC trusted publishing.
Do not upload from a workstation and do not manually dispatch the publish workflow.

## One-Time PyPI Setup

Register a pending trusted publisher with these exact values:

- PyPI project: `kpress`
- GitHub owner: `jlevy`
- GitHub repository: `kpress`
- Workflow filename: `publish.yml`
- Environment: `pypi`

The environment must match the workflow.
A pending publisher does not reserve the name, so confirm
`https://pypi.org/project/kpress/` is still unclaimed immediately before the first
release.

## Release Checklist

1. Start from an up-to-date, clean `main` and confirm CI is green.

2. Run the complete local gate:

   ```bash
   make verify
   ```

   This installs only from the locks, runs the Python and browser quality gates, audits
   both dependency graphs, builds the source distribution and wheel, rejects repository
   internals from either artifact, and installs the wheel into an isolated environment
   for import, resource, and CLI smokes.

3. Inspect both distributions.
   Run the README quickstart and all bundled examples outside the checkout when a
   release changes public behavior or packaged assets.

4. Update `docs/releases/X.Y.Z.md` and confirm the README install command names the new
   release.

5. Create and publish a GitHub release with the exact tag `vX.Y.Z`. For the first alpha,
   use `v0.1.0`—no alpha suffix.

6. Watch `.github/workflows/publish.yml`. It refuses a non-semantic tag and verifies
   that the dynamically derived package version exactly equals the tag before upload.
   If the workflow fails transiently, re-run the failed jobs from the original Actions
   run (or use `gh run rerun RUN_ID --failed`). A re-run keeps the original event ref
   and commit; do not recreate the tag, republish the release, or add a manual dispatch.

7. Verify the published package from a clean environment:

   ```bash
   uvx --from kpress==X.Y.Z kpress --version
   uvx --from kpress==X.Y.Z kpress --help
   uvx --from kpress==X.Y.Z kpress doctor
   ```

8. Run the README quickstart against the PyPI package and confirm the project page shows
   the AGPL license, Python classifiers, source/issues links, and release notes.

If trusted publishing reports `invalid-pending-publisher` or `invalid-publisher`, check
the owner, repository, workflow filename, and environment on both sides.
Do not work around an identity mismatch with a long-lived API token.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
