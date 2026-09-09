from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from pytest import MonkeyPatch

import kpress.format.pdf as pdf_module
from kpress.errors import KPressMissingOptionalDependencyError


def test_browser_pdf_backend_reports_missing_playwright(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    html_path = tmp_path / "doc.html"
    html_path.write_text("<h1>PDF</h1>", encoding="utf-8")

    def missing_playwright() -> object:
        raise KPressMissingOptionalDependencyError(
            "Install `kpress[pdf]` and run `playwright install chromium`."
        )

    monkeypatch.setattr(pdf_module, "_sync_playwright", missing_playwright)

    try:
        pdf_module.render_pdf(
            html_path,
            pdf_module.PdfOptions(output=tmp_path / "doc.pdf"),
        )
    except KPressMissingOptionalDependencyError as exc:
        assert "playwright install chromium" in str(exc)
    else:
        raise AssertionError("browser PDF backend should report missing Playwright")


def test_browser_pdf_backend_reports_missing_chromium(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    html_path = tmp_path / "doc.html"
    html_path.write_text("<h1>PDF</h1>", encoding="utf-8")

    class FakeChromium:
        executable_path = str(tmp_path / "missing-chromium")

    class FakePlaywright:
        chromium = FakeChromium()

        def __enter__(self) -> FakePlaywright:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
            return False

    monkeypatch.setattr(pdf_module, "_sync_playwright", lambda: FakePlaywright())

    with pytest.raises(KPressMissingOptionalDependencyError, match="install chromium"):
        pdf_module.render_pdf(html_path, pdf_module.PdfOptions(output=tmp_path / "doc.pdf"))


def test_browser_pdf_backend_uses_playwright_print_pipeline(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    html_path = tmp_path / "doc.html"
    html_path.write_text("<!doctype html><h1>PDF</h1>", encoding="utf-8")
    events: list[tuple[object, ...]] = []
    chromium_path = tmp_path / "chromium"
    chromium_path.touch()

    class FakePage:
        def goto(self, url: str, *, wait_until: str) -> None:
            events.append(("goto", url, wait_until))

        def emulate_media(self, *, media: str) -> None:
            events.append(("media", media))

        def evaluate(self, expression: str, arg: object = None) -> object:
            events.append(("evaluate", "document.fonts.ready" in expression, arg))
            return None

        def pdf(self, *, path: str, format: str, print_background: bool) -> None:
            events.append(("pdf", Path(path).name, format, print_background))
            Path(path).write_bytes(b"%PDF-1.4\n% browser\n")

    class FakeBrowser:
        def new_page(self) -> FakePage:
            events.append(("new_page",))
            return FakePage()

        def close(self) -> None:
            events.append(("close",))

    class FakeChromium:
        executable_path = str(chromium_path)

        def launch(self) -> FakeBrowser:
            events.append(("launch",))
            return FakeBrowser()

    class FakePlaywright:
        chromium = FakeChromium()

        def __enter__(self) -> FakePlaywright:
            events.append(("enter",))
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
            events.append(("exit",))
            return False

    monkeypatch.setattr(pdf_module, "_sync_playwright", lambda: FakePlaywright())

    report = pdf_module.render_pdf(
        html_path,
        pdf_module.PdfOptions(
            output=tmp_path / "doc.pdf",
            page_size="A4",
            print_background=False,
        ),
    )

    assert report.backend == "browser-pdf"
    assert report.bytes_written == report.path.stat().st_size
    assert report.path.read_bytes().startswith(b"%PDF-1.4")
    assert ("media", "print") in events
    assert ("pdf", "kpress-output.pdf", "A4", False) in events
    # The print faces have to finish loading between the media switch and the print:
    # the static instances are declared inside `@media print`, and the `@page` margin
    # boxes need their families asked for by name.
    names = [event[0] for event in events]
    assert names.index("media") < names.index("evaluate") < names.index("pdf")
    readiness = next(event for event in events if event[0] == "evaluate")
    assert readiness[1] is True, readiness
    tokens, sample, timeout_ms = cast(tuple[list[str], str, int], readiness[2])
    assert tokens == [
        ("--kpress-font-sans", "--kpress-font-weight-sans-regular"),
        ("--kpress-font-prose", "--_kpress-font-weight-prose"),
    ], readiness
    assert sample.strip(), readiness
    # Bounded: a face that never answers prints as it did before the wait existed.
    assert timeout_ms > 0, readiness
    assert any(
        event[0] == "goto"
        and isinstance(event[1], str)
        and event[1].startswith("file://")
        and event[2] == "networkidle"
        for event in events
    )
    assert ("close",) in events
    assert events[-1] == ("exit",)
