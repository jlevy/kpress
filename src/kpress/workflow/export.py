"""Local document export workflow."""

from __future__ import annotations

from pathlib import Path

from kpress.output import write_text_atomic
from kpress.workflow.format import format_document
from kpress.workflow.workspace import WorkflowResult, prepare_work_root


def export_document(
    input_path: Path | str,
    *,
    html: Path | str | None = None,
    pdf: Path | str | None = None,
    docx: Path | str | None = None,
    work_root: Path | str = ".kpress",
) -> WorkflowResult:
    """Export a local document to HTML and optional artifacts."""

    root = prepare_work_root(work_root)
    result = format_document(
        input_path, output_dir=Path(html).parent if html else None, work_root=root
    )
    outputs = list(result.outputs)
    html_out = next(path for path in outputs if path.suffix == ".html")
    if html:
        target = Path(html)
        write_text_atomic(target, html_out.read_text(encoding="utf-8"))
        outputs.append(target)
        html_out = target
    diagnostics: list[str] = []
    if pdf:
        from kpress.format.pdf import PdfOptions, render_pdf

        report = render_pdf(html_out, PdfOptions(output=Path(pdf)))
        outputs.append(report.path)
    if docx:
        diagnostics.append("Missing optional office extra for DOCX export.")
    return WorkflowResult(
        command="export", work_root=root, outputs=outputs, diagnostics=diagnostics
    )
