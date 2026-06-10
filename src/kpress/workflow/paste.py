"""Clipboard paste workflow boundary."""

from __future__ import annotations

from pathlib import Path

from kpress.output import write_text_atomic
from kpress.workflow.workspace import WorkflowResult, prepare_work_root


def paste_document(
    *, title: str = "Pasted Document", text: str | None = None, work_root: Path | str = ".kpress"
) -> WorkflowResult:
    """Create a document from explicit text or report the missing clipboard extra."""

    root = prepare_work_root(work_root)
    if text is None:
        return WorkflowResult(
            command="paste",
            work_root=root,
            diagnostics=["Missing optional clipboard extra for clipboard paste."],
        )
    dest = root / "workspace" / (title.lower().replace(" ", "-") + ".md")
    write_text_atomic(dest, text)
    return WorkflowResult(command="paste", work_root=root, outputs=[dest])
