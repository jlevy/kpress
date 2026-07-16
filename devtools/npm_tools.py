"""Shared helper for invoking the pinned npm toolchain.

All JS tools (Biome, tsc, vitest, lefthook) are exact-pinned devDependencies in
package.json with a committed package-lock.json, per SUPPLY-CHAIN-SECURITY.md.
Devtools invoke them with `npx --no-install` so nothing is ever fetched at run
time; a missing node_modules fails fast with the fix.
"""

from __future__ import annotations

import sys
from pathlib import Path


def npx_no_install(root: Path, tool: str, *args: str) -> list[str]:
    """Build an `npx --no-install` command, failing clearly if deps are absent."""
    if not (root / "node_modules" / ".bin").is_dir():
        print(
            "node_modules is missing; run `make install` first.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return ["npx", "--no-install", tool, *args]
