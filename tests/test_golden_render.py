from __future__ import annotations

from .golden_helpers import KPRESS_ROOT, assert_matches_golden, load_scenario, render_scenario


def test_document_page_goldens() -> None:
    scenarios = sorted((KPRESS_ROOT / "tests/golden/scenarios").glob("*.yaml"))
    assert scenarios
    for scenario_path in scenarios:
        scenario = load_scenario(scenario_path)
        actual = render_scenario(scenario)
        expected = KPRESS_ROOT / "tests/golden/accepted" / scenario.name / "page.html"
        assert_matches_golden(actual, expected)


def test_minimal_document_page_golden_path_is_stable() -> None:
    scenario = load_scenario(KPRESS_ROOT / "tests/golden/scenarios/minimal-doc.yaml")
    assert_matches_golden(
        render_scenario(scenario),
        KPRESS_ROOT / "tests/golden/accepted/minimal-doc/page.html",
    )
