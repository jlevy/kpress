"""Readable-vs-hashed output-tree goldens.

Builds the same canonical source in readable mode (linked assets, no
precompression) and hashed mode (content-hashed assets with explicit gzip
precompression sidecars; optimizer left at the default ``none`` so the trees
are deterministic without Node), then captures normalized output trees as
goldens. The accepted differences between readable and hashed are exactly:
content hashing in filenames, gzip precompression sidecars, and sitemap/robots
metadata files. Full minification is an explicit, Node-gated option exercised
separately, not a readable-vs-hashed default.
"""

from __future__ import annotations

from pathlib import Path

from .equivalence_helpers import (
    build_readable_tree,
    build_sealed_tree,
    readable_vs_sealed_file_categories,
)
from .golden_helpers import (
    KPRESS_ROOT,
    assert_jsonable_matches_golden,
    assert_matches_golden,
    normalize_text_tree,
)

_GOLDEN_DIR = KPRESS_ROOT / "tests" / "golden" / "accepted" / "readable-vs-hashed"

_SOURCES = {
    "index.md": "# Home\n\nIntro paragraph with a [link](#details).\n\n## Details\n\n- first item\n- second item\n",
    "about.md": "# About\n\nStatic publishing fixture.\n",
}


def test_readable_output_tree_golden(tmp_path: Path) -> None:
    readable_root = build_readable_tree(_SOURCES, tmp_path)
    actual = normalize_text_tree(readable_root, temp_root=tmp_path)
    assert_matches_golden(actual, _GOLDEN_DIR / "readable-tree.json")


def test_sealed_output_tree_golden(tmp_path: Path) -> None:
    sealed_root = build_sealed_tree(_SOURCES, tmp_path)
    actual = normalize_text_tree(sealed_root, temp_root=tmp_path)
    assert_matches_golden(actual, _GOLDEN_DIR / "hashed-tree.json")


def test_readable_vs_sealed_file_categories_golden(tmp_path: Path) -> None:
    readable_root = build_readable_tree(_SOURCES, tmp_path / "readable")
    sealed_root = build_sealed_tree(_SOURCES, tmp_path / "hashed")

    readable_files = sorted(
        p.relative_to(readable_root).as_posix() for p in readable_root.rglob("*") if p.is_file()
    )
    sealed_files = sorted(
        p.relative_to(sealed_root).as_posix() for p in sealed_root.rglob("*") if p.is_file()
    )

    categories = readable_vs_sealed_file_categories(readable_files, sealed_files)
    assert_jsonable_matches_golden(categories, _GOLDEN_DIR / "file-categories.json")


def test_sealed_has_hashed_assets(tmp_path: Path) -> None:
    sealed_root = build_sealed_tree(_SOURCES, tmp_path)
    sealed_files = sorted(
        p.relative_to(sealed_root).as_posix() for p in sealed_root.rglob("*") if p.is_file()
    )

    # Hashed CSS/JS must have content hashes in filenames.
    hashed = [f for f in sealed_files if "_kpress/assets/" in f and ".gz" not in f]
    css_js = [f for f in hashed if f.endswith((".css", ".js"))]
    import re

    hash_pattern = re.compile(r"\.[0-9a-f]{16}\.")
    for path in css_js:
        assert hash_pattern.search(path), f"expected content hash in hashed asset: {path}"


def test_sealed_has_precompressed_files(tmp_path: Path) -> None:
    sealed_root = build_sealed_tree(_SOURCES, tmp_path)
    sealed_files = sorted(
        p.relative_to(sealed_root).as_posix() for p in sealed_root.rglob("*") if p.is_file()
    )
    gz_files = [f for f in sealed_files if f.endswith(".gz")]
    assert gz_files, "hashed build must include .gz precompressed files"


def test_readable_has_readable_asset_names(tmp_path: Path) -> None:
    readable_root = build_readable_tree(_SOURCES, tmp_path)
    readable_files = sorted(
        p.relative_to(readable_root).as_posix() for p in readable_root.rglob("*") if p.is_file()
    )

    # Readable CSS/JS must have unhashed filenames.
    import re

    hash_pattern = re.compile(r"\.[0-9a-f]{16}\.")
    css_js = [f for f in readable_files if f.endswith((".css", ".js"))]
    for path in css_js:
        assert not hash_pattern.search(path), f"readable asset should not have content hash: {path}"


def test_readable_has_no_precompressed_files(tmp_path: Path) -> None:
    readable_root = build_readable_tree(_SOURCES, tmp_path)
    readable_files = sorted(
        p.relative_to(readable_root).as_posix() for p in readable_root.rglob("*") if p.is_file()
    )
    gz_files = [f for f in readable_files if f.endswith(".gz")]
    assert not gz_files, f"readable build should not include .gz files, got: {gz_files}"


def test_readable_and_sealed_share_same_document_content(tmp_path: Path) -> None:
    readable_root = build_readable_tree(_SOURCES, tmp_path / "readable")
    sealed_root = build_sealed_tree(_SOURCES, tmp_path / "hashed")

    # Both must produce the same HTML pages (by name, ignoring hashes in assets).
    readable_html = sorted(
        p.relative_to(readable_root).as_posix()
        for p in readable_root.rglob("*.html")
        if p.is_file()
    )
    sealed_html = sorted(
        p.relative_to(sealed_root).as_posix() for p in sealed_root.rglob("*.html") if p.is_file()
    )
    assert readable_html == sealed_html, (
        f"HTML pages differ: readable={readable_html}, hashed={sealed_html}"
    )

    import re

    for page in readable_html:
        readable_text = (readable_root / page).read_text(encoding="utf-8")
        sealed_text = (sealed_root / page).read_text(encoding="utf-8")

        # Strip asset URLs and whitespace to compare document structure.
        def normalize(html: str) -> str:
            html = re.sub(r"<head>.*?</head>", "", html, flags=re.DOTALL)
            html = re.sub(
                r'<style\s+data-kpress-asset="[^"]*">.*?</style>',
                "",
                html,
                flags=re.DOTALL,
            )
            html = re.sub(
                r'<script\s+type="module"\s+data-kpress-asset="[^"]*">.*?</script>',
                "",
                html,
                flags=re.DOTALL,
            )
            html = re.sub(
                r'<script\s+type="application/json"\s+id="kpress-diagnostics">.*?</script>',
                "",
                html,
                flags=re.DOTALL,
            )
            html = re.sub(
                r"<script>\s*\(\(\)\s*=>\s*\{.*?\}\)\(\);\s*</script>",
                "",
                html,
                flags=re.DOTALL,
            )
            # Collapse whitespace between tags (minification difference).
            html = re.sub(r">\s+<", "><", html)
            html = re.sub(r"\s+", " ", html).strip()
            return html

        assert normalize(readable_text) == normalize(sealed_text), (
            f"document content differs for {page}"
        )
