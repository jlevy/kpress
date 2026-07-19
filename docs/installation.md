# Installing uv and Python

KPress `0.2.3` supports macOS and Linux with Python 3.12 or newer.
The current full optimizer uses a POSIX file lock, so Windows is not yet a supported
runtime platform; native Windows support is tracked by `kpr-isp2`.

KPress uses [uv](https://docs.astral.sh/uv/) to install Python, resolve the locked
environment, and run project commands.
Follow the repository [supply-chain policy](../SUPPLY-CHAIN-SECURITY.md) before
installing or upgrading uv or any project dependency.

Use the
[official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)
for a reviewed installation method.
The [CI workflow](../.github/workflows/ci.yml) owns the repository’s reviewed exact uv
version. Use that version, verify its source and checksum, and confirm `uv --version`
before using it on the lockfile.
Do not run a mutable installer command copied from an unreviewed source.

Install one of KPress’s supported Python versions:

```shell
uv python install 3.13
```

Then continue with the [development guide](development.md).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
