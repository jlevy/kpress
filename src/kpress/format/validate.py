"""Validation helpers for KPress public contracts."""

from __future__ import annotations

from kpress.format.model import Diagnostic, DocumentInput


def validate_document_input(document: DocumentInput) -> list[Diagnostic]:
    """Return diagnostics for invalid-but-recoverable document input."""

    diagnostics: list[Diagnostic] = []
    if not document.title.strip():
        diagnostics.append(Diagnostic(type="missing_title", message="Document title is empty."))
    if not document.source_path.strip():
        diagnostics.append(
            Diagnostic(type="missing_source_path", message="Document source path is empty.")
        )
    if document.body_markdown is None and document.body_html is None and not document.source_text:
        diagnostics.append(
            Diagnostic(type="empty_document", message="Document has no renderable content.")
        )
    return diagnostics
