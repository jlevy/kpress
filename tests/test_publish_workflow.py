from __future__ import annotations

import re
from pathlib import Path

import pytest

from kpress.publish import BuildOptions, build_site
from kpress.workflow import export_document, format_document


def test_sealed_build_has_no_eager_external_asset_refs(tmp_path: Path) -> None:
    """A sealed build must not load external assets at page load. Author hyperlinks
    (`<a href>`) to external sites are content, not eager loads, and stay allowed."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(
        "# Sealed\n\nAn [external link](https://example.com) stays a link.\n\n"
        "A video: [watch](https://www.youtube.com/watch?v=dQw4w9WgXcQ).\n",
        encoding="utf-8",
    )
    config = tmp_path / "kpress.yml"
    config.write_text(
        "site:\n  title: Sealed\n\nsources:\n  - path: docs\n\npublish:\n"
        "  output_dir: public\n  asset_mode: sealed\n",
        encoding="utf-8",
    )

    build_site(config, BuildOptions(asset_mode="sealed"))

    html = (tmp_path / "public" / "index.html").read_text(encoding="utf-8")
    # No eager external ASSET refs: src/href to http(s) on script/link/img/iframe.
    eager_external = re.findall(
        r'<(?:script|link|img|iframe)\b[^>]*\b(?:src|href)="https?://[^"]+"', html
    )
    assert eager_external == [], f"sealed build loads external assets: {eager_external}"
    # The author hyperlink is preserved (content, not an asset load).
    assert 'href="https://example.com"' in html


def test_build_site_writes_static_tree(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Home\n\nBody\n", encoding="utf-8")
    config = tmp_path / "kpress.yml"
    config.write_text(
        """site:
  title: Test

sources:
  - path: docs

publish:
  output_dir: public
""",
        encoding="utf-8",
    )

    report = build_site(config)

    assert (tmp_path / "public" / "index.html").exists()
    assert (tmp_path / "public" / "_kpress" / "kpress-manifest.json").exists()
    assert report.routes == {"/": "index.html"}


def test_build_site_collects_document_image_assets(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    (docs / "assets").mkdir(parents=True)
    (docs / "assets" / "logo.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>\n',
        encoding="utf-8",
    )
    # An off-tree file that a malicious ref must not be able to exfiltrate.
    (tmp_path / "secret.png").write_bytes(b"secret")
    (docs / "index.md").write_text(
        "# Home\n\n![Logo](assets/logo.svg)\n\n![Bad](../secret.png)\n",
        encoding="utf-8",
    )
    config = tmp_path / "kpress.yml"
    config.write_text(
        "site:\n  title: Test\n\nsources:\n  - path: docs\n\npublish:\n  output_dir: public\n",
        encoding="utf-8",
    )

    report = build_site(config)

    copied = tmp_path / "public" / "assets" / "logo.svg"
    assert copied.is_file(), "referenced document image should be copied into the output"
    # A ref that escapes the output tree (../secret.png) is never written into it.
    assert not (tmp_path / "public" / "secret.png").exists()
    # The collected asset is tracked in the build manifest.
    assert any(file.path == "assets/logo.svg" for file in report.files)


def test_build_site_routes_multiple_source_roots_independently(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "notes").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Home\n", encoding="utf-8")
    (tmp_path / "notes" / "index.md").write_text("# Notes\n", encoding="utf-8")
    config = tmp_path / "kpress.yml"
    config.write_text(
        """site:
  title: Test

sources:
  - path: docs
  - path: notes

publish:
  output_dir: public
""",
        encoding="utf-8",
    )

    report = build_site(config)

    assert report.routes == {"/": "index.html", "/notes/": "notes/index.html"}
    assert (tmp_path / "public" / "index.html").exists()
    assert (tmp_path / "public" / "notes" / "index.html").exists()


def test_production_has_no_implicit_optimizer_or_precompression(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Home\n\nBody\n", encoding="utf-8")
    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: docs\n\npublish:\n  output_dir: public\n",
        encoding="utf-8",
    )

    report = build_site(config, BuildOptions(asset_mode="hashed"))

    # No implicit behavior: production neither minifies nor emits sidecars
    # unless explicitly asked. Optimizer mode defaults to "none".
    assert report.as_dict().get("optimizer_backend") is None
    assert not any(f.path.endswith((".gz", ".br")) for f in report.files)


def test_build_site_renders_remote_video_iframes_as_offline_placeholders(
    tmp_path: Path,
) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text(
        '# Home\n\n<iframe src="https://www.youtube.com/embed/demo" title="Demo"></iframe>\n',
        encoding="utf-8",
    )
    config = tmp_path / "kpress.yml"
    config.write_text(
        """sources:
  - path: docs

publish:
  asset_mode: hashed
  output_dir: public
""",
        encoding="utf-8",
    )

    build_site(config)

    html = (tmp_path / "public" / "index.html").read_text(encoding="utf-8")
    # YouTube iframes are transformed into offline-safe placeholders at render
    # time (not via the deleted seal pass); the iframe element must be gone.
    assert "<iframe src=" not in html
    assert 'data-kpress-video-id="demo"' in html


def test_build_site_inline_asset_mode_inlines_package_css_and_js(tmp_path: Path) -> None:
    # `inline` is config-rejected until truly self-contained (orig-7ehk);
    # the programmatic BuildOptions override remains for the equivalence
    # harness and the future single-file work, exercised here.
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Home\n\nBody\n", encoding="utf-8")
    config = tmp_path / "kpress.yml"
    config.write_text(
        """sources:
  - path: docs

publish:
  output_dir: public
""",
        encoding="utf-8",
    )

    report = build_site(config, BuildOptions(asset_mode="inline"))

    html = (tmp_path / "public" / "index.html").read_text(encoding="utf-8")
    assert '<style data-kpress-asset="css/style-tokens.css">' in html
    assert '<script type="module" data-kpress-asset="js/theme.js">' in html
    assert 'href="/_kpress/assets/css/' not in html
    assert 'src="/_kpress/assets/js/' not in html
    assert (tmp_path / "public" / "_kpress" / "assets" / "fonts").exists()
    assert any(asset.output_path == "inline:css/style-tokens.css" for asset in report.assets)
    assert any(asset.output_path == "inline:js/theme.js" for asset in report.assets)


def test_build_site_hashes_package_css_js_and_writes_precompressed_sidecars(
    tmp_path: Path,
) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Home\n\nBody\n", encoding="utf-8")
    config = tmp_path / "kpress.yml"
    config.write_text(
        """sources:
  - path: docs

publish:
  asset_mode: hashed
  output_dir: public
""",
        encoding="utf-8",
    )

    report = build_site(config, BuildOptions(asset_mode="hashed", precompress=["gzip"]))

    js_asset = next(asset for asset in report.assets if asset.path == "js/theme.js")
    css_asset = next(asset for asset in report.assets if asset.path == "css/document.css")
    html = (tmp_path / "public" / "index.html").read_text(encoding="utf-8")
    assert f"/{js_asset.output_path}" in html
    assert f"/{css_asset.output_path}" in html
    # Content-addressed hashing: the hash is in the output path.
    assert js_asset.content_hash in js_asset.output_path
    assert css_asset.content_hash in css_asset.output_path
    # Explicit precompression wrote a deterministic gzip sidecar.
    assert any(file.path == f"{js_asset.output_path}.gz" for file in report.files)


def test_dynamic_and_static_outputs_preserve_document_surface(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    source = "# Home\n\nIntro with [link](#details).\n\n## Details\n\n- item\n"
    (tmp_path / "docs" / "index.md").write_text(source, encoding="utf-8")
    config = tmp_path / "kpress.yml"
    config.write_text(
        """sources:
  - path: docs

publish:
  asset_mode: hashed
  output_dir: public
""",
        encoding="utf-8",
    )

    build_site(config, BuildOptions(asset_mode="hashed"))

    dynamic = format_document(tmp_path / "docs" / "index.md", work_root=tmp_path / ".kpress")
    static_html = (tmp_path / "public" / "index.html").read_text(encoding="utf-8")
    dynamic_html_path = next(path for path in dynamic.outputs if path.suffix == ".html")
    dynamic_html = dynamic_html_path.read_text(encoding="utf-8")

    def normalize_document_surface(html: str) -> str:
        html = re.sub(r"<head>.*?</head>", "", html, flags=re.DOTALL)
        html = re.sub(r"\s+", " ", html)
        return html

    assert not dynamic.diagnostics
    assert '<h1 id="home">Home</h1>' in static_html
    assert '<h2 id="details">Details</h2>' in static_html
    assert normalize_document_surface(static_html).count(
        "Intro with"
    ) == normalize_document_surface(dynamic_html).count("Intro with")


def test_workflow_format_and_export_html_pdf(tmp_path: Path) -> None:
    source = tmp_path / "doc.md"
    source.write_text("# Doc\n\nBody\n", encoding="utf-8")
    work_root = tmp_path / ".kpress"

    formatted = format_document(source, work_root=work_root)
    exported = export_document(
        source,
        html=tmp_path / "out" / "doc.html",
        pdf=tmp_path / "out" / "doc.pdf",
        work_root=work_root,
    )

    assert any(path.name == "doc.html" for path in formatted.outputs)
    assert (tmp_path / "out" / "doc.html").exists()
    assert (tmp_path / "out" / "doc.pdf").read_bytes().startswith(b"%PDF")
    assert exported.diagnostics == []

    # The formatted/exported HTML references ./_kpress/assets; that bundle must
    # be emitted beside the HTML so the document opens without an asset server.
    formatted_html_dir = next(p for p in formatted.outputs if p.suffix == ".html").parent
    formatted_html = (formatted_html_dir / "doc.html").read_text(encoding="utf-8")
    assert "./_kpress/assets/" in formatted_html
    first_css = formatted_html.split('<link rel="stylesheet" href="', 1)[1].split('"', 1)[0]
    assert first_css.startswith("./_kpress/assets/")
    assert (formatted_html_dir / first_css[2:]).is_file()
    assert any(p.name == "style-tokens.css" for p in formatted.outputs)
    assert (tmp_path / "out" / "_kpress" / "assets" / "css" / "document.css").is_file()


def test_workflow_format_export_have_no_dangling_kpress_refs(tmp_path: Path) -> None:
    """Every ./_kpress/assets URL the formatted and exported HTML references
    must resolve to a real file beside the HTML, so a single-doc format/export
    opens offline with zero dangling assets (orig-quj4).
    """
    source = tmp_path / "doc.md"
    source.write_text("# Doc\n\nBody with `code` and a [link](https://x.test).\n", encoding="utf-8")
    work_root = tmp_path / ".kpress"

    formatted = format_document(source, work_root=work_root)
    exported = export_document(source, html=tmp_path / "out" / "doc.html", work_root=work_root)

    ref_pattern = re.compile(r'(?:href|src)="(\./_kpress/assets/[^"]+)"')

    def assert_no_dangling(html_path: Path) -> list[str]:
        html = html_path.read_text(encoding="utf-8")
        refs = ref_pattern.findall(html)
        # A standalone document must pull in at least its CSS and JS bundle.
        assert refs, f"no ./_kpress/assets refs in {html_path}"
        for ref in refs:
            target = html_path.parent / ref[2:]
            assert target.is_file(), f"dangling asset {ref} for {html_path}"
        return refs

    formatted_html = next(p for p in formatted.outputs if p.suffix == ".html")
    exported_html = next(p for p in exported.outputs if p.suffix == ".html")
    formatted_refs = assert_no_dangling(formatted_html)
    exported_refs = assert_no_dangling(exported_html)

    # Both entry points reference the same package bundle layout.
    assert set(formatted_refs) == set(exported_refs)
    # No absolute /_kpress or remote asset-server URL leaks into a local doc.
    assert "/_kpress/assets/" not in formatted_html.read_text(encoding="utf-8").replace(
        "./_kpress/assets/", ""
    )


# --- invalid config values must raise, not silently downgrade (orig-1tkb) -


def test_invalid_publish_asset_mode_raises(tmp_path: Path) -> None:
    from kpress.errors import KPressPublishError
    from kpress.publish.config import load_config

    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: .\npublish:\n  asset_mode: typo\n",
        encoding="utf-8",
    )
    with pytest.raises(KPressPublishError, match="asset_mode"):
        load_config(config)


def test_invalid_optimizer_mode_raises(tmp_path: Path) -> None:
    from kpress.errors import KPressPublishError
    from kpress.publish.config import load_config

    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: .\noptimizer:\n  mode: aggressive\n",
        encoding="utf-8",
    )
    with pytest.raises(KPressPublishError, match="optimizer.mode"):
        load_config(config)


def test_format_widgets_parses_normalizes_and_defaults_empty(tmp_path: Path) -> None:
    from kpress.publish.config import load_config

    default = load_config(tmp_path / "missing.yml")
    assert default.format.widgets == {}

    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: .\n"
        "format:\n  widgets:\n"
        "    settings:\n      choosers: [theme, reading-font]\n"
        "    toc: auto\n"
        "    minimap: off\n"
        "    extra: true\n",
        encoding="utf-8",
    )
    widgets = load_config(config).format.widgets
    # Dict config passes through verbatim; presence scalars normalize to strings.
    assert widgets["settings"] == {"choosers": ["theme", "reading-font"]}
    assert widgets["toc"] == "auto"
    assert widgets["minimap"] == "off"
    assert widgets["extra"] == "on"


def test_format_widgets_invalid_value_raises(tmp_path: Path) -> None:
    from kpress.errors import KPressPublishError
    from kpress.publish.config import load_config

    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: .\nformat:\n  widgets:\n    settings: 42\n",
        encoding="utf-8",
    )
    with pytest.raises(KPressPublishError, match="format.widgets"):
        load_config(config)


def test_invalid_format_math_raises(tmp_path: Path) -> None:
    from kpress.errors import KPressPublishError
    from kpress.publish.config import load_config

    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: .\nformat:\n  math: katex\n",
        encoding="utf-8",
    )
    with pytest.raises(KPressPublishError, match="format.math"):
        load_config(config)


def test_invalid_precompress_method_raises(tmp_path: Path) -> None:
    from kpress.errors import KPressPublishError
    from kpress.publish.config import load_config

    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: .\noptimizer:\n  precompress: [snappy]\n",
        encoding="utf-8",
    )
    with pytest.raises(KPressPublishError, match="precompress"):
        load_config(config)


def test_omitted_enum_values_still_use_defaults(tmp_path: Path) -> None:
    """Lenient defaults for OMITTED values only — provided-but-invalid fails."""

    from kpress.publish.config import load_config

    config = tmp_path / "kpress.yml"
    config.write_text("sources:\n  - path: .\n", encoding="utf-8")
    cfg = load_config(config)
    assert cfg.publish.asset_mode == "linked"
    assert cfg.optimizer.mode == "none"
    assert cfg.format.math == "auto"
    assert cfg.optimizer.precompress == []


def test_external_and_local_refs_pass_through_verbatim(tmp_path: Path) -> None:
    """Spec acceptance: post-seal-removal, document-local and external asset
    URLs are emitted into the rendered HTML verbatim; the deploy layer
    owns delivery. Only KPress's own package assets land in ``_kpress/``.
    See ``docs/project/specs/active/plan-2026-05-21-kpress-remove-sealing-for-v1.md``.

    Uses ``<img>`` tags (which survive the publish sanitizer) for both
    local and external refs — the point of this test is the *fetch/seal*
    behavior, not active-content sanitization (which is its own contract).
    """

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(
        "# Sample\n\n"
        '<img src="./local-image.png" alt="local">\n'
        '<img src="https://cdn.example.com/photo.png" alt="external">\n',
        encoding="utf-8",
    )
    (tmp_path / "kpress.yml").write_text(
        "sources:\n  - path: docs\npublish:\n  output_dir: public\n",
        encoding="utf-8",
    )

    build_site(tmp_path / "kpress.yml", BuildOptions())

    rendered = (tmp_path / "public" / "index.html").read_text(encoding="utf-8")
    # Document-local ref: emitted verbatim, NOT rewritten to a sealed path.
    assert 'src="./local-image.png"' in rendered
    # External ref: emitted verbatim, NOT fetched or hashed into _kpress/.
    assert 'src="https://cdn.example.com/photo.png"' in rendered
    # Package assets still land under _kpress/assets/.
    assert (tmp_path / "public" / "_kpress" / "assets").is_dir()
    # And the external image is NOT fetched into the tree.
    fetched_photos = list((tmp_path / "public").rglob("photo.png"))
    assert not fetched_photos


def test_unknown_top_level_config_key_is_rejected(tmp_path: Path) -> None:
    """Stale ``assets:`` block (or any unknown top-level key) raises rather
    than being silently dropped — see ``_reject_unknown_keys`` in
    ``publish/config.py``. Silent drop would be a security regression for
    users relying on the (now-removed) external-asset allowlist.
    """

    from kpress.errors import KPressPublishError
    from kpress.publish.config import load_config

    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: .\nassets:\n  external:\n    allowlist: [https://cdn.example/]\n",
        encoding="utf-8",
    )
    with pytest.raises(KPressPublishError, match=r"assets"):
        load_config(config)


def test_unknown_publish_subkey_is_rejected(tmp_path: Path) -> None:
    """Removed sealing fields (``strict_assets``, ``external_fetcher``, etc.)
    under ``publish:`` raise on load. Same rationale as the top-level guard.
    """

    from kpress.errors import KPressPublishError
    from kpress.publish.config import load_config

    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: .\npublish:\n  output_dir: public\n  strict_assets: true\n",
        encoding="utf-8",
    )
    with pytest.raises(KPressPublishError, match=r"strict_assets"):
        load_config(config)


def test_chrome_slots_resolve_inline_and_file_variants(tmp_path: Path) -> None:
    from kpress.errors import KPressPublishError
    from kpress.publish.config import load_config

    (tmp_path / "_includes").mkdir()
    (tmp_path / "_includes" / "header.html").write_text(
        '<nav><a href="/">Guide</a></nav>\n', encoding="utf-8"
    )
    config = tmp_path / "kpress.yml"
    config.write_text(
        "site:\n"
        "  title: Slots\n"
        "  header_html_file: _includes/header.html\n"
        '  footer_html: "<p>Published with kpress</p>"\n'
        '  head_extra_html: \'<link rel="icon" href="/favicon.svg">\'\n'
        "sources:\n  - path: .\n",
        encoding="utf-8",
    )
    loaded = load_config(config)
    assert '<a href="/">Guide</a>' in loaded.header_html
    assert loaded.footer_html == "<p>Published with kpress</p>"
    assert loaded.head_extra_html == '<link rel="icon" href="/favicon.svg">'

    config.write_text(
        "site:\n"
        '  header_html: "<p>x</p>"\n'
        "  header_html_file: _includes/header.html\n"
        "sources:\n  - path: .\n",
        encoding="utf-8",
    )
    with pytest.raises(KPressPublishError, match=r"mutually exclusive"):
        load_config(config)

    config.write_text(
        "site:\n  footer_html_file: missing.html\nsources:\n  - path: .\n",
        encoding="utf-8",
    )
    with pytest.raises(KPressPublishError, match=r"footer_html_file not found"):
        load_config(config)


def test_build_site_emits_chrome_slots_in_every_page(tmp_path: Path) -> None:
    from kpress.publish import build_site

    (tmp_path / "index.md").write_text("# Home\n\nBody text.\n", encoding="utf-8")
    (tmp_path / "about.md").write_text("# About\n\nMore text.\n", encoding="utf-8")
    config = tmp_path / "kpress.yml"
    config.write_text(
        "site:\n"
        "  title: Slots\n"
        '  head_extra_html: \'<link rel="icon" href="/favicon.svg">\'\n'
        "  header_html: '<nav><a href=\"/\">Guide</a></nav>'\n"
        '  footer_html: "<p>Published with kpress</p>"\n'
        "sources:\n  - path: .\n"
        "publish:\n  output_dir: public\n",
        encoding="utf-8",
    )
    report = build_site(config)
    assert not report.diagnostics
    for page in ("index.html", "about.html"):
        html = (tmp_path / "public" / page).read_text(encoding="utf-8")
        assert '<link rel="icon" href="/favicon.svg">' in html
        assert (
            '<header class="kpress-site-header"><nav><a href="/">Guide</a></nav></header>' in html
        )
        assert '<footer class="kpress-site-footer"><p>Published with kpress</p></footer>' in html
        # Slots land inside the single scroll context so they share the
        # document column and typography.
        assert html.index('class="kpress-page-main') < html.index("kpress-site-header")


def test_render_page_omits_empty_chrome_slots() -> None:
    from kpress.format import DocumentInput, RenderOptions, render_page

    page = render_page(
        DocumentInput(title="t", source_text="# Hi", source_path="x.md", body_markdown="# Hi"),
        RenderOptions(asset_mode="linked"),
    )
    assert "kpress-site-header" not in page.html
    assert "kpress-site-footer" not in page.html


def test_static_passthrough_copies_files_and_lists_them_in_manifest(tmp_path: Path) -> None:
    import json

    from kpress.publish import build_site

    (tmp_path / "index.md").write_text("# Home\n", encoding="utf-8")
    (tmp_path / "logo.svg").write_text(
        "<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8"
    )
    (tmp_path / "img").mkdir()
    (tmp_path / "img" / "photo.png").write_bytes(b"\x89PNG fake")
    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n"
        "  - path: .\n"
        '    static: ["*.svg", "img/**/*.png"]\n'
        "publish:\n  output_dir: public\n",
        encoding="utf-8",
    )
    report = build_site(config)
    assert (tmp_path / "public" / "logo.svg").is_file()
    assert (tmp_path / "public" / "img" / "photo.png").read_bytes() == b"\x89PNG fake"
    listed = {f.path for f in report.files}
    assert "logo.svg" in listed and "img/photo.png" in listed
    manifest = json.loads(
        (tmp_path / "public" / "_kpress" / "kpress-manifest.json").read_text(encoding="utf-8")
    )
    manifest_paths = {f["path"] for f in manifest["files"]}
    assert "logo.svg" in manifest_paths and "img/photo.png" in manifest_paths

    # Rebuild after deleting the source: the stale copy is purged (the output
    # stays a pure function of current inputs).
    (tmp_path / "logo.svg").unlink()
    build_site(config)
    assert not (tmp_path / "public" / "logo.svg").exists()
    assert (tmp_path / "public" / "img" / "photo.png").is_file()


def test_static_passthrough_rejects_reserved_and_colliding_paths(tmp_path: Path) -> None:
    from kpress.errors import KPressPublishError
    from kpress.publish import build_site

    # Reserved: a static file may not land inside _kpress/.
    (tmp_path / "_kpress").mkdir()
    (tmp_path / "_kpress" / "x.svg").write_text("<svg/>", encoding="utf-8")
    config = tmp_path / "kpress.yml"
    config.write_text(
        'sources:\n  - path: .\n    static: ["_kpress/**/*.svg"]\npublish:\n  output_dir: public\n',
        encoding="utf-8",
    )
    with pytest.raises(KPressPublishError, match=r"reserved"):
        build_site(config)

    # Collision: a static file may not overwrite a rendered page.
    (tmp_path / "index.md").write_text("# Home\n", encoding="utf-8")
    (tmp_path / "index.html").write_text("<!doctype html>", encoding="utf-8")
    config.write_text(
        'sources:\n  - path: .\n    static: ["index.html"]\npublish:\n  output_dir: public\n',
        encoding="utf-8",
    )
    with pytest.raises(KPressPublishError, match=r"collides with the rendered page"):
        build_site(config)


def test_inline_asset_mode_and_single_file_export_are_gated(tmp_path: Path) -> None:
    """Until single-file output is truly self-contained (orig-7ehk), the
    config surface and the single-file export refuse loudly instead of
    emitting pages whose ES-module imports would 404 after relocation.
    """

    from kpress.errors import KPressPublishError
    from kpress.models import KPressExportRequest
    from kpress.publish.build import export_document
    from kpress.publish.config import load_config

    config = tmp_path / "kpress.yml"
    config.write_text("sources:\n  - path: .\npublish:\n  asset_mode: inline\n", encoding="utf-8")
    with pytest.raises(KPressPublishError, match=r"not yet supported.*sealed"):
        load_config(config)

    (tmp_path / "doc.md").write_text("# Doc\n", encoding="utf-8")
    with pytest.raises(KPressPublishError, match=r"single-file.*not yet supported"):
        export_document(
            KPressExportRequest(
                path=str(tmp_path / "doc.md"),
                kind="markdown",
                view="document",
                export_mode="single-file",
            )
        )


def test_static_passthrough_rejects_symlink_escaping_source_root(tmp_path: Path) -> None:
    """A static glob matching a symlink must not publish bytes from outside
    the source root (PR #175 review finding 2).
    """

    from kpress.errors import KPressPublishError

    outside = tmp_path / "outside-secret.txt"
    outside.write_text("SECRET\n", encoding="utf-8")
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.md").write_text("# Home\n", encoding="utf-8")
    (site / "secret.txt").symlink_to(outside)
    config = site / "kpress.yml"
    config.write_text(
        'sources:\n  - path: .\n    static: ["*.txt"]\npublish:\n  output_dir: public\n',
        encoding="utf-8",
    )

    with pytest.raises(KPressPublishError, match=r"outside its source root"):
        build_site(config)
    assert not (site / "public" / "secret.txt").exists()


def test_static_passthrough_allows_symlink_within_source_root(tmp_path: Path) -> None:
    (tmp_path / "index.md").write_text("# Home\n", encoding="utf-8")
    (tmp_path / "real.txt").write_text("fine\n", encoding="utf-8")
    (tmp_path / "alias.txt").symlink_to(tmp_path / "real.txt")
    config = tmp_path / "kpress.yml"
    config.write_text(
        'sources:\n  - path: .\n    static: ["*.txt"]\npublish:\n  output_dir: public\n',
        encoding="utf-8",
    )

    build_site(config)

    assert (tmp_path / "public" / "alias.txt").read_text(encoding="utf-8") == "fine\n"
