"""Workspace layout for local KPress workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class WorkflowResult:
    """Result returned by local document workflow APIs."""

    command: str
    work_root: Path
    outputs: list[Path] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "command": self.command,
            "work_root": str(self.work_root),
            "outputs": [str(path) for path in self.outputs],
            "diagnostics": list(self.diagnostics),
        }


WORK_ROOT_MARKER = ".kpress-work-root"
"""Marker file written into every KPress work root. ``kpress clean`` refuses to
remove a ``--work-root`` directory that carries neither this marker nor the
default ``.kpress`` name, so a mistyped path can never delete unrelated files."""


def prepare_work_root(work_root: Path | str = ".kpress") -> Path:
    """Create the local KPress workspace root."""

    root = Path(work_root)
    for child in ("cache", "workspace", "exports", "assets"):
        (root / child).mkdir(parents=True, exist_ok=True)
    (root / WORK_ROOT_MARKER).touch()
    return root
