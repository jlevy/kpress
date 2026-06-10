"""End-to-end cache-invalidation proofs for the static build (orig-aquv).

The static build output must be a pure, deterministic function of its inputs:
identical inputs reproduce identical content hashes, and any meaningful input
change (source text, render options, asset mode, optimization) propagates to a
different output hash. These tests prove invalidation without a separate cache
layer: content addressing is the invalidation contract.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from kpress.publish import BuildOptions, build_site

_CONFIG = """site:
  title: Cache Test

sources:
  - path: docs

publish:
  asset_mode: hashed
  output_dir: public
"""


def _site(tmp_path: Path, *, body: str = "# Home\n\nIntro.\n\n## Details\n\nMore.\n") -> Path:
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "index.md").write_text(body, encoding="utf-8")
    config = tmp_path / "kpress.yml"
    config.write_text(_CONFIG, encoding="utf-8")
    return config


def _page_hash(tmp_path: Path, config: Path, options: BuildOptions) -> str:
    report = build_site(config, options)
    index = next(f for f in report.files if f.path == "index.html")
    assert index.content_hash is not None
    return index.content_hash


def _asset_output_paths(tmp_path: Path, config: Path, options: BuildOptions) -> set[str]:
    report = build_site(config, options)
    return {a.output_path for a in report.assets}


def test_identical_inputs_reproduce_identical_hashes(tmp_path: Path) -> None:
    config = _site(tmp_path)
    first = _page_hash(tmp_path / "a", config, BuildOptions(asset_mode="hashed"))
    # Rebuild the same sources into a fresh output dir.
    config2 = _site(tmp_path / "again")
    second = _page_hash(
        tmp_path / "b",
        config2,
        BuildOptions(asset_mode="hashed", output_dir=tmp_path / "again" / "public"),
    )
    assert first == second


def test_source_edit_invalidates_page_hash(tmp_path: Path) -> None:
    config = _site(tmp_path, body="# Home\n\nOriginal body.\n")
    before = _page_hash(tmp_path, config, BuildOptions(asset_mode="hashed"))
    (tmp_path / "docs" / "index.md").write_text(
        "# Home\n\nEdited body with new content.\n", encoding="utf-8"
    )
    after = _page_hash(tmp_path, config, BuildOptions(asset_mode="hashed"))
    assert before != after


def test_optimizer_mode_invalidates_output(tmp_path: Path) -> None:
    from kpress.publish.optimize import full_optimizer_available

    if not full_optimizer_available():
        pytest.skip("full optimizer requires Node/npx")
    config = _site(tmp_path)
    none_hash = _page_hash(tmp_path, config, BuildOptions(asset_mode="hashed", optimizer="none"))
    full_hash = _page_hash(tmp_path, config, BuildOptions(asset_mode="hashed", optimizer="full"))
    assert none_hash != full_hash


def test_asset_mode_invalidates_asset_outputs(tmp_path: Path) -> None:
    config = _site(tmp_path)
    linked = _asset_output_paths(tmp_path, config, BuildOptions(asset_mode="linked"))
    hashed = _asset_output_paths(tmp_path, config, BuildOptions(asset_mode="hashed"))
    # Hashed mode addresses assets by content, so output paths differ from linked.
    assert linked != hashed


def test_unchanged_rebuild_is_stable_under_repeat(tmp_path: Path) -> None:
    config = _site(tmp_path)
    options = BuildOptions(asset_mode="hashed")
    first = _page_hash(tmp_path, config, options)
    # Rebuilding in place without input changes must not churn the hash.
    second = _page_hash(tmp_path, config, options)
    assert first == second


# --- stale output removal (orig-8qo4) -----------------------------------


def test_deleted_source_is_purged_from_next_build_output(tmp_path: Path) -> None:
    """A source file removed between builds must not leave its prior HTML
    behind in `output_dir`. Static publish output is a pure function of
    current inputs."""

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    (docs / "old.md").write_text("# Old\n", encoding="utf-8")
    (tmp_path / "kpress.yml").write_text(
        "sources:\n  - path: docs\npublish:\n  output_dir: public\n",
        encoding="utf-8",
    )

    build_site(tmp_path / "kpress.yml", BuildOptions())
    assert (tmp_path / "public" / "old.html").is_file()

    (docs / "old.md").unlink()
    build_site(tmp_path / "kpress.yml", BuildOptions())

    assert not (tmp_path / "public" / "old.html").exists()
    assert (tmp_path / "public" / "index.html").is_file()


def test_purge_preserves_operator_added_files(tmp_path: Path) -> None:
    """The purge only removes files KPress claimed in the prior manifest plus
    its package-owned `_kpress/` tree and named site files (sitemap/robots/
    _redirects). Operator-added files (deploy metadata, screenshots, etc.)
    are not in the manifest and must survive a rebuild."""

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    (tmp_path / "kpress.yml").write_text(
        "sources:\n  - path: docs\npublish:\n  output_dir: public\n",
        encoding="utf-8",
    )

    build_site(tmp_path / "kpress.yml", BuildOptions())
    operator_file = tmp_path / "public" / "deploy-marker.txt"
    operator_file.write_text("operator state\n", encoding="utf-8")
    nested = tmp_path / "public" / "extras" / "note.md"
    nested.parent.mkdir()
    nested.write_text("not from kpress\n", encoding="utf-8")

    build_site(tmp_path / "kpress.yml", BuildOptions())

    assert operator_file.read_text(encoding="utf-8") == "operator state\n"
    assert nested.read_text(encoding="utf-8") == "not from kpress\n"


def test_corrupt_prior_manifest_does_not_block_rebuild(tmp_path: Path) -> None:
    """A previous build manifest that is unreadable JSON must not stop the
    next build from purging the package-owned `_kpress/` tree and re-emitting
    HTML. The corrupt file is handled by ``_purge_prior_kpress_outputs``'s
    ``except (OSError, ValueError)`` branch — without that, the file walk
    would crash on every rebuild."""

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    (tmp_path / "kpress.yml").write_text(
        "sources:\n  - path: docs\npublish:\n  output_dir: public\n",
        encoding="utf-8",
    )

    # Seed a corrupt manifest from a "prior" build that crashed mid-write.
    kpress_dir = tmp_path / "public" / "_kpress"
    kpress_dir.mkdir(parents=True)
    (kpress_dir / "kpress-manifest.json").write_text("{not valid json", encoding="utf-8")
    # And a stale package asset that the wholesale wipe should clean up.
    (kpress_dir / "assets").mkdir()
    (kpress_dir / "assets" / "stale.css").write_text(".old{}", encoding="utf-8")

    build_site(tmp_path / "kpress.yml", BuildOptions())

    # The new build succeeded.
    assert (tmp_path / "public" / "index.html").is_file()
    # The stale asset is gone — the `_kpress/` wholesale wipe doesn't depend
    # on the prior manifest being parseable.
    assert not (kpress_dir / "assets" / "stale.css").exists()
    # A fresh manifest is written.
    fresh = (kpress_dir / "kpress-manifest.json").read_text(encoding="utf-8")
    assert '"schema_version": "kpress-build-manifest-v1"' in fresh
