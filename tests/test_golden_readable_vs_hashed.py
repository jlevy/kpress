"""Readable-vs-hashed publishing golden."""

from __future__ import annotations

import re
from pathlib import Path

from .equivalence_helpers import (
    build_hashed_tree,
    build_readable_tree,
    readable_vs_hashed_file_categories,
)
from .golden_helpers import KPRESS_ROOT, assert_yaml_matches_golden, snapshot_output_tree

_GOLDEN_PATH = KPRESS_ROOT / "tests" / "golden" / "accepted" / "readable-vs-hashed" / "trees.yaml"

_SOURCES = {
    "index.md": "# Home\n\nIntro paragraph with a [link](#details).\n\n## Details\n\n- first item\n- second item\n",
    "about.md": "# About\n\nStatic publishing fixture.\n",
}

_CONTENT_HASH_RE = re.compile(r"\.[0-9a-f]{16}\.")


def _file_paths(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def _normalize_document_content(html: str) -> str:
    html = re.sub(r"<head>.*?</head>", "", html, flags=re.DOTALL)
    html = re.sub(
        r'<script\s+type="application/json"\s+id="kpress-diagnostics">.*?</script>',
        "",
        html,
        flags=re.DOTALL,
    )
    html = re.sub(r"\s+", " ", html)
    return html.strip()


def test_readable_and_hashed_output_trees(tmp_path: Path) -> None:
    readable_root = build_readable_tree(_SOURCES, tmp_path / "readable")
    hashed_root = build_hashed_tree(_SOURCES, tmp_path / "hashed")
    readable_files = _file_paths(readable_root)
    hashed_files = _file_paths(hashed_root)

    assert_yaml_matches_golden(
        {
            "readable": snapshot_output_tree(readable_root, temp_root=tmp_path),
            "hashed": snapshot_output_tree(hashed_root, temp_root=tmp_path),
            "categories": readable_vs_hashed_file_categories(readable_files, hashed_files),
        },
        _GOLDEN_PATH,
    )

    readable_assets = [path for path in readable_files if path.endswith((".css", ".js"))]
    hashed_assets = [
        path
        for path in hashed_files
        if path.endswith((".css", ".js")) and "_kpress/assets/" in path
    ]
    assert readable_assets and hashed_assets
    assert all(_CONTENT_HASH_RE.search(path) is None for path in readable_assets)
    assert all(_CONTENT_HASH_RE.search(path) is not None for path in hashed_assets)
    assert not any(path.endswith(".gz") for path in readable_files)
    assert any(path.endswith(".gz") for path in hashed_files)

    readable_pages = [path for path in readable_files if path.endswith(".html")]
    hashed_pages = [path for path in hashed_files if path.endswith(".html")]
    assert readable_pages
    assert readable_pages == hashed_pages
    for page in readable_pages:
        readable_html = (readable_root / page).read_text(encoding="utf-8")
        hashed_html = (hashed_root / page).read_text(encoding="utf-8")
        assert _normalize_document_content(readable_html) == _normalize_document_content(
            hashed_html
        )
