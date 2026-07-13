"""Hygiene scan over the public package files: no private filesystem paths,
no secret tokens. Runs in the lint gate and pre-commit."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

TEXT_SUFFIXES: Final = {
    ".css",
    ".html",
    ".jinja",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yml",
}

PUBLIC_ROOT_FILES: Final = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    "NOTICE.md",
    "README.md",
    "SECURITY.md",
    "TODO.md",
    # docs/*.md files are covered by the "docs" entry in PUBLIC_DIRS; listing
    # them here too would scan them twice and duplicate findings.
    "pyproject.toml",
    "package.json",
    "lefthook.yml",
    "biome.json",
    "tsconfig.json",
)

PUBLIC_DIRS: Final = (".agents", "docs", "examples", "src/kpress", "tests")

RULE_PATTERNS: Final = (
    (
        "private-path",
        re.compile(r"(?:/Users|/home)/[^\s)\"'`>]+|~/(?:wrk|work|src|private)/[^\s)\"'`>]+"),
    ),
    (
        "secret-token",
        re.compile(
            r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"
            r"|\bAKIA[0-9A-Z]{16}\b"
            r"|\bghp_[A-Za-z0-9_]{20,}\b"
            r"|\bgithub_pat_[A-Za-z0-9_]{20,}\b"
            r"|\bsk-[A-Za-z0-9_-]{20,}\b"
            r"|\bxox[baprs]-[A-Za-z0-9-]{20,}\b"
        ),
    ),
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str
    excerpt: str


def public_package_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for rel in PUBLIC_ROOT_FILES:
        path = root / rel
        if path.exists():
            paths.append(path)
    for rel in PUBLIC_DIRS:
        path = root / rel
        if path.exists():
            paths.append(path)
    return paths


def _iter_text_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            if path.suffix in TEXT_SUFFIXES:
                files.append(path)
            continue
        for child in path.rglob("*"):
            if child.is_file() and child.suffix in TEXT_SUFFIXES:
                files.append(child)
    return sorted(files)


def find_violations(paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_text_files(paths):
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for rule, pattern in RULE_PATTERNS:
                match = pattern.search(line)
                if match is None:
                    continue
                findings.append(
                    Finding(
                        path=path,
                        line=line_number,
                        rule=rule,
                        excerpt=line.strip(),
                    )
                )
    return findings


def _display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Specific files or directories to scan. Defaults to public KPress package files.",
    )
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    paths = args.paths or public_package_paths(root)
    findings = find_violations(paths)
    if not findings:
        return 0

    for finding in findings:
        print(
            f"{_display_path(finding.path, root=root)}:{finding.line}: "
            f"{finding.rule}: {finding.excerpt}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
