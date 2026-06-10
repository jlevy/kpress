"""PDF artifact generation contract for KPress."""

from __future__ import annotations

import importlib
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from types import TracebackType
from typing import Any, Literal, Protocol, cast

from kpress.errors import KPressMissingOptionalDependencyError
from kpress.format.model import RenderedPage
from kpress.output import write_bytes_atomic


@dataclass(frozen=True)
class PdfOptions:
    """Options for browser-print-style PDF output."""

    output: Path | None = None
    backend: Literal["minimal", "browser"] = "minimal"
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


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        stripped = " ".join(data.split())
        if stripped:
            self.parts.append(stripped)


# Single-line placeholder PDF can fit roughly this many escaped-text
# characters on one letter-sized page at 12pt Helvetica before the BT/ET
# stream stops being legible. The full document is always available in
# the matching HTML output; the minimal PDF is a smoke artifact, not a
# rendering target, so we truncate explicitly rather than line-wrap.
_MINIMAL_PDF_TEXT_BUDGET_CHARS = 2000


def _minimal_pdf_bytes(text: str) -> bytes:
    """Build a deterministic single-page placeholder PDF.

    Used when no browser backend is available (``backend="minimal"`` or
    the optional ``kpress[pdf]`` extra missing). Truncates text to
    ``_MINIMAL_PDF_TEXT_BUDGET_CHARS`` after escape; readers that need
    the full document should consult the paired HTML output.
    """

    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    safe = escaped[:_MINIMAL_PDF_TEXT_BUDGET_CHARS]
    stream = f"BT /F1 12 Tf 72 720 Td ({safe}) Tj ET"
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        f"5 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj",
    ]
    body = "%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(body.encode("latin-1")))
        body += obj + "\n"
    xref = len(body.encode("latin-1"))
    body += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    body += "".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
    body += f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    return body.encode("latin-1")


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
    """Generate a PDF artifact from rendered page HTML."""

    options = options or PdfOptions()
    if isinstance(page, Path):
        html = page.read_text(encoding="utf-8")
        output = options.output or page.with_suffix(".pdf")
        source_path = page
    else:
        html = page.html
        output = options.output or Path("kpress-output.pdf")
        source_path = None
    if options.backend == "browser":
        return _write_browser_pdf(
            html=html,
            source_path=source_path,
            output=output,
            options=options,
        )
    parser = _TextExtractor()
    parser.feed(html)
    data = _minimal_pdf_bytes(" ".join(parser.parts) or "KPress document")
    write_bytes_atomic(output, data)
    return PdfReport(path=output, bytes_written=len(data), backend="minimal-pdf")
