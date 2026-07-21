"""The icon-button hover contract (kpress-design.md "Icon-Button Hover Contract").

Every icon-only control that performs an operation shares one hover treatment:
the light hover fill (--color-hover-bg) plus slight text darkening
(--kpress-doc-text), and never a border introduced or recolored on hover.
Resting borders (layout or legibility) are fine; state feedback such as the
code-copy copied/error border recoloring is state, not hover, and stays out of
the :hover rules this test scans.

A new icon control joins _ICON_BUTTON_HOVER_CONTROLS when it is added.
"""

from __future__ import annotations

import re
from pathlib import Path

_COMPONENTS_CSS = (
    Path(__file__).resolve().parents[1] / "src/kpress/format/static/css/components.css"
)

# Selector fragments identifying each icon operation button; a control's hover
# rules are the blocks whose selector attaches :hover directly to it.
_ICON_BUTTON_HOVER_CONTROLS = (
    ".kpress-settings-btn",
    ".kpress-menu-seg",
    ".kpress-toc-toggle",
    ".kpress-toc-expand-all",
    ".kpress-code-copy",
    "[data-kpress-video-close]",
)


def _hover_blocks(css: str, control: str) -> list[tuple[str, str]]:
    """(selector, body) for every rule with ``<control>:hover`` in its selector."""
    blocks: list[tuple[str, str]] = []
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selector = match.group(1).strip()
        if re.search(re.escape(control) + r":hover", selector):
            blocks.append((selector, match.group(2)))
    return blocks


def test_icon_buttons_share_the_hover_treatment() -> None:
    css = _COMPONENTS_CSS.read_text(encoding="utf-8")
    for control in _ICON_BUTTON_HOVER_CONTROLS:
        blocks = _hover_blocks(css, control)
        assert blocks, f"{control}: no :hover rule found"
        for selector, body in blocks:
            assert "border" not in body, (
                f"{control}: hover rule {selector!r} touches a border; the icon-button "
                f"hover contract is hover fill + darkening only"
            )
        combined = "\n".join(body for _, body in blocks)
        assert "var(--color-hover-bg)" in combined, (
            f"{control}: hover rules never apply the shared hover fill --color-hover-bg"
        )
        assert "color: var(--kpress-doc-text)" in combined, (
            f"{control}: hover rules never darken to --kpress-doc-text"
        )
