"""KPress package version.

The canonical version comes from the git tag via uv-dynamic-versioning at
build time; at runtime it is read from the installed package metadata.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("kpress")
except PackageNotFoundError:  # Source tree without an installed distribution.
    __version__ = "0.0.0+unknown"
