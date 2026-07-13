from __future__ import annotations

from pathlib import Path

import pytest

from kpress.errors import KPressPublishError
from kpress.publish import KPressConfig, PublishConfig, SourceConfig, build_site
from kpress.publish.discover import discover_sources, discover_static_files


def test_recursive_excludes_cover_every_descendant(tmp_path: Path) -> None:
    content = tmp_path / "content"
    (content / "public" / "nested").mkdir(parents=True)
    (content / "public" / "nested" / "leak.md").write_text("# leak\n", encoding="utf-8")
    (content / "public" / "nested" / "leak.txt").write_text("leak\n", encoding="utf-8")
    (content / "keep").mkdir()
    kept_doc = content / "keep" / "page.md"
    kept_static = content / "keep" / "asset.txt"
    kept_doc.write_text("# kept\n", encoding="utf-8")
    kept_static.write_text("kept\n", encoding="utf-8")
    config = KPressConfig(
        base_dir=tmp_path,
        sources=[
            SourceConfig(
                path="content",
                include=["**/*.md"],
                exclude=["public/**"],
                static=["**/*.txt"],
            )
        ],
    )

    assert discover_sources(config) == [kept_doc]
    assert discover_static_files(config) == [(kept_static, content)]


def test_unmatched_source_fails_instead_of_using_an_unrelated_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configured = tmp_path / "configured"
    configured.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("# outside\n", encoding="utf-8")
    config = KPressConfig(
        base_dir=tmp_path,
        sources=[SourceConfig(path="configured")],
        publish=PublishConfig(output_dir=tmp_path / "public"),
    )

    def discover_outside(_config: KPressConfig) -> list[Path]:
        return [outside]

    monkeypatch.setattr("kpress.publish.build.discover_sources", discover_outside)

    with pytest.raises(KPressPublishError) as excinfo:
        build_site(config)

    message = str(excinfo.value)
    assert str(outside) in message
    assert str(configured) in message
