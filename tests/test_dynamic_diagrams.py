"""The dynamic render path selects the diagram mode, as RenderOptions.diagrams does.

A host that renders GitHub content through ``render_view`` passes
``diagrams="mermaid"`` so a ```svg fence stays highlighted code, as GitHub shows it,
while a ```mermaid fence still becomes a diagram figure.
"""

from __future__ import annotations

import typing

import pytest

from kpress.contract import PUBLIC_RENDER_REQUEST_FIELDS
from kpress.errors import KPressInvalidRequestError
from kpress.format import DiagramMode as FormatDiagramMode
from kpress.models import DiagramMode, KPressRenderRequest
from kpress.runtime import render_view

SOURCE = (
    "# Diagrams\n\n"
    "```mermaid\ngraph TD\n  A --> B\n```\n\n"
    '```svg\n<svg viewBox="0 0 10 10"><circle cx="5" cy="5" r="4"></circle></svg>\n```\n'
)


def _request(diagrams: str, mtime_hash: str = "hash") -> KPressRenderRequest:
    return KPressRenderRequest(
        source_text=SOURCE,
        source_path="diagrams.md",
        kind="markdown",
        view="document",
        ext=".md",
        mtime_hash=mtime_hash,
        size=len(SOURCE),
        diagrams=diagrams,  # pyright: ignore[reportArgumentType]
    )


def test_the_request_mode_mirrors_the_format_mode() -> None:
    assert typing.get_args(DiagramMode) == typing.get_args(FormatDiagramMode)
    assert "diagrams" in PUBLIC_RENDER_REQUEST_FIELDS


def test_mermaid_mode_leaves_an_svg_fence_as_code() -> None:
    html = render_view(_request("mermaid"))["html"]

    assert 'data-kpress-diagram="mermaid"' in html
    assert 'data-kpress-diagram="svg"' not in html
    assert '<code class="language-svg">&lt;svg viewBox="0 0 10 10"&gt;&lt;circle' in html
    assert '<svg viewBox="0 0 10 10">' not in html


@pytest.mark.parametrize(
    ("mode", "mermaid", "svg"),
    [("auto", True, True), ("mermaid", True, False), ("off", False, False)],
)
def test_each_mode_shares_one_fingerprint_without_sharing_a_cache_entry(
    mode: str, mermaid: bool, svg: bool
) -> None:
    # One fingerprint for every mode: the mode itself must keep the entries apart.
    html = render_view(_request(mode, mtime_hash="shared"))["html"]

    assert ('data-kpress-diagram="mermaid"' in html) is mermaid
    assert ('data-kpress-diagram="svg"' in html) is svg


def test_an_unknown_mode_is_rejected() -> None:
    with pytest.raises(KPressInvalidRequestError, match="Invalid diagrams"):
        _ = render_view(_request("graphviz"))
