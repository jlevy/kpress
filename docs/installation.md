# Installing uv and Python

KPress `0.1.0` supports macOS and Linux with Python 3.12 or newer.
The current full optimizer uses a POSIX file lock, so Windows is not yet a supported
runtime platform; native Windows support is tracked by `kpr-isp2`.

This project is set up to use [**uv**](https://docs.astral.sh/uv/), the new package
manager for Python. `uv` replaces traditional use of `pyenv`, `pipx`, `poetry`, `pip`,
etc. This is a quick cheat sheet on that:

On macOS or Linux, if you don’t have `uv` installed, a quick way to install it:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On macOS, if you prefer [brew](https://brew.sh/), you can install or upgrade uv with:

```shell
brew update
brew install uv
```

See [uv’s docs](https://docs.astral.sh/uv/getting-started/installation/) for more
installation methods and platforms.

Now you can use uv to install a current Python environment:

```shell
uv python install 3.13 # Or pick another version.
```

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
