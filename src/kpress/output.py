"""Atomic output helpers for KPress-generated files."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from strif import atomic_output_file as _atomic_output_file


@contextmanager
def atomic_output_path(path: Path | str) -> Generator[Path]:
    """Yield a temp path that atomically replaces *path* on successful exit."""

    with _atomic_output_file(path, make_parents=True) as tmp_path:
        yield tmp_path


def write_text_atomic(path: Path | str, text: str, *, encoding: str = "utf-8") -> None:
    """Write text to *path* via an atomic same-directory replacement."""

    with atomic_output_path(path) as tmp_path:
        tmp_path.write_text(text, encoding=encoding)


def write_bytes_atomic(path: Path | str, data: bytes) -> None:
    """Write bytes to *path* via an atomic same-directory replacement."""

    with atomic_output_path(path) as tmp_path:
        tmp_path.write_bytes(data)
