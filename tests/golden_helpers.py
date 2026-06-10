from __future__ import annotations

import json
import os
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from kpress.format import DocumentInput, RenderOptions, render_page
from kpress.format.model import TocMode

KPRESS_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class GoldenScenario:
    name: str
    title: str
    source: Path
    include_toc: str = "auto"
    toc_min_headings: int = 4


def _parse_scalar(value: str) -> str | int:
    raw = value.strip().strip('"').strip("'")
    try:
        return int(raw)
    except ValueError:
        return raw


def load_scenario(path: Path) -> GoldenScenario:
    data: dict[str, str | int] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        data[key.strip()] = _parse_scalar(value)
    source = KPRESS_ROOT / "tests" / "fixtures" / "documents" / str(data["source"])
    return GoldenScenario(
        name=str(data["name"]),
        title=str(data["title"]),
        source=source,
        include_toc=str(data.get("include_toc", "auto")),
        toc_min_headings=int(data.get("toc_min_headings", 4)),
    )


def render_scenario(scenario: GoldenScenario) -> str:
    source_text = scenario.source.read_text(encoding="utf-8")
    return render_page(
        DocumentInput(
            title=scenario.title,
            source_text=source_text,
            body_markdown=source_text,
            source_path=scenario.source.name,
        ),
        RenderOptions(
            include_toc=cast(TocMode, scenario.include_toc),
            toc_min_headings=scenario.toc_min_headings,
        ),
    ).html


def normalize_text_tree(root: Path, *, temp_root: Path | None = None) -> str:
    tree: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix()
        if path.suffix in {".gz", ".br"}:
            data = path.read_bytes()
            text = f"[binary size={len(data)} sha256={sha256(data).hexdigest()[:16]}]"
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if temp_root is not None:
                text = text.replace(str(temp_root), "[TMP]")
        tree[rel] = text
    return json.dumps(tree, indent=2, sort_keys=True) + "\n"


def assert_matches_golden(actual: str, expected_path: Path) -> None:
    if os.environ.get("KPRESS_UPDATE_GOLDENS") == "1":
        expected_path.parent.mkdir(parents=True, exist_ok=True)
        expected_path.write_text(actual, encoding="utf-8")
    expected = expected_path.read_text(encoding="utf-8")
    assert actual == expected


def assert_jsonable_matches_golden(actual: dict[str, Any], expected_path: Path) -> None:
    assert_matches_golden(json.dumps(actual, indent=2, sort_keys=True) + "\n", expected_path)
