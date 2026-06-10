"""Local KPress document workflows."""

from __future__ import annotations

from kpress.workflow.convert import convert_document
from kpress.workflow.export import export_document
from kpress.workflow.format import format_document
from kpress.workflow.paste import paste_document
from kpress.workflow.workspace import WorkflowResult, prepare_work_root

__all__ = [
    "WorkflowResult",
    "convert_document",
    "export_document",
    "format_document",
    "paste_document",
    "prepare_work_root",
]
