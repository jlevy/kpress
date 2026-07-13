"""Unit coverage for the three small workflow modules.

`workflow/{convert,workspace,paste}.py` are small (~30 LOC each) but they are
the surface a user/agent hits via the `kpress` CLI, so they deserve focused
tests that pin behavior — passthrough vs missing-extra diagnostics, file
naming, and workspace layout. The CLI tests in test_kpress_cli.py exercise
the integration; these are the unit-level guarantees the CLI tests assume.
"""

from __future__ import annotations

from pathlib import Path

from kpress.workflow import convert_document, paste_document
from kpress.workflow.workspace import WorkflowResult, prepare_work_root

# --- workspace.prepare_work_root ------------------------------------------


def test_prepare_work_root_creates_expected_layout(tmp_path: Path) -> None:
    root = prepare_work_root(tmp_path / "kpress-ws")
    assert root == tmp_path / "kpress-ws"
    for child in ("cache", "workspace", "exports", "assets"):
        assert (root / child).is_dir(), f"missing workspace child {child!r}"


def test_prepare_work_root_is_idempotent(tmp_path: Path) -> None:
    """Calling twice on the same dir must not raise (mkdir(parents,
    exist_ok)). Pre-existing files inside the children are preserved."""

    root = tmp_path / "kpress-ws"
    prepare_work_root(root)
    sentinel = root / "workspace" / "preexisting.md"
    sentinel.write_text("# preserved\n", encoding="utf-8")

    prepare_work_root(root)

    assert sentinel.is_file()
    assert sentinel.read_text(encoding="utf-8") == "# preserved\n"


def test_workflow_result_as_dict_is_json_safe(tmp_path: Path) -> None:
    result = WorkflowResult(
        command="paste",
        work_root=tmp_path,
        outputs=[tmp_path / "a.md", tmp_path / "b.md"],
        diagnostics=["one", "two"],
    )
    payload = result.as_dict()
    assert payload == {
        "command": "paste",
        "work_root": str(tmp_path),
        "outputs": [str(tmp_path / "a.md"), str(tmp_path / "b.md")],
        "diagnostics": ["one", "two"],
    }


# --- workflow.convert_document --------------------------------------------


def test_convert_document_passes_markdown_through(tmp_path: Path) -> None:
    src = tmp_path / "input.md"
    src.write_text("# Hello\n\nBody.\n", encoding="utf-8")

    result = convert_document(src, work_root=tmp_path / ".kpress")

    assert result.command == "convert"
    assert result.diagnostics == []
    assert len(result.outputs) == 1
    out = result.outputs[0]
    assert out.name == "input.md"
    assert out.read_text(encoding="utf-8") == "# Hello\n\nBody.\n"


def test_convert_document_renames_txt_to_md_and_passes_through(tmp_path: Path) -> None:
    src = tmp_path / "plain.txt"
    src.write_text("paragraph one\n\nparagraph two\n", encoding="utf-8")

    result = convert_document(src, work_root=tmp_path / ".kpress")

    assert result.diagnostics == []
    out = result.outputs[0]
    assert out.name == "plain.md"
    assert out.read_text(encoding="utf-8") == "paragraph one\n\nparagraph two\n"


def test_convert_document_html_emits_clear_unsupported_diagnostic(tmp_path: Path) -> None:
    """The earlier behavior of replacing <br> with \\n in HTML was a near-empty
    pseudo-conversion that silently misled users. Now we state the public support
    boundary, write no output, and let the caller choose an external converter."""

    src = tmp_path / "page.html"
    src.write_text(
        "<html><body><p>One.<br>Two.</p><h1>Heading</h1></body></html>",
        encoding="utf-8",
    )

    result = convert_document(src, work_root=tmp_path / ".kpress")

    assert result.outputs == []
    assert len(result.diagnostics) == 1
    assert "not supported by KPress 0.1.0" in result.diagnostics[0]
    assert "external tool" in result.diagnostics[0]
    # No fake "converted" output left behind.
    assert not (tmp_path / ".kpress" / "workspace" / "page.md").exists()


def test_convert_document_unknown_extension_lists_supported_inputs(tmp_path: Path) -> None:
    src = tmp_path / "weird.xyz"
    src.write_text("data", encoding="utf-8")

    result = convert_document(src, work_root=tmp_path / ".kpress")

    assert result.outputs == []
    assert len(result.diagnostics) == 1
    diag = result.diagnostics[0]
    assert ".xyz" in diag
    assert ".md" in diag
    assert ".html" not in diag


def test_convert_document_honors_explicit_output_path(tmp_path: Path) -> None:
    src = tmp_path / "in.md"
    src.write_text("# X\n", encoding="utf-8")
    out = tmp_path / "custom" / "deeply" / "out.md"

    result = convert_document(src, output=out, work_root=tmp_path / ".kpress")

    assert result.outputs == [out]
    assert out.read_text(encoding="utf-8") == "# X\n"


# --- workflow.paste_document ----------------------------------------------


def test_paste_document_writes_titled_workspace_file(tmp_path: Path) -> None:
    result = paste_document(
        title="Q3 Earnings Notes",
        text="# Q3\n\nBody.\n",
        work_root=tmp_path / ".kpress",
    )

    assert result.command == "paste"
    assert result.diagnostics == []
    out = result.outputs[0]
    # Title is slugified by lowercasing + replacing spaces with hyphens.
    assert out.name == "q3-earnings-notes.md"
    assert out.read_text(encoding="utf-8") == "# Q3\n\nBody.\n"


def test_paste_document_without_text_reports_missing_clipboard_extra(tmp_path: Path) -> None:
    """The CLI does not bundle a clipboard reader yet; without explicit text the
    workflow must surface the missing extra rather than crash."""

    result = paste_document(work_root=tmp_path / ".kpress")

    assert result.outputs == []
    assert len(result.diagnostics) == 1
    assert "clipboard" in result.diagnostics[0]
