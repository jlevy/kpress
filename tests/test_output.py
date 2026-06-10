from __future__ import annotations

from pathlib import Path

import pytest

from kpress.output import atomic_output_path, write_bytes_atomic, write_text_atomic


def test_write_text_atomic_creates_parent_and_file(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "doc.html"

    write_text_atomic(target, "<h1>Hi</h1>\n")

    assert target.read_text(encoding="utf-8") == "<h1>Hi</h1>\n"


def test_write_bytes_atomic_creates_parent_and_file(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "doc.pdf"

    write_bytes_atomic(target, b"%PDF-1.4\n")

    assert target.read_bytes() == b"%PDF-1.4\n"


def test_atomic_output_path_preserves_existing_file_on_error(tmp_path: Path) -> None:
    target = tmp_path / "out.txt"
    target.write_text("old\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="boom"):
        with atomic_output_path(target) as tmp_path:
            tmp_path.write_text("new\n", encoding="utf-8")
            raise RuntimeError("boom")

    assert target.read_text(encoding="utf-8") == "old\n"
