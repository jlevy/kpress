"""Run browserless DOM tests for KPress native browser modules."""

from __future__ import annotations

import subprocess
from pathlib import Path

from npm_tools import npx_no_install


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cmd = npx_no_install(root, "vitest", "run", "--config", "tests/js/vitest.config.mjs")
    return subprocess.run(cmd, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
