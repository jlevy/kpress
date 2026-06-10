"""Pinned npm tool versions and supply-chain environment for KPress devtools.

KPress's quality gate shells out to a few npm tools via ``npx`` (Biome, tsc,
vitest, happy-dom). Per SUPPLY-CHAIN-SECURITY.md, every zero-install runner
invocation must be exact-pinned and resolved behind the 14-day cool-off, which
``npm_env()`` enforces via npm's native ``min-release-age`` gate (npm 11.10+).
"""

from __future__ import annotations

import os

NPM_MIN_RELEASE_AGE_DAYS = "14"

NPM_TOOL_PINS = {
    "@biomejs/biome": "2.4.14",
    "happy-dom": "20.9.0",
    "typescript": "6.0.3",
    "vitest": "4.1.5",
}


def npm_env() -> dict[str, str]:
    """Return an environment that carries the repository npm age gate."""
    env = os.environ.copy()
    env["NPM_CONFIG_MIN_RELEASE_AGE"] = NPM_MIN_RELEASE_AGE_DAYS
    env["NPM_CONFIG_SAVE_EXACT"] = "true"
    env["NPM_CONFIG_PACKAGE_LOCK"] = "true"
    return env
