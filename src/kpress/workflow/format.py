"""Local document formatting workflow."""

from __future__ import annotations

from pathlib import Path

from kpress.format import AssetMode, DocumentInput, RenderOptions, render_page
from kpress.output import write_text_atomic
from kpress.publish.build import STANDALONE_ASSET_PREFIX, emit_standalone_assets
from kpress.workflow.workspace import WorkflowResult, prepare_work_root


def format_document(
    input_path: Path | str,
    *,
    output_dir: Path | str | None = None,
    work_root: Path | str = ".kpress",
    asset_mode: AssetMode = "linked",
) -> WorkflowResult:
    """Render a local Markdown file to paired Markdown and KPress HTML outputs.

    ``asset_mode`` is an explicit independent lever (see kpress-design.md
    "Combinations under evaluation"); it is not a coarse build mode.
    """

    root = prepare_work_root(work_root)
    source = Path(input_path)
    out_dir = Path(output_dir) if output_dir else root / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    markdown = source.read_text(encoding="utf-8")
    md_out = out_dir / f"{source.stem}.md"
    html_out = out_dir / f"{source.stem}.html"
    write_text_atomic(md_out, markdown)
    page = render_page(
        DocumentInput(
            title=source.stem.replace("-", " ").title(),
            source_text=markdown,
            body_markdown=markdown,
            source_path=str(source),
        ),
        RenderOptions(asset_mode=asset_mode, asset_url_prefix=STANDALONE_ASSET_PREFIX),
    )
    write_text_atomic(html_out, page.html)
    # Emit the referenced package bundle beside the HTML so the formatted
    # document opens with its CSS/JS without a separate asset server.
    asset_files = emit_standalone_assets(html_out, asset_mode=asset_mode, page=page, source=source)
    return WorkflowResult(
        command="format", work_root=root, outputs=[md_out, html_out, *asset_files]
    )
