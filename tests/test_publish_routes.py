from __future__ import annotations

from pathlib import Path

import pytest

from kpress.errors import KPressPublishError
from kpress.publish import BuildOptions, build_site
from kpress.publish.routes import (
    normalize_route,
    plan_site_routes,
    validate_public_route,
    validate_public_slug,
)
from kpress.publish.site_files import write_site_files


def _touch(path: Path, text: str = "# Page\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_normalize_route_lowercases_and_keeps_leading_slash() -> None:
    assert normalize_route("/Getting-Started.html") == "/getting-started.html"
    assert normalize_route("/Guide/Index/") == "/guide/index/"
    assert normalize_route("/") == "/"


def test_plan_site_routes_maps_index_and_trailing_slash(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    home = _touch(root / "index.md")
    section = _touch(root / "guide" / "index.md")
    page = _touch(root / "about.md")

    plan = plan_site_routes([(home, root), (section, root), (page, root)], tmp_path / "public")

    by_route = {entry.route: entry for entry in plan}
    assert set(by_route) == {"/", "/guide/", "/about.html"}
    assert by_route["/"].output_path == Path("index.html")
    assert by_route["/guide/"].output_path == Path("guide/index.html")
    assert by_route["/about.html"].output_path == Path("about.html")


def test_plan_site_routes_normalizes_mixed_case_routes(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    page = _touch(root / "Getting-Started.md")

    plan = plan_site_routes([(page, root)], tmp_path / "public")

    assert plan[0].route == "/getting-started.html"
    assert plan[0].output_path == Path("getting-started.html")


def test_plan_site_routes_detects_case_insensitive_collision(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    upper = _touch(root / "Guide.md")
    lower = _touch(root / "guide.md")

    with pytest.raises(KPressPublishError) as excinfo:
        plan_site_routes([(upper, root), (lower, root)], tmp_path / "public")

    message = str(excinfo.value)
    assert "/guide.html" in message
    assert "Guide.md" in message
    assert "guide.md" in message


def test_plan_site_routes_rejects_reserved_output_path(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    reserved = _touch(root / "_kpress" / "page.md")

    with pytest.raises(KPressPublishError) as excinfo:
        plan_site_routes([(reserved, root)], tmp_path / "public")

    assert "reserved" in str(excinfo.value).lower()


def test_write_site_files_uses_absolute_urls_lastmod_and_escaping(tmp_path: Path) -> None:
    output_dir = tmp_path / "public"
    output_dir.mkdir()
    routes = {"/": "index.html", "/a&b.html": "a&b.html"}
    lastmods = {"/": "2026-05-17", "/a&b.html": "2026-05-10"}

    written = write_site_files(
        output_dir, routes, base_url="https://site.example/docs/", lastmods=lastmods
    )

    sitemap = (output_dir / "sitemap.xml").read_text(encoding="utf-8")
    robots = (output_dir / "robots.txt").read_text(encoding="utf-8")
    assert "<loc>https://site.example/docs/</loc>" in sitemap
    assert "<loc>https://site.example/docs/a&amp;b.html</loc>" in sitemap
    assert "<lastmod>2026-05-17</lastmod>" in sitemap
    assert "Sitemap: https://site.example/docs/sitemap.xml" in robots
    assert {p.name for p in written} >= {"sitemap.xml", "robots.txt"}


def test_write_site_files_omits_sitemap_without_base_url(tmp_path: Path) -> None:
    output_dir = tmp_path / "public"
    output_dir.mkdir()

    write_site_files(output_dir, {"/": "index.html"})

    robots = (output_dir / "robots.txt").read_text(encoding="utf-8")
    assert not (output_dir / "sitemap.xml").exists()
    assert "Sitemap:" not in robots


def test_write_site_files_emits_redirects_file(tmp_path: Path) -> None:
    output_dir = tmp_path / "public"
    output_dir.mkdir()

    written = write_site_files(
        output_dir,
        {"/new.html": "new.html"},
        redirects=[{"from": "/old.html", "to": "/new.html", "status": 301}],
    )

    redirects = (output_dir / "_redirects").read_text(encoding="utf-8")
    assert redirects.strip() == "/old.html /new.html 301"
    assert any(p.name == "_redirects" for p in written)


def test_build_site_emits_absolute_sitemap_and_redirects(tmp_path: Path) -> None:
    _touch(tmp_path / "docs" / "index.md", "# Home\n\nBody\n")
    config = tmp_path / "kpress.yml"
    config.write_text(
        """site:
  base_url: https://site.example/
  build_date: 2026-05-17
  redirects:
    - from: /legacy.html
      to: /
      status: 301

sources:
  - path: docs

publish:
  asset_mode: hashed
  output_dir: public
""",
        encoding="utf-8",
    )

    build_site(config, BuildOptions(asset_mode="hashed"))

    sitemap = (tmp_path / "public" / "sitemap.xml").read_text(encoding="utf-8")
    redirects = (tmp_path / "public" / "_redirects").read_text(encoding="utf-8")
    assert "<loc>https://site.example/</loc>" in sitemap
    assert "<lastmod>2026-05-17</lastmod>" in sitemap
    assert "/legacy.html / 301" in redirects


def test_package_asset_prefix_derives_from_base_url() -> None:
    from kpress.publish.build import package_asset_prefix

    assert package_asset_prefix("") == "/_kpress/assets/"
    assert package_asset_prefix("https://site.example/") == "/_kpress/assets/"
    assert package_asset_prefix("https://site.example/docs/") == "/docs/_kpress/assets/"
    assert package_asset_prefix("https://site.example/a/b") == "/a/b/_kpress/assets/"


def test_build_site_subpath_base_url_prefixes_package_assets(tmp_path: Path) -> None:
    _touch(tmp_path / "docs" / "index.md", "# Home\n\nBody\n")
    config = tmp_path / "kpress.yml"
    config.write_text(
        """site:
  base_url: https://site.example/docs/

sources:
  - path: docs

publish:
  asset_mode: hashed
  output_dir: public
""",
        encoding="utf-8",
    )

    build_site(config, BuildOptions(asset_mode="hashed"))

    public = tmp_path / "public"
    html = (public / "index.html").read_text(encoding="utf-8")
    first_css = html.split('<link rel="stylesheet" href="', 1)[1].split('"', 1)[0]
    # Subpath deployment: asset URLs live under the base-url path, and the
    # bundle is materialized at the matching tree location.
    assert first_css.startswith("/docs/_kpress/assets/")
    rel = first_css[len("/docs/") :]
    assert (public / rel).is_file()
    sitemap = (public / "sitemap.xml").read_text(encoding="utf-8")
    assert "<loc>https://site.example/docs/</loc>" in sitemap


def test_build_site_rejects_reserved_route(tmp_path: Path) -> None:
    _touch(tmp_path / "docs" / "_kpress" / "page.md")
    config = tmp_path / "kpress.yml"
    config.write_text(
        """sources:
  - path: docs

publish:
  output_dir: public
""",
        encoding="utf-8",
    )

    with pytest.raises(KPressPublishError, match="reserved"):
        build_site(config)


@pytest.mark.parametrize(
    ("raw", "match"),
    [
        ("", "non-empty"),
        ("   ", "non-empty"),
        ("/foo/..", "path-traversal"),
        ("/foo/.", "path-traversal"),
        ("/foo//bar", "empty interior"),
        ("/foo\\bar", "forbidden"),
        ("/foo\x00bar", "forbidden"),
        ("/foo\x1fbar", "forbidden"),
        ("/foo\x7fbar", "forbidden"),
        ("http://evil.example/foo", "site-root-relative"),
        ("C:/Windows/foo", "site-root-relative"),
    ],
)
def test_validate_public_route_rejects_unsafe_inputs(raw: str, match: str) -> None:
    with pytest.raises(KPressPublishError, match=match):
        validate_public_route(raw)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("/about", "/about"),
        ("about/", "/about/"),
        ("/About/Index.html", "/about/index.html"),
        ("/", "/"),
    ],
)
def test_validate_public_route_normalizes_safe_inputs(raw: str, expected: str) -> None:
    assert validate_public_route(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["", "   ", "/", "..", ".", "foo/bar"],
)
def test_validate_public_slug_skips_non_slug_values(raw: str) -> None:
    assert validate_public_slug(raw) is None


@pytest.mark.parametrize(
    "raw",
    ["foo\x00bar", "foo\x1fbar", "foo\x7fbar", "foo\\bar"],
)
def test_validate_public_slug_rejects_forbidden_chars(raw: str) -> None:
    with pytest.raises(KPressPublishError, match="forbidden"):
        validate_public_slug(raw)


def test_validate_public_slug_returns_clean_value() -> None:
    assert validate_public_slug("My-Post") == "My-Post"
    assert validate_public_slug("  /trimmed/  ") == "trimmed"
