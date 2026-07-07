"""Build-pipeline plugin tests (docs/kpress-design.md "Extension and Injection
Model", layer E): ordered stage plugins + tree/page-HTML transforms."""

from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path

import pytest

from kpress.format.model import DocumentTree, TocEntry
from kpress.publish import BuildExtensions, build_site
from kpress.publish.optimize import NoneOptimizer, OptimizerResult, resolve_stage


class RecordingStage:
    """A minimal stage: the existing OptimizerBackend shape."""

    def __init__(self, name: str, suffix: str) -> None:
        self.name = name
        self.suffix = suffix
        self.kinds: list[str] = []

    def optimize(self, content: str, *, kind: str) -> OptimizerResult:
        self.kinds.append(kind)
        if kind != "html":
            return OptimizerResult(content=content, backend=self.name, changed=False)
        new = content.replace("</body>", f"<!--{self.suffix}--></body>")
        return OptimizerResult(content=new, backend=self.name, changed=new != content)


def _write_site(tmp_path: Path) -> Path:
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "index.md").write_text(
        "# Alpha\n\nBody text.\n\n## Beta\n\nMore.\n", encoding="utf-8"
    )
    config = tmp_path / "kpress.yml"
    config.write_text(
        f"sources:\n  - path: {tmp_path / 'content'}\n"
        f"publish:\n  output_dir: {tmp_path / 'public'}\n",
        encoding="utf-8",
    )
    return config


def test_resolve_stage_builtin_names_and_unknown() -> None:
    from kpress.errors import KPressPublishError

    assert isinstance(resolve_stage("kpress:none"), NoneOptimizer)
    assert resolve_stage("kpress:full").name == "full"

    custom = RecordingStage("custom", "c")
    assert resolve_stage(custom) is custom

    with pytest.raises(KPressPublishError, match="kpress:none"):
        resolve_stage("bogus")


def test_pipeline_stages_run_in_order_and_manifest_records_names(tmp_path: Path) -> None:
    config = _write_site(tmp_path)
    first = RecordingStage("one", "one")
    second = RecordingStage("two", "two")

    report = build_site(config, extensions=BuildExtensions(pipeline=[first, second]))

    html = (tmp_path / "public" / "index.html").read_text(encoding="utf-8")
    # Both stages ran, in list order (one's comment precedes two's).
    assert "<!--one--><!--two--></body>" in html
    # Stages also saw the package assets (css/js kinds).
    assert "css" in first.kinds and "js" in first.kinds
    # The manifest records the joined stage names for the rewritten page.
    page_files = [f for f in report.files if f.path == "index.html"]
    assert page_files and page_files[0].optimizer_backend == "one+two"


def test_transform_page_html_stamps_each_page(tmp_path: Path) -> None:
    config = _write_site(tmp_path)

    def stamp(html: str, route: str) -> str:
        return html.replace("</body>", f"<!--route:{route}--></body>")

    build_site(config, extensions=BuildExtensions(transform_page_html=stamp))

    html = (tmp_path / "public" / "index.html").read_text(encoding="utf-8")
    assert "<!--route:/-->" in html


def test_transform_tree_is_reflected_in_toc_and_page_model(tmp_path: Path) -> None:
    config = _write_site(tmp_path)

    def add_entry(tree: DocumentTree) -> DocumentTree:
        return dataclasses.replace(
            tree, toc=[*tree.toc, TocEntry(level=2, title="Injected Entry", href="#injected")]
        )

    build_site(config, extensions=BuildExtensions(transform_tree=add_entry))

    html = (tmp_path / "public" / "index.html").read_text(encoding="utf-8")
    match = re.search(
        r'<script type="application/json" id="kpress-page-model">(.*?)</script>', html, re.DOTALL
    )
    assert match
    model = json.loads(match.group(1))
    titles = [h["title"] for h in model["headings"]]
    assert "Injected Entry" in titles


def test_no_extensions_matches_default_build(tmp_path: Path) -> None:
    config = _write_site(tmp_path)
    build_site(config)
    plain = (tmp_path / "public" / "index.html").read_bytes()

    build_site(config, extensions=BuildExtensions())
    assert (tmp_path / "public" / "index.html").read_bytes() == plain


def test_public_pipeline_stage_names_resolve() -> None:
    from kpress.contract import PUBLIC_PIPELINE_STAGES

    for name in PUBLIC_PIPELINE_STAGES:
        assert resolve_stage(name).name in {"none", "full"}
