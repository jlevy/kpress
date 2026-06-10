"""Run the pinned Biome formatter/linter for KPress browser assets."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from npm_policy import NPM_TOOL_PINS, npm_env

BIOME_VERSION = NPM_TOOL_PINS["@biomejs/biome"]


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parents[1]
    cmd = [
        "npx",
        "--yes",
        "--package",
        f"@biomejs/biome@{BIOME_VERSION}",
        "biome",
        *args,
    ]
    return subprocess.run(cmd, cwd=root, check=False, env=npm_env()).returncode


if __name__ == "__main__":
    raise SystemExit(main())
