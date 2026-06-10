from __future__ import annotations

from kpress.format.sanitize import sanitize_generated_svg


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
