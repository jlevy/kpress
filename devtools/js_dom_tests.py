"""Run browserless DOM tests for KPress native browser modules."""

from __future__ import annotations

import subprocess
from pathlib import Path

from npm_policy import NPM_TOOL_PINS, npm_env

VITEST_VERSION = NPM_TOOL_PINS["vitest"]
HAPPY_DOM_VERSION = NPM_TOOL_PINS["happy-dom"]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cmd = [
        "npx",
        "--yes",
        "--package",
        f"vitest@{VITEST_VERSION}",
        "--package",
        f"happy-dom@{HAPPY_DOM_VERSION}",
        "vitest",
        "run",
        "--config",
        "tests/js/vitest.config.mjs",
    ]
    return subprocess.run(cmd, cwd=root, check=False, env=npm_env()).returncode


if __name__ == "__main__":
    raise SystemExit(main())
