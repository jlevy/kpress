"""Scan public package files for private filesystem paths and secret tokens."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ROOT = Path(__file__).resolve().parents[1]
COMMON_DOC_FOOTER = "This document follows common-doc-guidelines.md."
COMMON_DOC_EXEMPT_ROOTS = (
    ROOT / ".agents" / "skills",
    ROOT / ".claude" / "skills",
    ROOT / "examples" / "single-doc",
    ROOT / "examples" / "static-site" / "content",
    ROOT / "examples" / "wrapped-site" / "content",
    ROOT / "tests" / "e2e" / "docs",
    ROOT / "tests" / "fixtures",
)
COMMON_DOC_EXEMPT_FILES = {ROOT / "CLAUDE.md"}

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
    ".copier-answers.yml",
    ".flowmarkignore",
    ".gitignore",
    ".node-version",
    ".npmrc",
    ".nvmrc",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "Makefile",
    "NOTICE.md",
    "README.md",
    "SECURITY.md",
    "SUPPLY-CHAIN-SECURITY.md",
    "TODO.md",
    "package-lock.json",
    "package.json",
    "pyproject.toml",
    "lefthook.yml",
    "biome.json",
    "tsconfig.json",
    "uv.toml",
)

PUBLIC_DIRS: Final = (
    ".agents",
    ".claude",
    ".codex",
    ".github",
    "devtools",
    "docs",
    "examples",
    "src/kpress",
    "tests",
)

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

# Sizing contract (style-tokens.css SIZING POLICY, kpress-design.md "Sizing
# Policy"): every font size in first-party CSS derives from
# --kpress-font-size-base, so no font-size declaration or size token may
# reference rem. Layout lengths (measure, bands, margins) are deliberately
# root-relative and not covered by this rule; the one legitimate rem is the
# base knob's own default, which keeps standalone pages tracking the reader's
# browser font preference.
KPRESS_CSS_ROOT: Final = ROOT / "src" / "kpress" / "format" / "static" / "css"
SIZING_REM_ALLOWLIST: Final = frozenset(
    {"--kpress-font-size-base: var(--kpress-host-font-size-base, 1rem)"}
)
_SIZE_DECLARATION = re.compile(
    r"(?P<prop>--kpress-font-size[\w-]*|--kpress-bullet-size|(?<![\w-])font-size)"
    r"\s*:\s*(?P<value>[^;{}]*)"
)
_REM_UNIT = re.compile(r"[\d.]rem\b")


# Theme contract (style-tokens.css SELECTOR GRAMMAR, kpress-design.md): CSS
# keys on the resolved theme only. The mode attribute (data-kpress-theme) is
# resolver state and must never appear as an attribute selector; the widget
# control attribute data-kpress-theme-choice remains legitimate.
_MODE_ATTRIBUTE_SELECTOR = re.compile(r"\[data-kpress-theme(?![-\w])")


def find_theme_vocabulary_findings(path: Path, text: str) -> list[Finding]:
    """Flag attribute selectors on the theme MODE in a first-party stylesheet."""
    findings: list[Finding] = []
    for match in _MODE_ATTRIBUTE_SELECTOR.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        excerpt = text.splitlines()[line - 1].strip()
        findings.append(
            Finding(path=path, line=line, rule="mode-keyed-css", excerpt=excerpt)
        )
    return findings


def find_sizing_findings(path: Path, text: str) -> list[Finding]:
    """Flag rem-based font sizes and size tokens in a first-party stylesheet."""
    findings: list[Finding] = []
    for match in _SIZE_DECLARATION.finditer(text):
        value = match.group("value")
        if _REM_UNIT.search(value) is None:
            continue
        declaration = re.sub(r"\s+", " ", f"{match.group('prop')}: {value}").strip()
        if declaration in SIZING_REM_ALLOWLIST:
            continue
        findings.append(
            Finding(
                path=path,
                line=text.count("\n", 0, match.start()) + 1,
                rule="rem-font-size",
                excerpt=declaration,
            )
        )
    return findings


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
            try:
                path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            files.append(path)
            continue
        for child in path.rglob("*"):
            if child.is_file() and child.suffix in TEXT_SUFFIXES:
                files.append(child)
    return sorted(files)


def find_text_findings(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in RULE_PATTERNS:
            if pattern.search(line) is None:
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


def find_violations(paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_text_files(paths):
        text = path.read_text(encoding="utf-8")
        findings.extend(find_text_findings(path, text))
        if path.suffix == ".css" and path.is_relative_to(KPRESS_CSS_ROOT):
            findings.extend(find_sizing_findings(path, text))
            findings.extend(find_theme_vocabulary_findings(path, text))
    return findings


def find_documentation_findings(path: Path, text: str) -> list[str]:
    """Return common-document-policy findings for a repository file."""
    if path.suffix.lower() != ".md":
        return []
    if path in COMMON_DOC_EXEMPT_FILES:
        return []
    if any(path.is_relative_to(root) for root in COMMON_DOC_EXEMPT_ROOTS):
        return []
    if COMMON_DOC_FOOTER not in text:
        return [f"{_display_path(path, root=ROOT)}: missing common-doc-guidelines footer"]
    return []


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

    root = ROOT
    paths = args.paths or public_package_paths(root)
    findings = find_violations(paths)
    documentation_findings: list[str] = []
    for path in _iter_text_files(paths):
        documentation_findings.extend(
            find_documentation_findings(path, path.read_text(encoding="utf-8"))
        )
    if not findings and not documentation_findings:
        return 0

    for finding in findings:
        print(
            f"{_display_path(finding.path, root=root)}:{finding.line}: "
            f"{finding.rule}: {finding.excerpt}",
            file=sys.stderr,
        )
    for finding in documentation_findings:
        print(finding, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
