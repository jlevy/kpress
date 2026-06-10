from __future__ import annotations

from html.parser import HTMLParser

from kpress.format import DocumentInput, RenderOptions, render_page


class _IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.classes: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        _ = tag
        for name, value in attrs:
            if name == "id" and value:
                self.ids.append(value)
            if name == "class" and value:
                self.classes.update(value.split())


def test_rendered_page_has_stable_document_structure() -> None:
    page = render_page(
        DocumentInput(
            title="Contract",
            # No body H1, so the title header renders (its `kpress-metadata`
            # class is part of the structure asserted below).
            source_text="## Section\n\nText[^a]\n\n[^a]: Note",
            body_markdown="## Section\n\nText[^a]\n\n[^a]: Note",
            source_path="contract.md",
        ),
        RenderOptions(include_toc="on"),
    )
    parser = _IdCollector()
    parser.feed(page.html)

    assert len(parser.ids) == len(set(parser.ids))
    assert {
        "kpress",
        "kpress-doc",
        "kpress-metadata",
        "kpress-print-surface",
        "kpress-footnotes",
    } <= parser.classes
    assert "#section" in page.html
    assert "fn-a" in parser.ids
