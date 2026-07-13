"""Local document conversion workflow.

KPress core only knows how to *copy* inputs that are already Markdown (or plain text
that is valid as Markdown) into the workspace. KPress 0.1.0 does not advertise format
conversion extras: HTML, DOCX, PDF, and other source formats must be converted
externally before calling :func:`convert_document`.
"""

from __future__ import annotations

from pathlib import Path

from kpress.output import write_text_atomic
from kpress.workflow.workspace import WorkflowResult, prepare_work_root

# Inputs that can be copied verbatim into the workspace as Markdown. Plain
# text is included because it parses correctly as Markdown (the body is just
# treated as text), so users running `kpress convert notes.txt` get a `.md`
# workspace file with the same content rather than a confusing diagnostic.
_PASSTHROUGH_SUFFIXES = frozenset({".md", ".markdown", ".txt"})

# Inputs that require conversion outside KPress 0.1.0.
_UNSUPPORTED_CONVERSION_SUFFIXES = frozenset({".html", ".htm", ".docx", ".pdf", ".rst"})


def convert_document(
    input_path: Path | str, *, output: Path | str | None = None, work_root: Path | str = ".kpress"
) -> WorkflowResult:
    """Copy a Markdown-compatible local input into the workspace.

    ``.md``/``.markdown``/``.txt`` are copied verbatim and renamed to
    ``.md`` in the workspace. Any other extension returns a workspace
    result with a diagnostic directing the caller to convert externally and writes
    nothing. KPress does not advertise optional extras that do not exist.
    """

    root = prepare_work_root(work_root)
    source = Path(input_path)
    suffix = source.suffix.lower()

    if suffix in _UNSUPPORTED_CONVERSION_SUFFIXES:
        return WorkflowResult(
            command="convert",
            work_root=root,
            diagnostics=[
                f"Converting {suffix} to Markdown is not supported by KPress 0.1.0. "
                "Convert the source to Markdown with an external tool, then pass the "
                "result to KPress."
            ],
        )

    if suffix not in _PASSTHROUGH_SUFFIXES:
        return WorkflowResult(
            command="convert",
            work_root=root,
            diagnostics=[
                f"Cannot convert {suffix or 'extension-less'} input: no built-in handler "
                f"and no known optional extra. Supported inputs: "
                f"{sorted(_PASSTHROUGH_SUFFIXES)}."
            ],
        )

    text = source.read_text(encoding="utf-8")
    dest = Path(output) if output else root / "workspace" / (source.stem + ".md")
    write_text_atomic(dest, text)
    return WorkflowResult(command="convert", work_root=root, outputs=[dest])
