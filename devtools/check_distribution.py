"""Validate built KPress artifacts and a clean-wheel installation."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

from devtools.public_hygiene import find_documentation_findings, find_text_findings

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
    path = Path(name)
    findings = find_text_findings(path, text)
    if findings:
        summaries = [f"{name}:{finding.line}: {finding.rule}" for finding in findings]
        raise RuntimeError(f"artifact hygiene failed: {summaries[:10]}")
    if path.name == "README.md" and find_documentation_findings(path, text):
        raise RuntimeError(f"artifact documentation footer is missing: {name}")


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


def _run_smoke_command(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"installed wheel command failed: {shlex.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def _smoke_install(wheel: Path) -> None:
    env = os.environ.copy()
    env.setdefault("UV_EXCLUDE_NEWER", "14 days")
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    uv = ["uv", "--config-file", str(ROOT / "uv.toml")]
    with tempfile.TemporaryDirectory(prefix="kpress-wheel-") as temp_dir:
        temp = Path(temp_dir)
        venv = temp / "venv"
        subprocess.run([*uv, "venv", str(venv), "--python", sys.executable], env=env, check=True)
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        executable = venv / ("Scripts/kpress.exe" if os.name == "nt" else "bin/kpress")
        subprocess.run(
            [*uv, "pip", "install", "--python", str(python), str(wheel)],
            env=env,
            check=True,
        )

        site = temp / "site"
        site.mkdir()
        (site / "index.md").write_text(
            "# Wheel smoke\n\nBuilt outside the checkout.\n", encoding="utf-8"
        )
        (site / "kpress.yml").write_text(
            "sources:\n  - path: .\npublish:\n  output_dir: public\n  asset_mode: hashed\n",
            encoding="utf-8",
        )
        _run_smoke_command(
            [
                str(python),
                "-c",
                (
                    "from importlib.resources import files; import kpress; "
                    "assert kpress.__version__; "
                    "assert files('kpress').joinpath('format/static/js/runtime.js').is_file(); "
                    "assert files('kpress').joinpath('format/templates/page.html.jinja').is_file()"
                ),
            ],
            cwd=site,
            env=env,
        )
        for args in (["--version"], ["--help"], ["doctor"], ["build"]):
            _run_smoke_command([str(executable), *args], cwd=site, env=env)

        public = site / "public"
        required_outputs = (
            public / "index.html",
            public / "_kpress" / "kpress-manifest.json",
            public / "_kpress" / "assets" / "css",
            public / "_kpress" / "assets" / "js",
            public / "_kpress" / "assets" / "fonts",
        )
        missing = [str(path.relative_to(site)) for path in required_outputs if not path.exists()]
        if missing:
            raise RuntimeError(f"installed wheel smoke is missing outputs: {missing}")


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
