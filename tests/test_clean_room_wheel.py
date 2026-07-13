"""Clean-room wheel gate: the built wheel must work outside the monorepo.

Builds the kpress wheel, installs it into a fresh venv, and renders/builds in
a scratch directory with no repo imports — proving package data (CSS, JS,
fonts, icon sprite, KaTeX, templates) ships in the wheel and resolves via
``importlib.resources``. This is the v0.1 publishability gate (orig-wp8v).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

_KPRESS_DIR = Path(__file__).resolve().parents[1]

needs_uv = pytest.mark.skipif(shutil.which("uv") is None, reason="clean-room gate requires uv")

_CLEAN_ROOM_SCRIPT = """
import sys
from pathlib import Path

import kpress

# The interpreter must resolve kpress from the venv, never the repo checkout.
location = Path(kpress.__file__).resolve()
assert "site-packages" in str(location), f"kpress resolved outside the venv: {location}"

from kpress.format import DocumentInput, RenderOptions, render_page

page = render_page(
    DocumentInput(
        title="Clean Room",
        source_text="# Clean Room\\n\\nProse with `code`.",
        body_markdown="# Clean Room\\n\\nProse with `code`.",
        source_path="index.md",
    ),
    RenderOptions(asset_mode="linked"),
)
assert "kpress-icon-settings" in page.html, "icon sprite missing from rendered page"
assert "<style>" in page.html, "inlined page reset missing"

from kpress.publish import build_site

report = build_site("kpress.yml")
out = Path("public")
assert (out / "index.html").is_file()
assets = out / "_kpress" / "assets"
for sub in ("css", "js", "fonts"):
    found = list((assets / sub).glob("*"))
    assert found, f"no {sub} assets emitted from the installed wheel"
assert report.routes, "no routes in build report"
print("clean-room-ok")
"""


@needs_uv
def test_wheel_installs_and_builds_in_clean_venv(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    build = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(dist)],
        cwd=_KPRESS_DIR,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert build.returncode == 0, f"uv build failed:\n{build.stderr}"
    wheels = list(dist.glob("kpress-*.whl"))
    assert len(wheels) == 1, f"expected one wheel, got {wheels}"

    venv_dir = tmp_path / "venv"
    subprocess.run(["uv", "venv", str(venv_dir)], capture_output=True, check=True, timeout=120)
    python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    install = subprocess.run(
        ["uv", "pip", "install", "--python", str(python), str(wheels[0])],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert install.returncode == 0, f"wheel install failed:\n{install.stderr}"

    site = tmp_path / "site"
    site.mkdir()
    (site / "index.md").write_text("# Clean Room\n\nProse with `code`.\n", encoding="utf-8")
    (site / "kpress.yml").write_text(
        "sources:\n  - path: .\npublish:\n  output_dir: public\n  asset_mode: hashed\n",
        encoding="utf-8",
    )
    env = {
        key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "VIRTUAL_ENV"}
    }
    run = subprocess.run(
        [str(python), "-c", _CLEAN_ROOM_SCRIPT],
        cwd=site,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
        env=env,
    )
    assert run.returncode == 0, f"clean-room script failed:\n{run.stdout}\n{run.stderr}"
    assert "clean-room-ok" in run.stdout
