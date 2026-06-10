"""Run the pinned Biome formatter/linter for KPress browser assets.

Biome resolves from the committed package-lock.json (`npm ci` / `make install`);
`--no-install` means it can never fetch an unpinned version at run time.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from npm_tools import npx_no_install


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parents[1]
    return subprocess.run(npx_no_install(root, "biome", *args), cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
