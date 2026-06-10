"""Local document conversion workflow.

KPress core only knows how to *copy* inputs that are already Markdown (or
plain text that is valid as Markdown) into the workspace. Real format
conversion (HTML → Markdown, DOCX → Markdown, PDF → Markdown, etc.)
requires an optional extra with the right library (e.g. ``html2text``,
``markdownify``, ``pandoc``). Until those extras exist,
:func:`convert_document` copies the passthrough cases and surfaces a
missing-extra diagnostic for everything else.
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

# Inputs that need a real converter behind an optional extra. The extra
# isn't built yet — we emit a clear diagnostic instead of a fake conversion.
_NEEDS_CONVERTER_EXTRA = {
    ".html": "kpress[convert-html]",
    ".htm": "kpress[convert-html]",
    ".docx": "kpress[convert-office]",
    ".pdf": "kpress[convert-pdf]",
    ".rst": "kpress[convert-rst]",
}


def convert_document(
    input_path: Path | str, *, output: Path | str | None = None, work_root: Path | str = ".kpress"
) -> WorkflowResult:
    """Copy a Markdown-compatible local input into the workspace.

    ``.md``/``.markdown``/``.txt`` are copied verbatim and renamed to
    ``.md`` in the workspace. Any other extension returns a workspace
    result with a diagnostic naming the optional extra that would
    provide the conversion (``kpress[convert-html]``,
    ``kpress[convert-office]``, ``kpress[convert-pdf]``, etc.) and
    writes nothing.
    """

    root = prepare_work_root(work_root)
    source = Path(input_path)
    suffix = source.suffix.lower()

    if suffix in _NEEDS_CONVERTER_EXTRA:
        extra = _NEEDS_CONVERTER_EXTRA[suffix]
        return WorkflowResult(
            command="convert",
            work_root=root,
            diagnostics=[
                f"Converting {suffix} to Markdown requires the {extra} optional extra "
                f"(not yet implemented in KPress core)."
            ],
        )

    if suffix not in _PASSTHROUGH_SUFFIXES:
        return WorkflowResult(
            command="convert",
            work_root=root,
            diagnostics=[
                f"Cannot convert {suffix or 'extension-less'} input: no built-in handler "
                f"and no known optional extra. Supported inputs: "
                f"{sorted(_PASSTHROUGH_SUFFIXES | _NEEDS_CONVERTER_EXTRA.keys())}."
            ],
        )

    text = source.read_text(encoding="utf-8")
    dest = Path(output) if output else root / "workspace" / (source.stem + ".md")
    write_text_atomic(dest, text)
    return WorkflowResult(command="convert", work_root=root, outputs=[dest])
