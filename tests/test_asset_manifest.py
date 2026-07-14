from __future__ import annotations

import json
import posixpath
import re
from pathlib import Path
from typing import cast

import pytest

from kpress.contract import BUILD_MANIFEST_SCHEMA_VERSION
from kpress.errors import KPressPublishError
from kpress.format import (
    AssetManifest,
    AssetRef,
    DocumentInput,
    RenderOptions,
    materialize_package_assets,
    render_fragment,
    render_page,
)
from kpress.format.assets import (
    DEFAULT_JS_ASSETS,
    katex_asset_manifest,
    package_asset_manifest,
    package_asset_refs,
    read_package_text,
    resolve_package_asset_manifest,
)
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


def test_render_fragment_returns_complete_resolved_asset_manifest() -> None:
    document = DocumentInput(
        title="Host contract",
        source_text="# Host contract\n\nPlain prose.",
        source_path="host-contract.md",
        body_markdown="# Host contract\n\nPlain prose.",
        trust_mode="sanitized",
    )

    rendered = render_fragment(
        document,
        RenderOptions(
            asset_mode="hashed",
            asset_url_prefix="/assets/kpress/",
            asset_policy="all",
            include_toc="off",
            widgets={"settings": "off"},
        ),
    )

    assert isinstance(rendered.assets, AssetManifest)
    assets = rendered.assets.by_id()
    stylesheet = assets["css/document.css"]
    assert stylesheet.entry_point is True
    assert stylesheet.loading == "stylesheet"
    assert stylesheet.public_url == f"/assets/kpress/{stylesheet.output_path}"
    font = assets["fonts/pt-serif-latin-400-normal.woff2"]
    assert font.entry_point is False
    assert font.loading == "resource"
    module = assets["js/theme.js"]
    assert module.entry_point is True
    assert module.loading == "module"
    dependency = assets["js/viewport.js"]
    assert dependency.entry_point is False
    assert dependency.loading == "module"
    assert rendered.assets.import_map["/assets/kpress/js/viewport.js"] == dependency.public_url


def test_math_render_manifest_includes_classic_scripts_and_font_closure() -> None:
    markdown = "# Math\n\n$$x^2$$\n"
    rendered = render_fragment(
        DocumentInput(
            title="Math",
            source_text=markdown,
            source_path="math.md",
            body_markdown=markdown,
        ),
        RenderOptions(
            asset_mode="hashed",
            asset_url_prefix="/assets/kpress/",
            asset_policy="all",
        ),
    )

    assets = rendered.assets.by_id()
    assert assets["katex/katex.min.css"].loading == "stylesheet"
    assert assets["katex/katex.min.js"].loading == "classic"
    assert assets["katex/katex.min.js"].entry_point is True
    assert assets["katex/fonts/KaTeX_Main-Regular.woff2"].loading == "resource"


def test_manifests_declare_every_relative_css_and_module_dependency() -> None:
    manifest = package_asset_manifest(
        mode="hashed",
        prefix="/assets/kpress/",
    ).merged(
        katex_asset_manifest(
            mode="hashed",
            prefix="/assets/kpress/",
        )
    )
    assets = manifest.by_id()
    css_url = re.compile(r"url\(\s*['\"]?([^'\")]+)")
    module_import = re.compile(r"(?:\bfrom\b|\bimport\b)\s*\(?\s*['\"]([^'\"]+)['\"]")

    for asset in manifest.assets:
        if asset.loading == "stylesheet":
            dependencies = css_url.findall(read_package_text(asset.path))
        elif asset.loading == "module":
            dependencies = module_import.findall(read_package_text(asset.path))
        else:
            continue
        for dependency in dependencies:
            if dependency.startswith(("data:", "http:", "https:", "/", "#")):
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(asset.path), dependency))
            assert resolved in assets, f"{asset.path} depends on undeclared {resolved}"
            if asset.loading == "module":
                natural_url = f"/assets/kpress/{resolved}"
                assert manifest.import_map[natural_url] == assets[resolved].public_url


@pytest.mark.parametrize("entry_point", DEFAULT_JS_ASSETS)
def test_selected_module_closure_contains_every_declared_import(entry_point: str) -> None:
    manifest = resolve_package_asset_manifest(
        {entry_point},
        mode="hashed",
        prefix="/assets/kpress/",
    )
    assets = manifest.by_id()
    module_import = re.compile(r"(?:\bfrom\b|\bimport\b)\s*\(?\s*['\"]([^'\"]+)['\"]")

    assert assets[entry_point].entry_point is True
    for asset in manifest.assets:
        if asset.loading != "module":
            continue
        for dependency in module_import.findall(read_package_text(asset.path)):
            if dependency.startswith(("data:", "http:", "https:", "/", "#")):
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(asset.path), dependency))
            assert resolved in assets, f"{asset.path} depends on omitted {resolved}"
            assert assets[resolved].entry_point is (resolved == entry_point)


def test_asset_manifest_serializes_typed_loading_contract() -> None:
    data = package_asset_manifest(mode="hashed", prefix="/assets/kpress/").as_dict()
    serialized_assets = cast("list[dict[str, object]]", data["assets"])
    rows = {str(row["id"]): row for row in serialized_assets}

    assert rows["css/document.css"]["entry_point"] is True
    assert rows["css/document.css"]["loading"] == "stylesheet"
    assert rows["js/viewport.js"]["entry_point"] is False
    assert rows["js/viewport.js"]["loading"] == "module"
    assert data["import_map"]


def test_manifest_union_promotes_an_asset_used_as_an_entry_point() -> None:
    theme_entry = resolve_package_asset_manifest(
        {"js/theme.js"},
        mode="hashed",
        prefix="/assets/kpress/",
    )
    theme_dependency = resolve_package_asset_manifest(
        {"js/settings-widget.js"},
        mode="hashed",
        prefix="/assets/kpress/",
    )

    merged = theme_dependency.merged(theme_entry)

    assert merged.by_id()["js/theme.js"].entry_point is True


def test_materializer_writes_and_verifies_exact_manifest(tmp_path: Path) -> None:
    manifest = package_asset_manifest(mode="hashed", prefix="/assets/kpress/")

    emitted = materialize_package_assets(manifest, tmp_path)

    assert emitted == manifest.assets
    assert sorted(
        path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()
    ) == sorted(asset.output_path for asset in manifest.assets if asset.output_path is not None)
    for asset in emitted:
        assert asset.output_path is not None
        assert (tmp_path / asset.output_path).is_file()


def test_materializer_rejects_manifest_hash_or_path_tampering(tmp_path: Path) -> None:
    original = package_asset_manifest().assets[0]
    wrong_hash = AssetManifest(
        assets=[
            AssetRef(
                id=original.id,
                kind=original.kind,
                path=original.path,
                media_type=original.media_type,
                content_hash="0" * 16,
                output_path=original.output_path,
                public_url=original.public_url,
                entry_point=original.entry_point,
                loading=original.loading,
                mode=original.mode,
            )
        ]
    )
    escaping = AssetManifest(
        assets=[
            AssetRef(
                id=original.id,
                kind=original.kind,
                path=original.path,
                media_type=original.media_type,
                content_hash=original.content_hash,
                output_path="../escape.css",
                public_url=original.public_url,
                entry_point=original.entry_point,
                loading=original.loading,
                mode=original.mode,
            )
        ]
    )

    with pytest.raises(ValueError, match="hash mismatch"):
        materialize_package_assets(wrong_hash, tmp_path)
    with pytest.raises(ValueError, match="output path"):
        materialize_package_assets(escaping, tmp_path)


def test_materializer_rejects_symlinked_output_parent(tmp_path: Path) -> None:
    manifest = package_asset_manifest()
    outside = tmp_path / "outside"
    outside.mkdir()
    destination = tmp_path / "site"
    destination.mkdir()
    (destination / "css").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink"):
        materialize_package_assets(manifest, destination)

    assert not any(outside.iterdir())


def test_auto_policy_plain_fragment_has_css_and_no_javascript() -> None:
    markdown = "# Plain\n\nNo enhanced features.\n"
    rendered = render_fragment(
        DocumentInput(
            title="Plain",
            source_text=markdown,
            source_path="plain.md",
            body_markdown=markdown,
        ),
        RenderOptions(
            include_toc="off",
            theme_mode="light",
            widgets={"settings": "off"},
        ),
    )

    assert any(asset.loading == "stylesheet" for asset in rendered.assets.assets)
    assert not any(asset.loading in {"module", "classic"} for asset in rendered.assets.assets)


def test_none_policy_returns_empty_manifest() -> None:
    markdown = "# Plain\n"
    rendered = render_fragment(
        DocumentInput(
            title="Plain",
            source_text=markdown,
            source_path="plain.md",
            body_markdown=markdown,
        ),
        RenderOptions(asset_policy="none"),
    )

    assert rendered.assets == AssetManifest()


def test_invalid_asset_policy_fails_loudly() -> None:
    from kpress.format.model import AssetPolicy

    markdown = "# Plain\n"
    with pytest.raises(KPressPublishError, match="asset policy"):
        render_fragment(
            DocumentInput(
                title="Plain",
                source_text=markdown,
                source_path="plain.md",
                body_markdown=markdown,
            ),
            RenderOptions(asset_policy=cast("AssetPolicy", "typo")),
        )


def test_auto_policy_rich_fragment_loads_only_feature_modules_and_dependencies() -> None:
    markdown = """# Data

| Item | Value |
| --- | ---: |
| Revenue | 42 |
"""
    rendered = render_fragment(
        DocumentInput(
            title="Data",
            source_text=markdown,
            source_path="data.md",
            body_markdown=markdown,
        ),
        RenderOptions(
            include_toc="off",
            theme_mode="light",
            widgets={"settings": "off"},
        ),
    )
    assets = rendered.assets.by_id()

    assert assets["js/tables.js"].entry_point is True
    assert assets["js/runtime.js"].entry_point is False
    assert "js/settings-widget.js" not in assets
    assert "js/theme.js" not in assets
    assert "js/toc.js" not in assets
    assert "js/viewport.js" not in assets


@pytest.mark.parametrize(
    ("body_html", "expected_module"),
    [
        ('<table class="custom kpress-table"><tr><td>x</td></tr></table>', "js/tables.js"),
        ('<pre class="custom kpress-code"><code>x</code></pre>', "js/code-copy.js"),
    ],
)
def test_auto_policy_detects_feature_classes_in_any_class_order(
    body_html: str,
    expected_module: str,
) -> None:
    rendered = render_fragment(
        DocumentInput(
            title="Custom classes",
            source_text="",
            source_path="custom.html",
            body_html=body_html,
        ),
        RenderOptions(
            include_toc="off",
            theme_mode="light",
            widgets={"settings": "off"},
        ),
    )

    assert rendered.assets.by_id()[expected_module].entry_point is True


def test_all_policy_includes_every_reader_module() -> None:
    markdown = "# Plain\n"
    rendered = render_fragment(
        DocumentInput(
            title="Plain",
            source_text=markdown,
            source_path="plain.md",
            body_markdown=markdown,
        ),
        RenderOptions(asset_policy="all"),
    )
    entries = {asset.path for asset in rendered.assets.browser_entry_points()}

    assert set(DEFAULT_JS_ASSETS) <= entries


def test_page_auto_policy_adds_enabled_widget_and_theme_assets() -> None:
    markdown = "# Plain\n"
    page = render_page(
        DocumentInput(
            title="Plain",
            source_text=markdown,
            source_path="plain.md",
            body_markdown=markdown,
        ),
        RenderOptions(include_toc="off"),
    )
    assets = page.assets.by_id()

    assert assets["js/settings-widget.js"].entry_point is True
    assert assets["js/theme.js"].entry_point is True
    assert "js/tables.js" not in assets


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
