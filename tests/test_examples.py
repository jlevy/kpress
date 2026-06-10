"""End-to-end tests for the bundled examples under ``examples/``.

These run each example's ``build.py`` into a scratch directory and assert the
Markdown-to-many-URLs output, so the examples stay runnable as the public API
evolves.
"""

from __future__ import annotations

import contextlib
import functools
import importlib.util
import re
import sys
import threading
import urllib.request
import zipfile
from collections.abc import Generator
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from types import ModuleType

import pytest

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _load(name: str, path: Path) -> ModuleType:
    """Load an example's build.py under a unique module name."""

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclass annotation resolution (which looks the
    # module up in sys.modules) works under `from __future__ import annotations`.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_static_site_example_builds_multiple_urls(tmp_path: Path) -> None:
    build_mod = _load("example_static_build", EXAMPLES / "static-site" / "build.py")
    report = build_mod.build(tmp_path)

    # One Markdown tree -> several published URLs, including a frontmatter
    # `public_path` override (/reference/api/).
    assert report.routes == {
        "/": "index.html",
        "/guides/getting-started.html": "guides/getting-started.html",
        "/guides/markdown-features.html": "guides/markdown-features.html",
        "/reference/api/": "reference/api/index.html",
    }
    for output_path in report.routes.values():
        assert (tmp_path / output_path).is_file()

    # KPress owns the whole page: a complete <html> doc with its asset bundle.
    home = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "<!doctype html>" in home.lower()
    assert 'class="kpress' in home
    assert (tmp_path / "_kpress" / "kpress-manifest.json").is_file()
    assert any((tmp_path / "_kpress").rglob("*.css"))
    assert any((tmp_path / "_kpress").rglob("*.woff2"))


def test_wrapped_site_example_embeds_fragments(tmp_path: Path) -> None:
    build_mod = _load("example_wrapped_build", EXAMPLES / "wrapped-site" / "build.py")
    routes = build_mod.build(tmp_path)

    assert set(routes) == {
        "/",
        "/docs/installation/",
        "/docs/configuration/",
        "/blog/announcing/",
    }

    for url, output_path in routes.items():
        page = (tmp_path / output_path).read_text(encoding="utf-8")
        # Every page carries BOTH the outer shell and an embedded KPress
        # fragment. That is the wrapper pattern.
        assert "shell__sidebar" in page, f"{url} missing outer chrome"
        assert 'class="kpress' in page, f"{url} missing embedded KPress fragment"

    # KPress's asset bundle is self-hosted by the wrapper, fonts included.
    assert any((tmp_path / "assets" / "kpress" / "fonts").glob("*.woff2"))

    # Per-page asset sets: only the page with math pulls in KaTeX.
    announce = (tmp_path / "blog" / "announcing" / "index.html").read_text(encoding="utf-8")
    home = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "katex" in announce
    assert "katex" not in home

    # No dangling asset links anywhere in the built site.
    for html in tmp_path.rglob("*.html"):
        for ref in re.findall(r'(?:href|src)="(/assets/kpress/[^"]+)"', html.read_text()):
            assert (tmp_path / ref.lstrip("/")).is_file(), f"broken asset link {ref}"

    # The injected <script type="module"> entry points import transitive
    # modules (overlay.js, viewport.js) that are NOT in the injected list. The
    # wrapper must serve the whole import graph or the browser 404s on them.
    js_dir = tmp_path / "assets" / "kpress" / "js"
    assert (js_dir / "overlay.js").is_file(), "transitive module overlay.js not copied"
    assert (js_dir / "viewport.js").is_file(), "transitive module viewport.js not copied"
    for module in js_dir.glob("*.js"):
        for spec in _ESM_IMPORT_RE.findall(module.read_text(encoding="utf-8")):
            if spec.startswith((".", "/")) and not spec.startswith(("http", "data:")):
                target = (module.parent / spec).resolve()
                assert target.is_file(), f"{module.name} imports missing module {spec}"


_ESM_IMPORT_RE = re.compile(r"""(?:\bfrom\b|\bimport\b)\s*\(?\s*['"]([^'"]+)['"]""")


def test_wrapped_site_zip_bundles_transitive_assets(tmp_path: Path) -> None:
    """The uploadable --zip archive must contain the full asset graph, not just
    the injected top-level modules."""

    build_mod = _load("example_wrapped_zip", EXAMPLES / "wrapped-site" / "build.py")
    build_mod.build(tmp_path)
    archive = build_mod.package_zip(tmp_path, tmp_path.parent / "wrapped-zip-test.zip")

    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
    # Transitive ESM modules and fonts must ride along in the archive.
    assert "assets/kpress/js/overlay.js" in names
    assert "assets/kpress/js/viewport.js" in names
    assert "assets/kpress/js/toc.js" in names
    assert any(n.startswith("assets/kpress/fonts/") and n.endswith(".woff2") for n in names)
    # Every relative import inside a bundled module must also be in the archive.
    js_modules = [n for n in names if n.startswith("assets/kpress/js/") and n.endswith(".js")]
    with zipfile.ZipFile(archive) as zf:
        for name in js_modules:
            source = zf.read(name).decode("utf-8")
            base = PurePosixPath(name).parent
            for spec in _ESM_IMPORT_RE.findall(source):
                if spec.startswith(".") and not spec.startswith(("http", "data:")):
                    resolved = (base / spec).as_posix()
                    # Normalize any ./ or ../ segments.
                    parts: list[str] = []
                    for segment in PurePosixPath(resolved).parts:
                        if segment == "..":
                            parts.pop()
                        elif segment != ".":
                            parts.append(segment)
                    assert "/".join(parts) in names, f"{name} imports unbundled {spec}"


@contextlib.contextmanager
def _serve(directory: Path) -> Generator[str, None, None]:
    """Serve ``directory`` on an ephemeral port for the duration of the block."""

    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(directory))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def _get(base_url: str, path: str) -> tuple[int, bytes]:
    with urllib.request.urlopen(base_url + path, timeout=5) as response:  # noqa: S310 (localhost)
        return response.status, response.read()


@pytest.mark.parametrize(
    ("module_name", "build_path"),
    [
        ("example_static_nav", EXAMPLES / "static-site" / "build.py"),
        ("example_wrapped_nav", EXAMPLES / "wrapped-site" / "build.py"),
    ],
)
def test_built_site_is_navigable_over_http(
    tmp_path: Path, module_name: str, build_path: Path
) -> None:
    """End to end: serve the built site and crawl every internal link + asset."""

    build_mod = _load(module_name, build_path)
    build_mod.build(tmp_path)

    with _serve(tmp_path) as base_url:
        status, home = _get(base_url, "/")
        assert status == 200
        assert b'class="kpress' in home, "home page is missing the rendered document"

        # Follow every site-absolute reference on the home page (navigation
        # links, cross-page links, and asset URLs) and require each to load.
        refs = sorted(set(re.findall(rb'(?:href|src)="(/[^"#]*)"', home)))
        assert refs, "home page has no internal links to navigate"
        for ref in refs:
            ref_status, _ = _get(base_url, ref.decode())
            assert ref_status == 200, f"{ref!r} did not serve (status {ref_status})"
