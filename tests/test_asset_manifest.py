from __future__ import annotations

import json
from pathlib import Path

from kpress.contract import BUILD_MANIFEST_SCHEMA_VERSION
from kpress.format.assets import package_asset_manifest, package_asset_refs
from kpress.publish.cache import (
    CacheRecord,
    cache_key,
    cache_path,
    read_cache_record,
    reset_cache_bucket,
    write_cache_record,
)
from kpress.publish.manifest import BuildReport, ManifestAsset, OutputFile


def test_package_asset_manifest_uses_hashed_paths_for_production() -> None:
    refs = package_asset_refs(mode="hashed")
    manifest = package_asset_manifest(mode="hashed")

    assert refs["css"][0].startswith("css/style-tokens.")
    assert refs["css"][0].endswith(".css")
    assert manifest.assets[0].content_hash
    assert manifest.assets[0].output_path == refs["css"][0]


def test_build_report_serializes_stably(tmp_path: Path) -> None:
    report = BuildReport(
        output_dir=tmp_path,
        files=[OutputFile(path="b.html", kind="html"), OutputFile(path="a.css", kind="css")],
        assets=[
            ManifestAsset(
                path="css/a.css",
                kind="package",
                source="package",
                output_path="_kpress/assets/css/a.css",
                content_hash="abc",
            )
        ],
        routes={"/": "index.html"},
    )
    manifest = report.write_manifest()

    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["schema_version"] == BUILD_MANIFEST_SCHEMA_VERSION
    assert [item["path"] for item in data["files"]] == ["a.css", "b.html"]
    assert data["assets"][0]["output_path"] == "_kpress/assets/css/a.css"


def test_cache_records_are_deterministic(tmp_path: Path) -> None:
    key = cache_key("source", "doc.md", "v1")
    path = cache_path(tmp_path, "render", key)
    record = CacheRecord(key=key, kind="render", value={"path": "doc.md"})

    written = write_cache_record(tmp_path, "render", record)

    assert written == path
    assert read_cache_record(tmp_path, "render", key) == record
    assert reset_cache_bucket(tmp_path, "render").exists()
    assert read_cache_record(tmp_path, "render", key) is None
