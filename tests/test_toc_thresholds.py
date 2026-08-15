"""An "auto" TOC is earned by two independent properties of the document.

A table of contents is navigation, and navigation only helps a document a
reader cannot take in by scrolling. Heading count alone gave one to a
half-screen note whose every section was already on screen; length alone would
give one to a long unbroken essay with three headings. ``include_toc="auto"``
therefore requires both ``toc_min_headings`` and ``toc_min_words``, and the
explicit ``"on"`` / ``"off"`` modes bypass both.
"""

from __future__ import annotations

import pytest

from kpress.errors import KPressInvalidRequestError
from kpress.format import DocumentInput, RenderOptions, render_fragment
from kpress.models import KPressRenderRequest
from kpress.runtime import render_view

TOC_MARKER = 'class="kpress-toc'


def _document(*, headings: int, words_per_heading: int) -> str:
    body = " ".join(["word"] * words_per_heading)
    return "# Title\n\nintro\n\n" + "".join(
        f"## Section {index}\n\n{body}\n\n" for index in range(headings)
    )


# Both fixtures sit on the far side of one threshold and the near side of the
# other, so neither can pass by clearing the test it was not meant to clear.
MANY_HEADINGS_FEW_WORDS = _document(headings=12, words_per_heading=4)
FEW_HEADINGS_MANY_WORDS = _document(headings=3, words_per_heading=600)
LONG_AND_SECTIONED = _document(headings=9, words_per_heading=120)


def _render(markdown: str, **options: object) -> str:
    return render_fragment(
        DocumentInput(
            title="Doc",
            source_text=markdown,
            source_path="doc.md",
            body_markdown=markdown,
            trust_mode="sanitized",
        ),
        RenderOptions(**options),  # pyright: ignore[reportArgumentType]
    ).html


@pytest.mark.parametrize(
    ("markdown", "label"),
    [
        (MANY_HEADINGS_FEW_WORDS, "many headings, short body"),
        (FEW_HEADINGS_MANY_WORDS, "long body, few headings"),
    ],
)
def test_auto_withholds_the_toc_when_only_one_threshold_is_cleared(
    markdown: str, label: str
) -> None:
    assert TOC_MARKER not in _render(markdown), label


def test_auto_renders_the_toc_when_both_thresholds_are_cleared() -> None:
    assert TOC_MARKER in _render(LONG_AND_SECTIONED)


def test_word_count_measures_visible_text_not_markup() -> None:
    """Link targets and attributes are markup, so they cannot buy a TOC.

    The naive measure — the length of the Markdown source — would let a
    document of nine one-line sections full of long URLs clear a word
    threshold it has no reading length to justify.
    """

    url = "https://example.com/a/very/long/path/that/carries/no/reading/weight"
    linky = "# Title\n\nintro\n\n" + "".join(
        f"## Section {index}\n\n[x]({url}) [y]({url}) [z]({url})\n\n" for index in range(9)
    )

    assert TOC_MARKER not in _render(linky)


def test_explicit_modes_bypass_both_thresholds() -> None:
    assert TOC_MARKER in _render(MANY_HEADINGS_FEW_WORDS, include_toc="on")
    assert TOC_MARKER not in _render(LONG_AND_SECTIONED, include_toc="off")


def test_thresholds_are_tunable_back_to_a_count_only_rule() -> None:
    """A host that wants the pre-threshold behavior can still ask for it."""

    assert TOC_MARKER in _render(MANY_HEADINGS_FEW_WORDS, toc_min_headings=4, toc_min_words=0)


def _request(**overrides: object) -> KPressRenderRequest:
    fields: dict[str, object] = {
        "source_text": LONG_AND_SECTIONED,
        "source_path": "doc.md",
        "kind": "markdown",
        "view": "rendered",
        "ext": ".md",
        "mtime_hash": "abc",
        "size": len(LONG_AND_SECTIONED),
    }
    fields.update(overrides)
    return KPressRenderRequest(**fields)  # pyright: ignore[reportArgumentType]


def test_dynamic_hosts_can_suppress_the_toc_for_an_embedded_document() -> None:
    """An embedding host's own chrome is the navigation; see include_toc."""

    assert TOC_MARKER in render_view(_request())["html"]
    assert TOC_MARKER not in render_view(_request(include_toc="off"))["html"]


def test_dynamic_toc_settings_take_part_in_the_render_cache_identity() -> None:
    """Same document, different TOC settings, different rendered HTML.

    Sharing a cache entry across these would serve one host's TOC choice to
    another, which is the failure a cache-key omission produces.
    """

    assert render_view(_request())["html"] != render_view(_request(include_toc="off"))["html"]
    assert (
        render_view(_request(toc_min_words=100_000))["html"]
        != render_view(_request(toc_min_words=0))["html"]
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"include_toc": "sometimes"},
        {"include_toc": True},
        {"toc_min_headings": -1},
        {"toc_min_headings": "4"},
        # bool is an int in Python, so this has to be rejected explicitly.
        {"toc_min_words": True},
        {"toc_min_words": 1.5},
    ],
)
def test_out_of_contract_toc_settings_fail_loudly(overrides: dict[str, object]) -> None:
    with pytest.raises(KPressInvalidRequestError):
        render_view(_request(**overrides))
