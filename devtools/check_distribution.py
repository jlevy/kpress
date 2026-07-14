"""Validate built KPress artifacts and a clean-wheel installation."""

from __future__ import annotations

import os
import subprocess
import tarfile
import zipfile
from pathlib import Path

from devtools.public_hygiene import RULE_PATTERNS

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
REPOSITORY_ONLY_PARTS = {
    ".agents",
    ".claude",
    ".codex",
    ".github",
    ".tbd",
    ".venv",
    "dist",
    "node_modules",
}
REPOSITORY_ONLY_NAMES = {".copier-answers.yml", "AGENTS.md", "CLAUDE.md"}


def _single_artifact(pattern: str, label: str) -> Path:
    artifacts = sorted(DIST.glob(pattern))
    if len(artifacts) != 1:
        raise RuntimeError(f"expected one {label} in dist/, found {len(artifacts)}")
    return artifacts[0]


def check_text_member(name: str, payload: bytes) -> None:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return
    findings: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in RULE_PATTERNS:
            if pattern.search(line) is not None:
                findings.append(f"{name}:{line_number}: {rule}")
    if findings:
        raise RuntimeError(f"artifact hygiene failed: {findings[:10]}")


def _inspect_wheel(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        required_suffixes = {
            "kpress/__init__.py",
            "kpress/format/static/css/document.css",
            "kpress/format/static/js/runtime.js",
            "kpress/format/static/fonts/pt-serif-latin-400-normal.woff2",
            "kpress/format/templates/page.html.jinja",
            "kpress/licenses/katex.txt",
        }
        for suffix in required_suffixes:
            if not any(name.endswith(suffix) for name in names):
                raise RuntimeError(f"wheel is missing {suffix}")
        forbidden_parts = REPOSITORY_ONLY_PARTS | {"tests", "devtools"}
        leaked = [name for name in names if forbidden_parts.intersection(Path(name).parts)]
        if leaked:
            raise RuntimeError(f"wheel contains repository-only files: {leaked[:10]}")
        for name in names:
            check_text_member(name, archive.read(name))


def _inspect_sdist(sdist: Path) -> None:
    with tarfile.open(sdist, "r:gz") as archive:
        members = [member for member in archive.getmembers() if member.isfile()]
        names = {member.name for member in members}
        required_suffixes = {
            "LICENSE",
            "README.md",
            "pyproject.toml",
            "src/kpress/format/static/js/runtime.js",
        }
        for suffix in required_suffixes:
            if not any(name.endswith(suffix) for name in names):
                raise RuntimeError(f"sdist is missing {suffix}")
        leaked = [
            name
            for name in names
            if REPOSITORY_ONLY_PARTS.intersection(Path(name).parts)
            or Path(name).name in REPOSITORY_ONLY_NAMES
        ]
        if leaked:
            raise RuntimeError(f"sdist contains repository-only files: {leaked[:10]}")
        for member in members:
            extracted = archive.extractfile(member)
            if extracted is not None:
                check_text_member(member.name, extracted.read())


def _smoke_install(wheel: Path) -> None:
    env = os.environ.copy()
    env.setdefault("UV_EXCLUDE_NEWER", "14 days")
    import_command = [
        "uv",
        "run",
        "--isolated",
        "--no-project",
        "--with",
        str(wheel),
        "python",
        "-c",
        (
            "from importlib.resources import files; import kpress; "
            "assert kpress.__version__; "
            "assert files('kpress').joinpath('format/static/js/runtime.js').is_file(); "
            "assert files('kpress').joinpath('format/templates/page.html.jinja').is_file()"
        ),
    ]
    subprocess.run(import_command, cwd=ROOT, env=env, check=True)
    subprocess.run(
        ["uv", "run", "--isolated", "--no-project", "--with", str(wheel), "kpress", "--help"],
        cwd=ROOT,
        env=env,
        check=True,
    )


def main() -> int:
    wheel = _single_artifact("kpress-*.whl", "wheel")
    sdist = _single_artifact("kpress-*.tar.gz", "sdist")
    _inspect_wheel(wheel)
    _inspect_sdist(sdist)
    _smoke_install(wheel)
    print(f"Distribution checks passed: {wheel.name}, {sdist.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
