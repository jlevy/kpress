from __future__ import annotations

from pathlib import Path

import pytest

from kpress import runtime
from kpress._version import __version__
from kpress.errors import KPressInvalidRequestError

_VSEG = f"v{__version__}"


def test_static_asset_url_is_version_keyed() -> None:
    # Hosts (e.g. an embedding app's chrome) preload/link a packaged asset from
    # their own page using this; it must match the version-keyed URL embedded
    # documents request so the two share one download and cache entry.
    assert (
        runtime.static_asset_url("fonts/source-sans-3-latin-wght-normal.woff2")
        == f"/kpress-static/{_VSEG}/fonts/source-sans-3-latin-wght-normal.woff2"
    )
    # Leading slashes on the rel path are normalized; a custom prefix is honored.
    assert runtime.static_asset_url("/css/style-tokens.css") == (
        f"/kpress-static/{_VSEG}/css/style-tokens.css"
    )
    assert runtime.static_asset_url("js/theme.js", prefix="/assets/") == (
        f"/assets/{_VSEG}/js/theme.js"
    )


def test_runtime_renders_and_caches_document() -> None:
    runtime.clear_render_cache()
    request = runtime.KPressRenderRequest(
        source_text="# One\n\nBody\n",
        source_path="docs/one.md",
        kind="markdown",
        view="rendered",
        ext=".md",
        mtime_hash="a",
        size=12,
        frontmatter={"title": "One"},
    )

    first = runtime.render_view(request)
    second = runtime.render_view(request)

    assert first == second
    assert first["type"] == "kpress-rendered-document"
    assert 'class="kpress kpress-doc kpress-print-surface"' in first["html"]
    assert f"/kpress-static/{_VSEG}/css/document.css" in first["assets"]["css"]
    assert f"/kpress-static/{_VSEG}/js/theme.js" in first["assets"]["js"]


def test_runtime_renders_source_profile() -> None:
    runtime.clear_render_cache()
    request = runtime.KPressRenderRequest(
        source_text="print('x')\n",
        source_path="script.py",
        kind="text",
        view="source",
        ext=".py",
        mtime_hash="a",
        size=11,
    )

    result = runtime.render_view(request)

    assert result["profile"] == "source"
    assert "kpress-source" in result["html"]
    assert "print(&#x27;x&#x27;)" in result["html"]


def test_runtime_rejects_bad_asset_paths() -> None:
    with pytest.raises(runtime.KPressAssetNotFoundError):
        _ = runtime.get_static_asset("../secret.css")


def test_runtime_serves_package_static_asset() -> None:
    asset = runtime.get_static_asset("css/document.css")

    assert b".kpress" in asset.content
    assert asset.media_type == "text/css"
    assert asset.etag.startswith('"kp-')
    assert asset.cache_control == "no-cache"


def test_runtime_versioned_asset_is_long_lived_but_revalidatable() -> None:
    versioned = runtime.get_static_asset(f"{_VSEG}/css/document.css")
    plain = runtime.get_static_asset("css/document.css")

    assert versioned.content == plain.content
    assert versioned.etag == plain.etag
    # Long-lived but NOT immutable: a normal reload must be able to revalidate
    # via the content-hash ETag, so a same-version content change (source build
    # or an unbumped release) never strands a reader on stale assets.
    assert versioned.cache_control == "public, max-age=31536000"
    assert "immutable" not in versioned.cache_control
    assert versioned.etag.startswith('"kp-')


def test_runtime_versioned_prefix_still_rejects_traversal() -> None:
    with pytest.raises(runtime.KPressAssetNotFoundError):
        _ = runtime.get_static_asset(f"{_VSEG}/../secret.css")


def test_runtime_static_root_override(tmp_path: Path) -> None:
    static_root = tmp_path / "static"
    static_root.mkdir()
    _ = (static_root / "x.css").write_text(".x{}\n")
    runtime.set_static_root_for_tests(static_root)
    try:
        asset = runtime.get_static_asset("x.css")
    finally:
        runtime.set_static_root_for_tests(None)

    assert asset.content == b".x{}\n"


# --- security: dynamic render must strip active content (orig-w14p) -----


_XSS_PAYLOADS = [
    ("script tag", "<script>globalThis.__kpress_xss = 1</script>"),
    ("img onerror handler", "<img src=x onerror=alert(1)>"),
    ("svg onload handler", "<svg onload=alert(1)></svg>"),
    ("javascript: href", '<a href="javascript:alert(1)">click</a>'),
    ("javascript: href with tab", '<a href="javas\tcript:alert(1)">tab</a>'),
    ("iframe with src", '<iframe src="javascript:alert(1)"></iframe>'),
]


@pytest.mark.parametrize(("label", "payload"), _XSS_PAYLOADS)
def test_dynamic_render_strips_active_content_from_document_body(label: str, payload: str) -> None:
    """The dynamic render path serves arbitrary host-supplied documents.
    Host apps inject the returned HTML fragment into their shell via
    `innerHTML`, so active content in the document body must not survive
    sanitization. Regression for orig-w14p.
    """

    source = f"# Title\n\n{payload}\n"
    payload_result = runtime.render_view(
        runtime.KPressRenderRequest(
            source_text=source,
            source_path="demo.md",
            kind="markdown",
            view="rendered",
            ext=".md",
            mtime_hash="x",
            size=len(source),
            profile="document",
        )
    )
    html = payload_result["html"]
    forbidden_substrings = (
        "<script",
        "onerror=",
        "onload=",
        "onclick=",
        "javascript:",
    )
    survivors = [s for s in forbidden_substrings if s in html.lower()]
    assert survivors == [], (
        f"{label}: payload {payload!r} survived sanitization (found {survivors!r} in rendered HTML)"
    )


def test_dynamic_render_does_not_emit_frontmatter_as_setext_h2() -> None:
    """Markdown-it interprets `---` as setext heading underline. If we feed
    the raw source (frontmatter block included) to the body renderer, the
    `---\\nkey: value\\n---` block emits an unwanted `<h2>` with the YAML
    keys as its text right above the real document body. Regression for
    the runtime helper that strips leading frontmatter before rendering."""

    source = "---\ntitle: Smoke\nauthor: Ada\n---\n\n# Real Heading\n\nBody.\n"
    runtime.clear_render_cache()
    payload = runtime.render_view(
        runtime.KPressRenderRequest(
            source_text=source,
            source_path="docs/x.md",
            kind="markdown",
            view="rendered",
            ext=".md",
            mtime_hash="x",
            size=len(source),
            frontmatter={"title": "Smoke", "author": "Ada"},
            profile="document",
        )
    )
    html = payload["html"]

    # Bug repro: an h2 containing the frontmatter keys appeared in the body.
    body = html.split("<header", 1)[-1]
    assert "<h2" not in body or "title: Smoke" not in body
    # The legitimate H1 from the body must still be present.
    assert 'id="real-heading"' in html or ">Real Heading</h1>" in html


@pytest.mark.parametrize(
    ("view", "profile", "expected"),
    [
        ("rendered", None, "document"),
        ("source", None, "source"),
        ("rendered", "doc", "document"),
        ("rendered", "text", "source"),
        ("source", "source", "source"),
    ],
)
def test_normalize_print_profile_maps_view_and_profile_aliases(
    view: str, profile: str | None, expected: str
) -> None:
    assert runtime.normalize_print_profile(view, profile) == expected


@pytest.mark.parametrize(
    "profile",
    ["bogus", "html", "PRINT", "  unknown  "],
)
def test_normalize_print_profile_raises_on_unsupported_profile(profile: str) -> None:
    with pytest.raises(KPressInvalidRequestError, match="Unsupported KPress print profile"):
        runtime.normalize_print_profile("rendered", profile)


def test_runtime_threads_widgets_map_into_payload() -> None:
    runtime.clear_render_cache()
    request = runtime.KPressRenderRequest(
        source_text="# One\n\nBody\n",
        source_path="docs/one.md",
        kind="markdown",
        view="rendered",
        ext=".md",
        mtime_hash="widgets-a",
        size=12,
        widgets={"settings": {"choosers": ["theme"]}, "minimap": "off"},
    )

    payload = runtime.render_view(request)

    # Echoed for host-mounted widgets: defaults merged, "off" removed,
    # config passed through verbatim.
    assert payload["widgets"] == {"settings": {"choosers": ["theme"]}}
    assert "minimap" not in payload["widgets"]


def test_render_view_normalizes_widget_values_like_the_static_dialects() -> None:
    """Static/dynamic parity: the same widget map publishes the same data.
    Presence booleans normalize ("on"/"off"); invalid values raise instead of
    being silently kept truthy."""

    runtime.clear_render_cache()

    def request(widgets: dict[str, object], tag: str) -> runtime.KPressRenderRequest:
        return runtime.KPressRenderRequest(
            source_text="# One\n\nBody\n",
            source_path="docs/one.md",
            kind="markdown",
            view="rendered",
            ext=".md",
            mtime_hash=f"widget-norm-{tag}",
            size=12,
            widgets=widgets,
        )

    payload = runtime.render_view(request({"settings": True}, "bool"))
    assert payload["widgets"] == {"settings": "on"}

    with pytest.raises(runtime.KPressPublishError, match="widgets"):
        runtime.render_view(request({"settings": "Off"}, "typo"))


def test_render_view_payload_model_matches_the_static_page_model() -> None:
    """Embeds get the full page model in the payload (same keys and data as
    the static #kpress-page-model block); route is empty because the request
    carries no site route."""

    import json
    import re

    from kpress.contract import PUBLIC_PAGE_MODEL_KEYS
    from kpress.format import DocumentInput, RenderOptions, render_page

    runtime.clear_render_cache()
    source = "# Alpha\n\nBody.\n\n## Beta\n\nMore.\n"
    payload = runtime.render_view(
        runtime.KPressRenderRequest(
            source_text=source,
            source_path="docs/guide.md",
            kind="markdown",
            view="rendered",
            ext=".md",
            mtime_hash="model-1",
            size=len(source),
            frontmatter={"title": "Guide"},
        )
    )
    model = payload["model"]
    assert set(model) == set(PUBLIC_PAGE_MODEL_KEYS)
    assert model["route"] == ""
    assert [heading["title"] for heading in model["headings"]] == ["Beta"]

    page = render_page(
        DocumentInput(
            title="guide.md",
            source_text=source,
            body_markdown=source,
            source_path="docs/guide.md",
            frontmatter={"title": "Guide"},
        ),
        RenderOptions(),
    )
    match = re.search(
        r'<script type="application/json" id="kpress-page-model">(.*?)</script>',
        page.html,
        re.DOTALL,
    )
    assert match
    static_model = json.loads(match.group(1))
    static_model["route"] = ""
    assert model == static_model


def test_render_view_threads_extra_tags_and_keys_the_cache_on_them() -> None:
    # The dynamic embed path admits the same host whitelist as static publish, so one
    # document renders identically both ways; renders with different whitelists must
    # not share a cache entry (same source, mtime, and size below).
    def request(extra_tags: tuple[str, ...]) -> runtime.KPressRenderRequest:
        return runtime.KPressRenderRequest(
            source_text='<x-callout class="tip" data-k="v">Note</x-callout>\n',
            source_path="docs/callout.md",
            kind="markdown",
            view="rendered",
            ext=".md",
            mtime_hash="a",
            size=10,
            extra_tags=extra_tags,
        )

    admitted = runtime.render_view(request(("x-callout",)))
    stripped = runtime.render_view(request(()))

    assert '<x-callout class="tip" data-k="v">' in admitted["html"]
    assert "<x-callout" not in stripped["html"]
    assert "Note" in stripped["html"]


def test_render_view_invalid_extra_tags_raise_invalid_request_error() -> None:
    # A forbidden or malformed extra_tags entry is bad request input, so it must
    # surface as KPressInvalidRequestError (like an unsupported print profile), not
    # be re-wrapped as a KPressRenderError by render_view's broad error handler.
    request = runtime.KPressRenderRequest(
        source_text="# Doc\n",
        source_path="docs/doc.md",
        kind="markdown",
        view="rendered",
        ext=".md",
        mtime_hash="b",
        size=6,
        extra_tags=("script",),
    )
    with pytest.raises(KPressInvalidRequestError, match="extra_tags"):
        runtime.render_view(request)


def test_render_view_threads_extra_attributes_and_keys_the_cache_on_them() -> None:
    # Same source/mtime/size: only the declared attribute names differ, so the two
    # renders must not share a cache entry and the attribute must survive only when
    # declared.
    def request(extra_attributes: tuple[str, ...]) -> runtime.KPressRenderRequest:
        return runtime.KPressRenderRequest(
            source_text='<x-callout kind="tip">Note</x-callout>\n',
            source_path="docs/kind.md",
            kind="markdown",
            view="rendered",
            ext=".md",
            mtime_hash="a",
            size=11,
            extra_tags=("x-callout",),
            extra_attributes=extra_attributes,
        )

    kept = runtime.render_view(request(("kind",)))
    stripped = runtime.render_view(request(()))
    assert 'kind="tip"' in kept["html"]
    assert 'kind="tip"' not in stripped["html"]
