from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict, cast

from kpress.format._github_slugger import GithubSlugger


class _Fixture(TypedDict):
    name: str
    input: str
    expected: str


def test_github_slugger_matches_complete_v2_fixture_sequence() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "github-slugger-2.0.0" / "fixtures.json"
    fixtures = cast(list[_Fixture], json.loads(fixture_path.read_text(encoding="utf-8")))
    assert len(fixtures) == 78

    slugger = GithubSlugger()
    actual = [slugger.slug(fixture["input"]) for fixture in fixtures]

    assert actual == [fixture["expected"] for fixture in fixtures]


def test_github_slugger_pins_edge_cases_and_collision_bookkeeping() -> None:
    slugger = GithubSlugger()

    assert slugger.slug("Figma's Share Price") == "figmas-share-price"
    assert slugger.slug("S&P 500") == "sp-500"
    assert slugger.slug("Café Notes") == "café-notes"
    assert slugger.slug("Summary") == "summary"
    assert slugger.slug("Summary") == "summary-1"
    assert slugger.slug("summary-1") == "summary-1-1"
    assert slugger.slug("Summary") == "summary-2"
    assert slugger.slug("😄 emoji") == "-emoji"
    assert slugger.slug("Привет 世界") == "привет-世界"
    assert slugger.slug(" a ") == "-a-"
    assert slugger.slug("!!!") == ""
