from __future__ import annotations

from kpress.format.sanitize import sanitize_generated_svg, sanitize_raw_html


def test_svg_camelcase_restored_at_attribute_position() -> None:
    svg = (
        '<svg viewbox="0 0 24 24" preserveaspectratio="xMidYMid"><circle refx="1" refy="2"/></svg>'
    )
    result = sanitize_generated_svg(svg)
    assert 'viewBox="0 0 24 24"' in result
    assert 'preserveAspectRatio="xMidYMid"' in result
    assert 'refX="1"' in result
    assert 'refY="2"' in result


def test_svg_camelcase_restore_skips_quoted_attribute_values() -> None:
    # A quoted value that literally contains ` viewbox=` must not be rewritten.
    svg = '<svg viewbox="0 0 8 8" aria-label="set the viewbox= value"><title>t</title></svg>'
    result = sanitize_generated_svg(svg)
    assert 'viewBox="0 0 8 8"' in result
    assert 'aria-label="set the viewbox= value"' in result


def test_svg_camelcase_restore_skips_text_content() -> None:
    svg = '<svg viewbox="0 0 8 8"><text x="0" y="0">use viewbox= here</text></svg>'
    result = sanitize_generated_svg(svg)
    assert 'viewBox="0 0 8 8"' in result
    assert ">use viewbox= here</text>" in result


def test_span_and_div_pass_through_by_default() -> None:
    html = '<div class="wrap" data-x="1"><span class="hl" data-y="2">hi</span></div>'
    for mode in ("public-static", "sanitized-local", "untrusted"):
        out, _ = sanitize_raw_html(html, mode)  # pyright: ignore[reportArgumentType]
        assert '<div class="wrap" data-x="1">' in out
        assert '<span class="hl" data-y="2">' in out


def test_extra_tags_survive_under_public_static_and_untrusted() -> None:
    html = '<x-callout class="variant" data-variant="x">D</x-callout>'
    for mode in ("public-static", "untrusted"):
        out, _ = sanitize_raw_html(html, mode, extra_tags=["x-callout"])  # pyright: ignore[reportArgumentType]
        assert out == '<x-callout class="variant" data-variant="x">D</x-callout>'


def test_non_whitelisted_tag_is_stripped() -> None:
    html = "<x-callout>kept</x-callout>"
    public, _ = sanitize_raw_html(html, "public-static")
    untrusted, _ = sanitize_raw_html(html, "untrusted")
    assert "<x-callout" not in public
    assert "<x-callout" not in untrusted
    assert "kept" in public
    assert "kept" in untrusted


def test_unsafe_attributes_stripped_on_whitelisted_tag() -> None:
    html = (
        '<x-callout class="ok" data-k="v" style="color:red" onclick="bad()" '
        'href="javascript:alert(1)">D</x-callout>'
    )
    for mode in ("public-static", "untrusted"):
        out, _ = sanitize_raw_html(html, mode, extra_tags=["x-callout"])  # pyright: ignore[reportArgumentType]
        assert 'class="ok"' in out
        assert 'data-k="v"' in out
        assert "style" not in out
        assert "onclick" not in out
        assert "javascript:" not in out


def test_untrusted_is_whitelist_only_and_strips_known_html_tags() -> None:
    # Under untrusted, the broad public-static allow-set does NOT apply: only the
    # pass-through whitelist survives, so an otherwise-safe <em> is stripped.
    html = "<em>emph</em><x-callout>dev</x-callout>"
    public, _ = sanitize_raw_html(html, "public-static", extra_tags=["x-callout"])
    untrusted, _ = sanitize_raw_html(html, "untrusted", extra_tags=["x-callout"])
    assert "<em>emph</em>" in public
    assert "<em" not in untrusted
    assert "<x-callout>dev</x-callout>" in untrusted


def test_trusted_local_skips_sanitization() -> None:
    html = '<x-callout style="x" onclick="y()">D</x-callout>'
    out, diagnostics = sanitize_raw_html(html, "trusted-local")
    assert out == html
    assert diagnostics == []
