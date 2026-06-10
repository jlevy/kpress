from __future__ import annotations

import json
import re
from typing import cast

from kpress.format import DocumentInput, RenderOptions, render_page
from kpress.format.assets import read_package_text

from .golden_helpers import KPRESS_ROOT

_TAILWIND_CDN_RE = re.compile(r"@tailwindcss/browser|tailwindcss", re.IGNORECASE)


def _inventory() -> dict[str, object]:
    path = KPRESS_ROOT / "tests/fixtures/textpress_kash/tailwind-migration.json"
    loaded: object = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return cast(dict[str, object], loaded)


def _replacement_selectors(value: str) -> list[str]:
    return re.findall(r"\.kpress-[A-Za-z0-9_-]+", value)


def test_tailwind_inventory_maps_each_active_utility_to_kpress_css() -> None:
    inventory = _inventory()
    raw_utilities = inventory["utilities"]
    assert isinstance(raw_utilities, dict)
    utilities = cast(dict[str, object], raw_utilities)
    css = "\n".join(
        [
            read_package_text("css/document.css"),
            read_package_text("css/components.css"),
            read_package_text("css/print.css"),
        ]
    )

    assert isinstance(utilities, dict)
    for utility, entry in utilities.items():
        assert isinstance(entry, dict), utility
        entry_dict = cast(dict[str, object], entry)
        assert entry_dict["status"] in {"kpress-owned", "legacy-only", "host-only"}, utility
        replacement = str(entry_dict["replacement"])
        selectors = _replacement_selectors(replacement)
        if entry_dict["status"] == "kpress-owned":
            assert selectors, utility
            for selector in selectors:
                assert selector in css, f"{utility} replacement {selector} missing from CSS"


def test_kpress_output_and_assets_do_not_reference_tailwind_runtime_or_utilities() -> None:
    inventory = _inventory()
    raw_utilities = inventory["utilities"]
    assert isinstance(raw_utilities, dict)
    utilities = set(cast(dict[str, object], raw_utilities))
    source_text = "# Tailwind Check\n\nBody\n"

    page = render_page(
        DocumentInput(
            title="Tailwind Check",
            source_text=source_text,
            body_markdown=source_text,
            source_path="tailwind-check.md",
        ),
        RenderOptions(include_toc="off"),
    )
    combined = "\n".join(
        [
            page.html,
            read_package_text("css/document.css"),
            read_package_text("css/components.css"),
            read_package_text("js/theme.js"),
        ]
    )

    assert _TAILWIND_CDN_RE.search(combined) is None
    for utility in utilities:
        assert f'class="{utility}"' not in page.html
        assert f" {utility} " not in page.html
