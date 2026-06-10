"""Run TypeScript checkJs over KPress native browser JavaScript."""

from __future__ import annotations

import subprocess
from pathlib import Path

from npm_policy import NPM_TOOL_PINS, npm_env

TYPESCRIPT_VERSION = NPM_TOOL_PINS["typescript"]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cmd = [
        "npx",
        "--yes",
        "--package",
        f"typescript@{TYPESCRIPT_VERSION}",
        "tsc",
        "--noEmit",
        "-p",
        "tsconfig.json",
    ]
    return subprocess.run(cmd, cwd=root, check=False, env=npm_env()).returncode


if __name__ == "__main__":
    raise SystemExit(main())
