from __future__ import annotations

import json
import os
import re
import subprocess
import sys

import pytest

from kpress.errors import KPressInvalidRequestError
from kpress.format import Diagnostic, parse_markdown, sanitize
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
    for bad in ("style", "onclick", "href", "id", "form", "Not-Valid", ""):
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


def test_removed_comments_are_not_reported_as_sanitization() -> None:
    html = "<p>Text.</p>\n<!-- This document follows common-doc-guidelines.md -->\n"
    sanitized, diagnostics = sanitize_raw_html(html, "sanitized")

    assert "<!--" not in sanitized
    assert "<p>Text.</p>" in sanitized
    assert diagnostics == []


def test_reserialization_is_not_reported_as_sanitization() -> None:
    # nh3 writes U+00A0 as `&nbsp;`; the reader sees the same text.
    html = "<p>a b</p>\n<p><span> x</span></p>"
    sanitized, diagnostics = sanitize_raw_html(html, "sanitized")

    assert "&nbsp;" in sanitized
    assert diagnostics == []


def test_presentational_align_survives_on_blocks_and_headings() -> None:
    html = (
        '<p align="center"><img src="icon.png" width="96" align="middle"></p>\n'
        '<h1 align="center">Title</h1>\n<h6 align="right">x</h6>\n'
        '<div align="left">y</div>'
    )
    sanitized, diagnostics = sanitize_raw_html(html, "sanitized")

    assert '<p align="center">' in sanitized
    assert 'align="middle"' in sanitized
    assert '<h1 align="center">' in sanitized
    assert '<h6 align="right">' in sanitized
    assert '<div align="left">' in sanitized
    assert diagnostics == []


_BOX = '<input class="task-list-item-checkbox" disabled="disabled" type="checkbox">'
_TICKED_BOX = (
    '<input class="task-list-item-checkbox" checked="checked" disabled="disabled" type="checkbox">'
)
_INERT = '<input disabled="disabled" type="checkbox">'


@pytest.mark.parametrize("box", [_BOX, _TICKED_BOX])
def test_task_box_survives_sanitizing_unchanged(box: str) -> None:
    html = (
        '<ul class="contains-task-list">\n'
        f'<li class="kpress-task task-list-item">{box} x</li>\n</ul>'
    )
    sanitized, diagnostics = sanitize_raw_html(html, "sanitized")

    assert sanitized == html
    assert diagnostics == []


def test_hand_written_disabled_checkbox_keeps_its_state_unreported() -> None:
    # A bare `disabled` is the value the policy sets, spelled differently.
    sanitized, diagnostics = sanitize_raw_html(
        '<input type="checkbox" checked disabled>', "sanitized"
    )

    assert sanitized == '<input checked="checked" disabled="disabled" type="checkbox">'
    assert diagnostics == []


@pytest.mark.parametrize(
    "html",
    [
        '<input type="checkbox" disabled class="task-list-item-checkbox" checked>',
        "<input checked='' type=checkbox class=task-list-item-checkbox disabled=''>",
        '<INPUT TYPE="checkbox" CHECKED="CHECKED" Disabled CLASS="task-list-item-checkbox">',
    ],
)
def test_a_box_written_in_any_order_or_case_is_byte_for_byte_kpress_box(html: str) -> None:
    sanitized, diagnostics = sanitize_raw_html(html, "sanitized")

    assert sanitized == _TICKED_BOX
    assert diagnostics == []


_UNSTABLE_INPUTS = [
    ("<input>", _INERT),
    ('<input class="x">', _INERT),
    ("<input checked>", '<input checked="checked" disabled="disabled" type="checkbox">'),
    ("<INPUT>", _INERT),
    ('<input class="task-list-item-checkbox">', _BOX),
]


@pytest.mark.parametrize(("html", "expected"), _UNSTABLE_INPUTS)
def test_an_input_missing_type_and_disabled_has_one_serialization(html: str, expected: str) -> None:
    # nh3 adds the two set values in hash order, so one call could pass by chance.
    outputs = {sanitize_raw_html(html, "sanitized")[0] for _ in range(200)}

    assert outputs == {expected}


def test_input_serialization_is_the_same_in_every_process() -> None:
    script = (
        "import json, sys\n"
        "from kpress.format.sanitize import sanitize_raw_html\n"
        "sources = json.loads(sys.argv[1])\n"
        "print(json.dumps([sanitize_raw_html(s, 'sanitized')[0] for s in sources]))\n"
    )
    sources = [html for html, _ in _UNSTABLE_INPUTS]
    outputs: set[str] = set()
    for seed in ("0", "1", "2", "3", "random", "random", "random", "random"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        result = subprocess.run(
            [sys.executable, "-c", script, json.dumps(sources)],
            capture_output=True,
            check=True,
            env=env,
            text=True,
            timeout=60,
        )
        outputs.add(result.stdout)

    assert len(outputs) == 1
    assert json.loads(outputs.pop()) == [expected for _, expected in _UNSTABLE_INPUTS]


@pytest.mark.parametrize(
    ("html", "expected", "messages"),
    [
        (
            '<input type="text" value="secret" form="host-form" id="field">',
            _INERT,
            [
                "Removed attribute 'value' from <input>.",
                "Removed attribute 'form' from <input>.",
                "Removed attribute 'id' from <input>.",
                "Set attribute 'disabled' to 'disabled' on <input>.",
                "Set attribute 'type' to 'checkbox' on <input>.",
            ],
        ),
        (
            '<input type="image" src="https://evil.test/pixel.png">',
            _INERT,
            [
                "Removed attribute 'src' from <input>.",
                "Set attribute 'disabled' to 'disabled' on <input>.",
                "Set attribute 'type' to 'checkbox' on <input>.",
            ],
        ),
        (
            '<input type="password" disabled>',
            _INERT,
            ["Set attribute 'type' to 'checkbox' on <input>."],
        ),
        (
            '<input type="checkbox" checked data-k="v" tabindex="0">',
            '<input checked="checked" disabled="disabled" type="checkbox">',
            [
                "Removed attribute 'data-k' from <input>.",
                "Removed attribute 'tabindex' from <input>.",
                "Set attribute 'disabled' to 'disabled' on <input>.",
            ],
        ),
        (
            '<input type="checkbox" disabled name="q" formaction="https://evil.test/" '
            'onclick="alert(1)" onfocus="alert(2)" style="position:fixed" autofocus>',
            _INERT,
            [
                "Removed attribute 'name' from <input>.",
                "Removed attribute 'formaction' from <input>.",
                "Removed attribute 'onclick' from <input>.",
                "Removed attribute 'onfocus' from <input>.",
                "Removed attribute 'style' from <input>.",
                "Removed attribute 'autofocus' from <input>.",
            ],
        ),
        # The first of a repeated attribute is the one HTML keeps.
        ('<input type="checkbox" type="text" disabled>', _INERT, []),
        (
            '<input type="text" type="checkbox" disabled>',
            _INERT,
            ["Set attribute 'type' to 'checkbox' on <input>."],
        ),
        (
            '<input class="kpress-video-backdrop" class="task-list-item-checkbox" disabled '
            'type="checkbox">',
            _INERT,
            ["Removed attribute 'class' from <input>."],
        ),
        # `type` is matched case-sensitively, so another spelling is rewritten.
        (
            '<input TYPE="CHECKBOX" disabled>',
            _INERT,
            ["Set attribute 'type' to 'checkbox' on <input>."],
        ),
        (
            '<input type=" checkbox " disabled>',
            _INERT,
            ["Set attribute 'type' to 'checkbox' on <input>."],
        ),
        (
            '<input type="hidden" value="token">',
            _INERT,
            [
                "Removed attribute 'value' from <input>.",
                "Set attribute 'disabled' to 'disabled' on <input>.",
                "Set attribute 'type' to 'checkbox' on <input>.",
            ],
        ),
        # A forged input cannot take a KPress class, and keeps only the box's.
        (
            '<input class="kpress-video-backdrop kpress-visible" type="checkbox" disabled>',
            _INERT,
            ["Removed attribute 'class' from <input>."],
        ),
        (
            '<input class="kpress-visible task-list-item-checkbox" type="checkbox" disabled>',
            _BOX,
            ["Set attribute 'class' to 'task-list-item-checkbox' on <input>."],
        ),
        (
            '<input checked="no" type="checkbox" disabled>',
            _TICKED_BOX.replace(' class="task-list-item-checkbox"', ""),
            [],
        ),
    ],
)
def test_any_other_input_becomes_a_disabled_checkbox(
    html: str, expected: str, messages: list[str]
) -> None:
    sanitized, diagnostics = sanitize_raw_html(html, "sanitized")

    assert sanitized == expected
    assert [item.type for item in diagnostics] == ["html_sanitized_attribute"] * len(messages)
    assert [item.message for item in diagnostics] == messages


def test_extra_tags_and_attributes_cannot_widen_an_input() -> None:
    sanitized, diagnostics = sanitize_raw_html(
        '<input type="text" kind="note" data-k="v" class="x-note">',
        "sanitized",
        extra_tags=["input", "x-note"],
        extra_attributes=["kind"],
    )

    assert sanitized == _INERT
    assert [item.message for item in diagnostics] == [
        "Removed attribute 'kind' from <input>.",
        "Removed attribute 'data-k' from <input>.",
        "Removed attribute 'class' from <input>.",
        "Set attribute 'disabled' to 'disabled' on <input>.",
        "Set attribute 'type' to 'checkbox' on <input>.",
    ]


def test_a_raw_input_in_markdown_is_a_disabled_checkbox_when_sanitized() -> None:
    tree = parse_markdown(
        'Search: <input type="text" name="q" value="v">\n', title="T", trust_mode="sanitized"
    )

    assert tree.html == f"<p>Search: {_INERT}</p>"
    assert [item.message for item in tree.diagnostics] == [
        "Removed attribute 'name' from <input>.",
        "Removed attribute 'value' from <input>.",
        "Set attribute 'disabled' to 'disabled' on <input>.",
        "Set attribute 'type' to 'checkbox' on <input>.",
    ]


def test_input_set_values_stay_inside_the_input_allow_list() -> None:
    # nh3 runs the attribute filter after it sets values, so a set value outside the
    # allow-list would be removed again: without `type`, an input is a text field.
    set_values = sanitize._INPUT_SET_VALUES  # pyright: ignore[reportPrivateUsage]
    values = sanitize._INPUT_VALUES  # pyright: ignore[reportPrivateUsage]
    assert set(set_values) <= sanitize._INPUT_ATTRIBUTES  # pyright: ignore[reportPrivateUsage]
    assert {"disabled", "type"} <= set(set_values)
    assert all(values[name] == value for name, value in set_values.items())


def _no_input_diagnostics(*_args: object) -> list[Diagnostic]:
    return []


def test_an_attribute_filter_error_is_raised_not_passed_to_nh3(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # nh3 keeps the attribute when its filter raises, which would keep `type="text"`.
    def broken(_name: str, _value: str) -> str | None:
        raise RuntimeError("filter bug")

    monkeypatch.setattr(sanitize, "_input_diagnostics", _no_input_diagnostics)
    monkeypatch.setattr(sanitize, "_input_attribute", broken)

    with pytest.raises(RuntimeError, match="filter bug"):
        sanitize_raw_html('<input type="text">', "sanitized")


@pytest.mark.parametrize(
    ("html", "expected", "diagnostics"),
    [
        # html5ever makes an input in SVG a foreign element, which nh3 removes.
        (
            '<svg><input type="text" form="x"></svg>',
            "<svg></svg>",
            [("html_sanitized_tag", "Removed raw HTML tag <input>.", "line 1, column 6")],
        ),
        (
            '<math><mrow><input type="text"></mrow></math>',
            "<math><mrow></mrow></math>",
            [("html_sanitized_tag", "Removed raw HTML tag <input>.", "line 1, column 13")],
        ),
        # html5ever parses `<noscript>` content as text, so no input is there.
        (
            '<noscript><input type="text" form="x"></noscript>',
            '&lt;input type="text" form="x"&gt;',
            [("html_sanitized_tag", "Removed raw HTML tag <noscript>.", "line 1, column 1")],
        ),
        # A MathML text element holds HTML, so its input survives and is reported.
        (
            '<math><mi><input type="text" disabled></mi></math>',
            f"<math><mi>{_INERT}</mi></math>",
            [
                (
                    "html_sanitized_attribute",
                    "Set attribute 'type' to 'checkbox' on <input>.",
                    "line 1, column 11",
                )
            ],
        ),
        # A survivor beside a removed input keeps its own report.
        (
            '<svg><input></svg><input type="text" disabled>',
            f"<svg></svg>{_INERT}",
            [
                ("html_sanitized_tag", "Removed raw HTML tag <input>.", "line 1, column 6"),
                (
                    "html_sanitized_attribute",
                    "Set attribute 'type' to 'checkbox' on <input>.",
                    "line 1, column 19",
                ),
            ],
        ),
        # html5ever leaves SVG at `<p>`, which the audit does not model: the count of
        # inputs disagrees, so no input is reported as edited and the catch-all fires.
        (
            '<svg><p><input type="text">',
            f"<svg></svg><p>{_INERT}</p>",
            [("html_sanitized", "Raw HTML was removed or rewritten for this trust mode.", None)],
        ),
    ],
)
def test_an_input_that_does_not_survive_is_reported_as_removed(
    html: str, expected: str, diagnostics: list[tuple[str, str, str | None]]
) -> None:
    sanitized, found = sanitize_raw_html(html, "sanitized")

    assert sanitized == expected
    assert [(item.type, item.message, item.location) for item in found] == diagnostics


def test_an_unexplained_input_change_is_reported_beside_other_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Simulate drift: the audit sees no change to the input that the policy rewrites.
    monkeypatch.setattr(sanitize, "_input_diagnostics", _no_input_diagnostics)
    sanitized, diagnostics = sanitize_raw_html(
        '<input type="text"><span style="color:red">x</span>', "sanitized"
    )

    assert sanitized == f"{_INERT}<span>x</span>"
    assert [item.type for item in diagnostics] == ["html_sanitized_attribute", "html_sanitized"]


@pytest.mark.parametrize(
    ("html", "expected", "messages"),
    [
        (
            '<button form="host-form">Go</button>',
            '<button type="button">Go</button>',
            [
                "Removed attribute 'form' from <button>.",
                "Set attribute 'type' to 'button' on <button>.",
            ],
        ),
        # Inside a form on the host page, a button without a type submits it.
        (
            "<button>Go</button>",
            '<button type="button">Go</button>',
            ["Set attribute 'type' to 'button' on <button>."],
        ),
        (
            '<button type="reset" form="host-form">Reset</button>',
            '<button type="button">Reset</button>',
            [
                "Removed attribute 'form' from <button>.",
                "Set attribute 'type' to 'button' on <button>.",
            ],
        ),
        (
            '<button class="cta" type="SUBMIT" formaction="https://evil.test/">Send</button>',
            '<button class="cta" type="button">Send</button>',
            [
                "Removed attribute 'formaction' from <button>.",
                "Set attribute 'type' to 'button' on <button>.",
            ],
        ),
        # The first of a repeated attribute is the one HTML keeps.
        ('<button type="button" type="submit">x</button>', '<button type="button">x</button>', []),
        # KPress's own video button is already `type="button"` and passes unchanged.
        (
            '<button type="button" class="kpress-video-placeholder" data-kpress-video-id="v" '
            'aria-label="Open video: V">Play</button>',
            '<button type="button" class="kpress-video-placeholder" data-kpress-video-id="v" '
            'aria-label="Open video: V">Play</button>',
            [],
        ),
    ],
)
def test_a_button_can_never_submit_or_reset_a_host_form(
    html: str, expected: str, messages: list[str]
) -> None:
    sanitized, diagnostics = sanitize_raw_html(html, "sanitized")

    assert sanitized == expected
    assert [item.message for item in diagnostics] == messages


def test_no_element_keeps_form() -> None:
    sanitized, diagnostics = sanitize_raw_html(
        '<div form="host-form"><span form="host-form">a</span>'
        '<x-note form="host-form">b</x-note></div>',
        "sanitized",
        extra_tags=["x-note"],
    )

    assert sanitized == "<div><span>a</span><x-note>b</x-note></div>"
    assert [item.message for item in diagnostics] == [
        "Removed attribute 'form' from <div>.",
        "Removed attribute 'form' from <span>.",
        "Removed attribute 'form' from <x-note>.",
    ]


@pytest.mark.parametrize(
    "html",
    [
        '<link rel="stylesheet" href="https://evil.test/x.css">',
        '<link rel="preload" as="image" href="https://evil.test/pixel.png">',
        '<link rel="prefetch" href="https://evil.test/track">',
    ],
)
def test_a_link_element_never_loads_a_resource(html: str) -> None:
    sanitized, diagnostics = sanitize_raw_html(f"<p>x</p>{html}", "sanitized")

    assert sanitized == "<p>x</p>"
    assert [(item.type, item.message) for item in diagnostics] == [
        ("html_sanitized_tag", "Removed raw HTML tag <link>.")
    ]


def test_a_link_element_cannot_be_admitted_as_an_extra_tag() -> None:
    with pytest.raises(KPressInvalidRequestError):
        sanitize_raw_html("<p>x</p>", "sanitized", extra_tags=["link"])


def test_trusted_keeps_a_raw_input_as_written() -> None:
    html = '<input type="text" value="x" form="host-form">'
    assert sanitize_raw_html(html, "trusted") == (html, [])


def test_unexplained_removal_still_reports_the_catch_all(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Simulate drift: the audit approves an attribute that the nh3 policy removes.
    def approve_everything(*_args: object) -> bool:
        return True

    monkeypatch.setattr(
        "kpress.format.sanitize._SanitizerAudit._attribute_allowed", approve_everything
    )
    sanitized, diagnostics = sanitize_raw_html('<p style="color:red">x</p>', "sanitized")

    assert "style" not in sanitized
    assert [item.type for item in diagnostics] == ["html_sanitized"]
