from __future__ import annotations

import json
import os
from dataclasses import dataclass
from hashlib import sha256
from io import StringIO
from pathlib import Path
from typing import cast

from frontmatter_format import custom_key_sort, new_yaml, read_yaml_file

from kpress.format import DocumentInput, RenderOptions, render_page
from kpress.format.model import TocMode
from kpress.output import write_text_atomic

KPRESS_ROOT = Path(__file__).resolve().parents[1]

_PACKAGE_ASSET_PREFIX = "_kpress/assets/"
_BINARY_SUFFIXES = frozenset({".br", ".gz"})
# Match the digest width used by KPress asset filenames and manifests.
_SHA256_PREFIX_LENGTH = 16
# Keep paths on one line so ruamel's wrapped scalars do not add diff-hostile whitespace.
_YAML_LINE_WIDTH = 4096
_GOLDEN_KEY_SORT = custom_key_sort(
    ["readable", "hashed", "categories", "files", "json", "text", "bytes", "sha256_16"]
)


@dataclass(frozen=True)
class GoldenScenario:
    name: str
    title: str
    source: Path
    include_toc: str = "auto"
    toc_min_headings: int = 4


def load_scenario(path: Path) -> GoldenScenario:
    raw = read_yaml_file(path)
    if not isinstance(raw, dict):
        raise TypeError(f"Golden scenario must be a YAML mapping: {path}")
    data = cast("dict[str, object]", raw)
    source = KPRESS_ROOT / "tests" / "fixtures" / "documents" / str(data["source"])
    return GoldenScenario(
        name=str(data["name"]),
        title=str(data["title"]),
        source=source,
        include_toc=str(data.get("include_toc", "auto")),
        toc_min_headings=int(cast("int | str", data.get("toc_min_headings", 4))),
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


def snapshot_output_tree(root: Path, *, temp_root: Path | None = None) -> dict[str, object]:
    """Capture generated text while summarizing copied package assets and binary files."""

    files: dict[str, object] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = None

        if rel.startswith(_PACKAGE_ASSET_PREFIX) or path.suffix in _BINARY_SUFFIXES or text is None:
            files[rel] = {
                "bytes": len(data),
                "sha256_16": sha256(data).hexdigest()[:_SHA256_PREFIX_LENGTH],
            }
            continue

        if temp_root is not None:
            text = text.replace(str(temp_root), "[TMP]")
        if path.suffix == ".json":
            files[rel] = {"json": cast("object", json.loads(text))}
        else:
            files[rel] = {"text": text}
    return {"files": files}


def assert_matches_golden(actual: str, expected_path: Path) -> None:
    if os.environ.get("KPRESS_UPDATE_GOLDENS") == "1":
        write_text_atomic(expected_path, actual)
    expected = expected_path.read_text(encoding="utf-8")
    assert actual == expected


def assert_yaml_matches_golden(actual: object, expected_path: Path) -> None:
    stream = StringIO()
    yaml = new_yaml(key_sort=_GOLDEN_KEY_SORT, typ="rt")
    yaml.width = _YAML_LINE_WIDTH
    yaml.dump(actual, stream)  # pyright: ignore[reportUnknownMemberType]
    serialized = stream.getvalue()
    if os.environ.get("KPRESS_UPDATE_GOLDENS") == "1":
        write_text_atomic(expected_path, serialized)
    expected = expected_path.read_text(encoding="utf-8")
    assert serialized == expected
