"""The wide-band TOC rail is a layout slot, optionally independent of the TOC.

``RenderOptions.toc_rail="reserved"`` keeps the reading column in the sidebar
layout's position and measure on a document that earned no TOC, instead of
dropping it back to the centred, measure-capped single column. The stamp is
emitted only in the held-open-but-empty case: a rendered TOC already drives the
CSS through the nav element, and ``include_toc="off"`` wants its centred column.

Geometry is asserted in real Chromium by
``tests/test_playwright_toc_rail.py`` — container queries and ``cqw`` units are
not evaluated by browserless DOM emulation.
"""

from __future__ import annotations

import pytest

from kpress.contract import PUBLIC_FORMAT_API, PUBLIC_RENDER_REQUEST_FIELDS
from kpress.errors import KPressInvalidRequestError, KPressPublishError
from kpress.format import DocumentInput, RenderOptions, read_package_text, render_fragment
from kpress.models import KPressRenderRequest
from kpress.publish.config import load_config
from kpress.runtime import render_view

STAMP = 'data-kpress-toc-rail="reserved"'

# Six H2s clears the default toc_min_headings of 4; one does not.
LONG = "# Title\n\nintro\n\n" + "".join(f"## Section {i}\n\nbody\n\n" for i in range(6))
SHORT = "# Title\n\nintro\n\n## Only section\n\nbody\n"


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


def test_default_render_is_unchanged_by_the_option_existing() -> None:
    """toc_rail defaults to "auto": no stamp, on any document."""

    assert STAMP not in _render(LONG)
    assert STAMP not in _render(SHORT)
    assert RenderOptions().toc_rail == "auto"


def test_reserved_stamps_only_the_document_that_lost_its_toc() -> None:
    long_html = _render(LONG, toc_rail="reserved")
    short_html = _render(SHORT, toc_rail="reserved")

    # The long document rendered a real TOC, so the nav drives the layout and
    # the markup stays byte-identical to the "auto" render.
    assert 'class="kpress-toc' in long_html
    assert STAMP not in long_html
    assert long_html == _render(LONG)

    # The short one lost its TOC and needs the stamp to hold the rail.
    assert 'class="kpress-toc' not in short_html
    assert STAMP in short_html


def test_reserved_never_overrides_an_explicit_toc_off() -> None:
    """A document with TOCs switched off wants its centred column back."""

    html = _render(SHORT, toc_rail="reserved", include_toc="off")

    assert STAMP not in html
    assert html == _render(SHORT, include_toc="off")


def test_reserved_holds_the_rail_for_a_document_with_no_headings_at_all() -> None:
    html = _render("Just a paragraph, no headings.\n", toc_rail="reserved")

    assert STAMP in html


def test_the_stamp_lands_on_the_layout_wrapper() -> None:
    """The CSS selects `.kpress-content-with-toc[data-kpress-toc-rail=...]`."""

    html = _render(SHORT, toc_rail="reserved")

    assert f'<div class="kpress-doc-layout kpress-content-with-toc" {STAMP}>' in html


@pytest.mark.parametrize("rail", ["auto", "reserved"])
def test_the_dynamic_path_carries_the_same_choice(rail: str) -> None:
    payload = render_view(
        KPressRenderRequest(
            source_text=SHORT,
            source_path="doc.md",
            kind="markdown",
            view="document",
            ext=".md",
            mtime_hash=f"hash-{rail}",
            size=len(SHORT),
            toc_rail=rail,  # pyright: ignore[reportArgumentType]
        )
    )

    assert (STAMP in payload["html"]) is (rail == "reserved")


def test_the_dynamic_path_rejects_an_unknown_rail_value() -> None:
    request = KPressRenderRequest(
        source_text=SHORT,
        source_path="doc.md",
        kind="markdown",
        view="document",
        ext=".md",
        mtime_hash="hash-bad",
        size=len(SHORT),
        toc_rail="reserve",  # pyright: ignore[reportArgumentType]
    )

    with pytest.raises(KPressInvalidRequestError, match="Invalid toc_rail"):
        _ = render_view(request)


def test_the_rail_choice_is_part_of_the_render_cache_identity() -> None:
    """Same document, same fingerprint, different rail: not the same entry."""

    def render(rail: str) -> str:
        return render_view(
            KPressRenderRequest(
                source_text=SHORT,
                source_path="cached.md",
                kind="markdown",
                view="document",
                ext=".md",
                mtime_hash="one-fingerprint",
                size=len(SHORT),
                toc_rail=rail,  # pyright: ignore[reportArgumentType]
            )
        )["html"]

    assert STAMP not in render("auto")
    assert STAMP in render("reserved")
    assert STAMP not in render("auto")


def test_the_option_is_pinned_in_the_public_contract() -> None:
    assert "toc_rail" in PUBLIC_RENDER_REQUEST_FIELDS
    assert "TocRail" in PUBLIC_FORMAT_API


def test_yaml_config_accepts_the_rail_and_rejects_a_typo(tmp_path: object) -> None:
    from pathlib import Path

    assert isinstance(tmp_path, Path)
    config_path = tmp_path / "kpress.yml"

    _ = config_path.write_text("format:\n  toc_rail: reserved\n", encoding="utf-8")
    assert load_config(config_path).format.toc_rail == "reserved"

    _ = config_path.write_text("format:\n  toc_rail: reserve\n", encoding="utf-8")
    with pytest.raises(KPressPublishError, match="format.toc_rail"):
        _ = load_config(config_path)


def test_every_wide_band_rule_lists_all_three_rail_conditions() -> None:
    """A rule that names fewer conditions splits the two layouts apart again.

    The failure mode is silent — the reserved-rail document simply drops out of
    that one rule — so the band is checked structurally rather than by eye.
    """

    css = read_package_text("css/components.css")
    band = css.partition("@container kpress-doc (min-width: 75rem) {")[2]
    band = band.partition("\n}\n")[0]
    assert band, "the wide document band moved or was renamed"

    # One reserved-rail selector for every selector that asks "did this document
    # render a TOC". Counting is the invariant that survives refactors: adding a
    # TOC-keyed rule without its rail counterpart is exactly the silent bug.
    assert band.count(":has(.kpress-toc)") == band.count('[data-kpress-toc-rail="reserved"]')

    # Spot-check the groups that carry the geometry, so the count above cannot
    # be satisfied by unrelated selectors.
    for reserved in [
        '.kpress-doc:has(> [data-kpress-toc-rail="reserved"])',
        '.kpress-doc-layout[data-kpress-toc-rail="reserved"]',
        '.kpress-content-with-toc[data-kpress-toc-rail="reserved"] {',
        '.kpress-content-with-toc[data-kpress-toc-rail="reserved"] .kpress-table-wrap',
        '.kpress-content-with-toc[data-kpress-toc-rail="reserved"] .kpress-table {',
    ]:
        assert reserved in band, f"missing reserved-rail rule: {reserved}"


def test_the_thumbnail_is_pinned_to_the_reading_column() -> None:
    """Otherwise grid auto-placement drops it into the empty rail."""

    css = read_package_text("css/components.css")

    assert ".kpress-content-with-toc > .thumbnail {" in css
