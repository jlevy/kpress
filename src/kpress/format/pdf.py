"""PDF artifact generation contract for KPress."""

from __future__ import annotations

import importlib
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Any, Protocol, cast

from kpress.errors import KPressMissingOptionalDependencyError
from kpress.format.model import RenderedPage
from kpress.output import write_bytes_atomic


@dataclass(frozen=True)
class PdfOptions:
    """Options for browser-print-style PDF output."""

    output: Path | None = None
    page_size: str = "Letter"
    print_background: bool = True


@dataclass(frozen=True)
class PdfReport:
    """Report for a generated PDF artifact."""

    path: Path
    bytes_written: int
    backend: str


class _PdfPage(Protocol):
    def goto(self, url: str, *, wait_until: str) -> None: ...

    def emulate_media(self, *, media: str) -> None: ...

    def pdf(self, *, path: str, format: str, print_background: bool) -> None: ...


class _PdfBrowser(Protocol):
    def new_page(self) -> _PdfPage: ...

    def close(self) -> None: ...


class _PdfChromium(Protocol):
    @property
    def executable_path(self) -> str: ...

    def launch(self) -> _PdfBrowser: ...


class _PdfPlaywright(Protocol):
    @property
    def chromium(self) -> _PdfChromium: ...


class _PdfPlaywrightContext(Protocol):
    def __enter__(self) -> _PdfPlaywright: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None: ...


def _sync_playwright() -> _PdfPlaywrightContext:
    # Access Playwright through an Any-typed importlib handle: the optional
    # dependency is absent in CI, so a direct typed import resolves to
    # Unknown and trips basedpyright (reportMissingImports /
    # reportUnknownVariableType).
    try:
        sync_api = cast(Any, importlib.import_module("playwright.sync_api"))
    except ModuleNotFoundError as exc:
        raise KPressMissingOptionalDependencyError(
            "Browser PDF backend requires the optional Playwright dependency. "
            "Install `kpress[pdf]` and run `playwright install chromium`."
        ) from exc
    return cast(_PdfPlaywrightContext, cast(object, sync_api.sync_playwright()))


def _write_browser_pdf(
    *,
    html: str,
    source_path: Path | None,
    output: Path,
    options: PdfOptions,
) -> PdfReport:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kpress-pdf-") as temp_dir:
        html_path = (
            source_path.resolve() if source_path is not None else Path(temp_dir) / "kpress-pdf.html"
        )
        if source_path is None:
            html_path.write_text(html, encoding="utf-8")
        pdf_path = Path(temp_dir) / "kpress-output.pdf"
        with _sync_playwright() as playwright:
            chromium_path = Path(playwright.chromium.executable_path)
            if not chromium_path.is_file():
                raise KPressMissingOptionalDependencyError(
                    "Browser PDF export requires Playwright Chromium. "
                    "Run `playwright install chromium`."
                )
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page()
                page.goto(html_path.as_uri(), wait_until="networkidle")
                page.emulate_media(media="print")
                page.pdf(
                    path=str(pdf_path),
                    format=options.page_size,
                    print_background=options.print_background,
                )
            finally:
                browser.close()
        # Browser PDFs are document-sized artifacts; copy through memory so the
        # final output still uses KPress's atomic write boundary.
        write_bytes_atomic(output, pdf_path.read_bytes())
    return PdfReport(
        path=output,
        bytes_written=output.stat().st_size,
        backend="browser-pdf",
    )


def render_pdf(page: RenderedPage | Path, options: PdfOptions | None = None) -> PdfReport:
    """Generate a browser-rendered PDF artifact from rendered page HTML.

    PDF export is never emulated with a placeholder. Missing Playwright or Chromium
    raises ``KPressMissingOptionalDependencyError`` with the required setup.
    """

    options = options or PdfOptions()
    if isinstance(page, Path):
        html = page.read_text(encoding="utf-8")
        output = options.output or page.with_suffix(".pdf")
        source_path = page
    else:
        html = page.html
        output = options.output or Path("kpress-output.pdf")
        source_path = None
    return _write_browser_pdf(
        html=html,
        source_path=source_path,
        output=output,
        options=options,
    )
