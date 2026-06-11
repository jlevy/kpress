"""Dynamic-vs-sealed equivalence tests for the full reader fixture corpus.

Each fixture document is rendered through both the dynamic path (render_page)
and the production sealed path (build_site with inline assets), then the
normalized document surfaces are compared.  Accepted differences are limited to
URL shape, hashing, minification, compression, and documented optimizations.
"""

from __future__ import annotations

from pathlib import Path

from .equivalence_helpers import (
    EquivalenceResult,
    assert_content_equivalence,
    assert_equivalence,
    discover_fixtures,
)


def test_fixture_corpus_is_nonempty() -> None:
    fixtures = discover_fixtures()
    assert len(fixtures) >= 3, f"expected at least 3 fixtures, got {len(fixtures)}"


def test_minimal_structural_equivalence(tmp_path: Path) -> None:
    fixtures = discover_fixtures()
    minimal = next(f for f in fixtures if f.name == "minimal")
    assert_equivalence(minimal, tmp_path / "minimal")


def test_rich_components_structural_equivalence(tmp_path: Path) -> None:
    fixtures = discover_fixtures()
    rich = next(f for f in fixtures if f.name == "rich-components")
    assert_equivalence(rich, tmp_path / "rich")


def test_semantic_components_structural_equivalence(tmp_path: Path) -> None:
    fixtures = discover_fixtures()
    semantic = next(f for f in fixtures if f.name == "semantic-components")
    assert_equivalence(semantic, tmp_path / "semantic")


def test_full_corpus_structural_equivalence(tmp_path: Path) -> None:
    fixtures = discover_fixtures()
    results: list[EquivalenceResult] = []
    for fixture in fixtures:
        work = tmp_path / fixture.name
        work.mkdir(parents=True, exist_ok=True)
        result = assert_equivalence(fixture, work)
        results.append(result)
    assert all(r.passed for r in results)


def test_minimal_content_equivalence(tmp_path: Path) -> None:
    fixtures = discover_fixtures()
    minimal = next(f for f in fixtures if f.name == "minimal")
    assert_content_equivalence(minimal, tmp_path / "minimal")


def test_rich_components_content_equivalence(tmp_path: Path) -> None:
    fixtures = discover_fixtures()
    rich = next(f for f in fixtures if f.name == "rich-components")
    assert_content_equivalence(rich, tmp_path / "rich")


def test_semantic_components_content_equivalence(tmp_path: Path) -> None:
    fixtures = discover_fixtures()
    semantic = next(f for f in fixtures if f.name == "semantic-components")
    assert_content_equivalence(semantic, tmp_path / "semantic")


def test_full_corpus_content_equivalence(tmp_path: Path) -> None:
    fixtures = discover_fixtures()
    results: list[EquivalenceResult] = []
    for fixture in fixtures:
        work = tmp_path / fixture.name
        work.mkdir(parents=True, exist_ok=True)
        result = assert_content_equivalence(fixture, work)
        results.append(result)
    assert all(r.passed for r in results)


def test_page_model_comparison_catches_model_drift() -> None:
    """The harness compares page models structurally (route normalized away):
    a parity break in any other model field must surface as a difference."""

    import json

    from .equivalence_helpers import page_model_differences

    def page(model: dict[str, object]) -> str:
        return (
            '<html><body><script type="application/json" id="kpress-page-model">'
            + json.dumps(model)
            + "</script></body></html>"
        )

    base: dict[str, object] = {
        "version": 1,
        "title": "Doc",
        "route": "/a",
        "profile": "document",
        "headings": [{"level": 1, "title": "Beta", "href": "#beta"}],
        "widgets": {"settings": "on"},
    }
    assert page_model_differences(page(base), page({**base, "route": "/b"})) == []

    drifted: dict[str, object] = {**base, "title": "Other", "widgets": {}}
    differences = page_model_differences(page(base), page(drifted))
    assert any("title" in diff for diff in differences)
    assert any("widgets" in diff for diff in differences)
    assert not any("route" in diff for diff in differences)
