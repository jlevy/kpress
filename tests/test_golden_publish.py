from __future__ import annotations

import shutil
from pathlib import Path

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
