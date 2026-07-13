from __future__ import annotations

import re

import pytest

from kpress.errors import KPressInvalidRequestError
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
    out, _ = sanitize_raw_html(html, "sanitized")
    assert '<div class="wrap" data-x="1">' in out
    assert '<span class="hl" data-y="2">' in out


def test_extra_tags_survive_under_sanitized() -> None:
    html = '<x-callout class="variant" data-variant="x">D</x-callout>'
    out, _ = sanitize_raw_html(html, "sanitized", extra_tags=["x-callout"])
    assert out == '<x-callout class="variant" data-variant="x">D</x-callout>'


def test_non_whitelisted_tag_is_stripped() -> None:
    html = "<x-callout>kept</x-callout>"
    out, _ = sanitize_raw_html(html, "sanitized")
    assert "<x-callout" not in out
    assert "kept" in out


def test_unsafe_attributes_stripped_on_whitelisted_tag() -> None:
    html = (
        '<x-callout class="ok" data-k="v" style="color:red" onclick="bad()" '
        'href="javascript:alert(1)">D</x-callout>'
    )
    out, _ = sanitize_raw_html(html, "sanitized", extra_tags=["x-callout"])
    assert 'class="ok"' in out
    assert 'data-k="v"' in out
    assert "style" not in out
    assert "onclick" not in out
    assert "javascript:" not in out


def test_sanitizer_reports_each_removed_item_with_location() -> None:
    html = '<p style="color:red">safe</p>\n<x-callout onclick="bad()">content</x-callout>'

    out, diagnostics = sanitize_raw_html(html, "sanitized")

    assert "style=" not in out
    assert "<x-callout" not in out
    assert [(item.type, item.location) for item in diagnostics] == [
        ("html_sanitized_attribute", "line 1, column 1"),
        ("html_sanitized_tag", "line 2, column 1"),
    ]
    assert "style" in diagnostics[0].message
    assert "x-callout" in diagnostics[1].message


def test_extra_tags_carry_only_class_and_data_attributes() -> None:
    # The pass-through attribute policy applies to tags admitted only via the
    # whitelist: class/data-* ride through, but the global attributes standard tags
    # keep (id/href/src) are stripped, so a custom element cannot carry navigation,
    # resource loads, or a clobbering id.
    html = (
        '<x-callout id="steal" href="https://evil.test" src="https://evil.test/x" '
        'class="ok" data-k="v">D</x-callout>'
        '<a id="anchor" href="https://example.com">link</a>'
    )
    out, _ = sanitize_raw_html(html, "sanitized", extra_tags=["x-callout"])
    callout = re.search(r"<x-callout[^>]*>", out)
    assert callout
    assert 'class="ok"' in callout.group(0)
    assert 'data-k="v"' in callout.group(0)
    for dropped in ("id=", "href=", "src="):
        assert dropped not in callout.group(0)
    # Standard tags are unaffected by the pass-through restriction.
    anchor = re.search(r"<a[^>]*>", out)
    assert anchor
    assert 'href="https://example.com"' in anchor.group(0)
    assert 'id="anchor"' in anchor.group(0)


def test_media_embedding_tags_are_forbidden_extra_tags() -> None:
    for bad in ("video", "audio", "source", "track", "picture"):
        with pytest.raises(KPressInvalidRequestError):
            sanitize_raw_html("<p>x</p>", "sanitized", extra_tags=[bad])


def test_trusted_skips_sanitization() -> None:
    html = '<x-callout style="x" onclick="y()">D</x-callout>'
    out, diagnostics = sanitize_raw_html(html, "trusted")
    assert out == html
    assert diagnostics == []


def test_extra_tags_validated_on_direct_render_path() -> None:
    # RenderOptions.extra_tags never passes through config loading, so the sanitizer
    # itself must reject forbidden or malformed names with a clear error instead of an
    # nh3 panic (script/style) or a silently ineffective entry.
    for bad in ("script", "frameset", "Not-Valid", ""):
        with pytest.raises(KPressInvalidRequestError):
            sanitize_raw_html("<p>x</p>", "sanitized", extra_tags=[bad])


def test_extra_attributes_survive_on_whitelisted_tags_only() -> None:
    html = '<x-callout kind="tip" term="stock option">D</x-callout><p kind="tip">p</p>'
    out, _ = sanitize_raw_html(
        html, "sanitized", extra_tags=["x-callout"], extra_attributes=["kind", "term"]
    )
    assert '<x-callout kind="tip" term="stock option">' in out
    # Standard tags keep their fixed policy: the declared name does not widen <p>.
    assert '<p kind="tip">' not in out
    assert "<p>p</p>" in out

    # Without the declaration the same attribute is stripped from the whitelisted tag.
    undeclared, _ = sanitize_raw_html(html, "sanitized", extra_tags=["x-callout"])
    assert "kind=" not in undeclared


def test_extra_attributes_validated_on_direct_render_path() -> None:
    for bad in ("style", "onclick", "href", "id", "Not-Valid", ""):
        with pytest.raises(KPressInvalidRequestError):
            sanitize_raw_html(
                "<p>x</p>", "sanitized", extra_tags=["x-callout"], extra_attributes=[bad]
            )


def test_sanitizer_audit_explains_every_representative_rewrite() -> None:
    cases = (
        ("<script>alert(1)</script>", None),
        ('<p style="color:red">text</p>', None),
        ('<a href="javascript:alert(1)">link</a>', None),
        ('<x-callout onclick="bad()">tip</x-callout>', ["x-callout"]),
    )

    for html, extra_tags in cases:
        sanitized, diagnostics = sanitize_raw_html(
            html,
            "sanitized",
            extra_tags=extra_tags,
        )

        assert sanitized != html
        assert diagnostics
        assert all(item.type != "html_sanitized" for item in diagnostics)
