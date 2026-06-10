"""Frontmatter-driven routing and shared frontmatter/sidematter precedence.

Covers the contract end to end: discovery (read_document_source) -> routing
(public_path / public_slug overrides, collisions, reserved paths) -> render
(merged metadata) -> manifest (overridden route recorded).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kpress.errors import KPressPublishError
from kpress.publish import BuildOptions, build_site
from kpress.publish.frontmatter import read_document_source, route_override
from kpress.publish.routes import plan_site_routes


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# --- discovery: read_document_source + sidematter precedence ---------------


def test_read_document_source_strips_frontmatter_and_merges_sidematter(
    tmp_path: Path,
) -> None:
    source = _write(
        tmp_path / "doc.md",
        "---\ntitle: From Frontmatter\nauthor: Ada\n---\n# Body\n\nText.\n",
    )
    _write(tmp_path / "doc.meta.yml", "title: From Sidematter\nlicense: CC0\n")

    doc = read_document_source(source)

    # Body has no frontmatter fence; frontmatter wins over sidematter; the
    # sidematter-only key survives the merge.
    assert doc.body == "# Body\n\nText.\n"
    assert doc.metadata["title"] == "From Frontmatter"
    assert doc.metadata["author"] == "Ada"
    assert doc.metadata["license"] == "CC0"
    assert doc.frontmatter == {"title": "From Frontmatter", "author": "Ada"}
    assert doc.sidematter == {"title": "From Sidematter", "license": "CC0"}


def test_read_document_source_without_metadata_is_empty(tmp_path: Path) -> None:
    doc = read_document_source(_write(tmp_path / "plain.md", "# Plain\n\nNo metadata.\n"))

    assert doc.body == "# Plain\n\nNo metadata.\n"
    assert doc.metadata == {}
    assert doc.frontmatter == {}
    assert doc.sidematter == {}


# --- routing: route_override unit behavior ---------------------------------


def test_route_override_public_path_takes_precedence_over_slug() -> None:
    override = route_override(
        {"public_path": "/Docs/Pinned/", "public_slug": "ignored"},
        base_route="/guide/page.html",
    )
    assert override == "/docs/pinned/"


def test_route_override_public_slug_replaces_leaf_segment() -> None:
    assert route_override({"public_slug": "intro"}, base_route="/guide/page.html") == (
        "/guide/intro.html"
    )
    # An index route's slug renames its own leaf directory.
    assert route_override({"public_slug": "Intro"}, base_route="/a/guide/") == "/a/intro/"
    assert route_override({"public_slug": "home"}, base_route="/") == "/home.html"


def test_route_override_absent_or_invalid_slug_returns_none() -> None:
    assert route_override({}, base_route="/a.html") is None
    assert route_override({"public_slug": "a/b"}, base_route="/a.html") is None


# --- routing: plan_site_routes honors overrides + keeps guarantees ---------


def test_plan_site_routes_applies_override_and_output_path(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    page = _write(root / "deep" / "raw-name.md", "# X\n")

    plan = plan_site_routes(
        [(page, root)],
        tmp_path / "public",
        overrides={page: "/Pinned/Place.html"},
    )

    assert plan[0].route == "/pinned/place.html"
    assert plan[0].output_path == Path("pinned/place.html")


def test_plan_site_routes_override_collision_is_reported(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    a = _write(root / "a.md", "# A\n")
    b = _write(root / "b.md", "# B\n")

    with pytest.raises(KPressPublishError, match="collision"):
        plan_site_routes(
            [(a, root), (b, root)],
            tmp_path / "public",
            overrides={a: "/same.html", b: "/same.html"},
        )


def test_plan_site_routes_override_onto_reserved_path_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    page = _write(root / "ok.md", "# OK\n")

    with pytest.raises(KPressPublishError, match="reserved"):
        plan_site_routes(
            [(page, root)],
            tmp_path / "public",
            overrides={page: "/sitemap.xml"},
        )


# --- end to end: build_site render + manifest ------------------------------


def _config(tmp_path: Path) -> Path:
    return _write(
        tmp_path / "kpress.yml",
        "sources:\n  - path: docs\n\npublish:\n  output_dir: public\n",
    )


def test_build_site_routes_document_by_public_path(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "raw.md",
        "---\ntitle: Pinned Page\npublic_path: /pinned/place.html\n---\n# Pinned\n\nBody.\n",
    )
    report = build_site(_config(tmp_path), BuildOptions())

    out = tmp_path / "public" / "pinned" / "place.html"
    assert out.is_file()
    assert not (tmp_path / "public" / "raw.html").exists()

    html = out.read_text(encoding="utf-8")
    # Frontmatter drives the title and is no longer literal body text.
    assert "<title>Pinned Page</title>" in html
    assert "public_path" not in html.split("<body", 1)[0]

    assert report.routes["/pinned/place.html"] == "pinned/place.html"
    manifest = json.loads(
        (tmp_path / "public" / "_kpress" / "kpress-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["routes"]["/pinned/place.html"] == "pinned/place.html"


def test_build_site_routes_document_by_public_slug_with_sidematter(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "guide" / "raw-name.md",
        "---\npublic_slug: getting-started\n---\n# Guide\n\nBody.\n",
    )
    _write(tmp_path / "docs" / "guide" / "raw-name.meta.yml", "title: Guide Title\n")

    report = build_site(_config(tmp_path), BuildOptions())

    out = tmp_path / "public" / "guide" / "getting-started.html"
    assert out.is_file()
    assert not (tmp_path / "public" / "guide" / "raw-name.html").exists()
    # Sidematter title applies since frontmatter does not override it.
    assert "<title>Guide Title</title>" in out.read_text(encoding="utf-8")
    assert "/guide/getting-started.html" in report.routes


# --- end-to-end provenance: discovery → routing → render → manifest --------


def test_frontmatter_format_contract_survives_full_publish_pipeline(tmp_path: Path) -> None:
    """The shared frontmatter/sidematter contract must hold through every stage.

    A single fixture exercises: discovery (sidematter merge with frontmatter
    precedence), routing (frontmatter `public_path` override), render (merged
    metadata visible in `<title>` and social tags, with frontmatter winning on
    collisions and sidematter-only fields surviving the merge), and the manifest
    (routes dict carries the resolved overridden route, not the source-derived
    one).
    """

    _write(
        tmp_path / "docs" / "raw-stem.md",
        "---\n"
        "public_path: /reports/q3.html\n"
        "title: Q3 Earnings (frontmatter wins)\n"
        "---\n"
        "# Heading\n\nBody.\n",
    )
    _write(
        tmp_path / "docs" / "raw-stem.meta.yml",
        "title: Q3 Earnings (sidematter loses)\n"
        "description: Quarter-three earnings analysis\n"
        "author: Ada\n",
    )

    # Discovery: frontmatter and sidematter are preserved separately and
    # merged with frontmatter precedence.
    doc = read_document_source(tmp_path / "docs" / "raw-stem.md")
    assert doc.frontmatter == {
        "public_path": "/reports/q3.html",
        "title": "Q3 Earnings (frontmatter wins)",
    }
    assert doc.sidematter == {
        "title": "Q3 Earnings (sidematter loses)",
        "description": "Quarter-three earnings analysis",
        "author": "Ada",
    }
    assert doc.metadata["title"] == "Q3 Earnings (frontmatter wins)"
    assert doc.metadata["description"] == "Quarter-three earnings analysis"
    assert doc.metadata["author"] == "Ada"

    build_site(_config(tmp_path), BuildOptions())

    # Routing: frontmatter override replaces the path-derived route, and the
    # source-derived path is not emitted.
    out = tmp_path / "public" / "reports" / "q3.html"
    assert out.is_file()
    assert not (tmp_path / "public" / "raw-stem.html").exists()
    html = out.read_text(encoding="utf-8")

    # Render: merged metadata is visible — frontmatter title wins, sidematter
    # description survives the merge into the social meta tags.
    assert "<title>Q3 Earnings (frontmatter wins)</title>" in html
    assert "Q3 Earnings (sidematter loses)" not in html
    assert '<meta property="og:description" content="Quarter-three earnings analysis">' in html

    # Manifest: the resolved (overridden) route is recorded, not the source-derived path.
    manifest = json.loads(
        (tmp_path / "public" / "_kpress" / "kpress-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["routes"] == {"/reports/q3.html": "reports/q3.html"}


# --- security: public_path traversal must not escape output_dir (orig-ymsl) ---


# Empty/whitespace public_path values are not attacks — they're "no
# override declared" — and correctly fall back to the source-derived
# route. The list below is the set of values that MUST be rejected.
_ADVERSARIAL_PUBLIC_PATHS = [
    "/../escape.html",
    "/docs/../../escape.html",
    "/./x.html",
    "/a//b.html",
    "/foo\\bar.html",
    "http://evil/x.html",
    "C:/escape.html",
    "/foo/\x00null.html",
]


@pytest.mark.parametrize("public_path", _ADVERSARIAL_PUBLIC_PATHS)
def test_public_path_traversal_is_rejected_at_build(tmp_path: Path, public_path: str) -> None:
    """Adversarial frontmatter `public_path` values must fail the build with a
    KPressPublishError and must NOT create any file outside the configured
    `publish.output_dir`."""

    _write(
        tmp_path / "docs" / "bad.md",
        f"---\npublic_path: {public_path!r}\n---\n# Bad\n",
    )
    config = _config(tmp_path)

    # Snapshot the filesystem under tmp_path after fixture setup but before
    # the build so any write attributable to the build that lands outside
    # `public/` is visible as a `new_file` below.
    before = {p for p in tmp_path.rglob("*") if p.is_file()}

    with pytest.raises(KPressPublishError):
        build_site(config, BuildOptions())

    after = {p for p in tmp_path.rglob("*") if p.is_file()}
    new_files = after - before
    # The only writes allowed on a rejected build are inside publish/output_dir.
    public_dir = (tmp_path / "public").resolve()
    for new_file in new_files:
        assert new_file.resolve().is_relative_to(public_dir), (
            f"Build rejected {public_path!r} but still wrote {new_file} outside {public_dir}"
        )


def test_public_slug_traversal_is_rejected_silently(tmp_path: Path) -> None:
    """`public_slug` accepts only a leaf segment — `..` or `.` or `a/b` must
    fall back to the path-derived route, never become an override."""

    _write(
        tmp_path / "docs" / "ok.md",
        "---\npublic_slug: '..'\n---\n# OK\n",
    )
    report = build_site(_config(tmp_path), BuildOptions())
    # Falls back to the source-derived route; `..` is ignored.
    assert report.routes == {"/ok.html": "ok.html"}
