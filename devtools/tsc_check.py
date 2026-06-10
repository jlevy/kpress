"""Run TypeScript checkJs over KPress native browser JavaScript."""

from __future__ import annotations

import subprocess
from pathlib import Path

from npm_tools import npx_no_install


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cmd = npx_no_install(root, "tsc", "--noEmit", "-p", "tsconfig.json")
    return subprocess.run(cmd, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
