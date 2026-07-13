from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from kpress.publish import BuildOptions, build_site

from .golden_helpers import KPRESS_ROOT, assert_yaml_matches_golden, snapshot_output_tree


def test_static_site_basic_golden(tmp_path: Path) -> None:
    fixture = KPRESS_ROOT / "tests/fixtures/sites/basic"
    site = tmp_path / "site"
    shutil.copytree(fixture, site)

    report = build_site(
        site / "kpress.yml",
        BuildOptions(asset_mode="hashed", precompress=["gzip"]),
    )

    assert report.routes == {"/": "index.html", "/about.html": "about.html"}
    actual = snapshot_output_tree(site / "public", temp_root=tmp_path)
    expected = KPRESS_ROOT / "tests/golden/accepted/static-site-basic/tree.yaml"
    assert_yaml_matches_golden(actual, expected)


def test_output_tree_snapshot_names_malformed_json(tmp_path: Path) -> None:
    output_root = tmp_path / "public"
    malformed = output_root / "data" / "broken.json"
    malformed.parent.mkdir(parents=True)
    malformed.write_text("{", encoding="utf-8")

    with pytest.raises(
        ValueError, match=r"Generated file is not valid JSON: data/broken.json"
    ) as exc:
        snapshot_output_tree(output_root)

    assert isinstance(exc.value.__cause__, json.JSONDecodeError)
