"""KPress command line interface."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import cast

from kpress._version import __version__
from kpress.errors import KPressMissingOptionalDependencyError
from kpress.format import DocumentInput, RenderOptions, render_page
from kpress.output import write_text_atomic
from kpress.publish import BuildOptions, build_site
from kpress.publish.build import STANDALONE_ASSET_PREFIX, emit_standalone_assets
from kpress.publish.capability import CAPABILITY_NAMES, platform_info, probe_all
from kpress.publish.config import load_config
from kpress.publish.frontmatter import read_document_source
from kpress.publish.optimize import optimize_text
from kpress.workflow import convert_document, export_document, format_document, paste_document
from kpress.workflow.workspace import WORK_ROOT_MARKER, WorkflowResult, prepare_work_root


def _print_result(result: WorkflowResult) -> int:
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    return 0 if not result.diagnostics else 2


def _print_missing_extra(command: str, exc: KPressMissingOptionalDependencyError) -> int:
    print(
        json.dumps(
            {
                "command": command,
                "diagnostics": [str(exc)],
                "error": type(exc).__name__,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 2


def _cmd_init(args: argparse.Namespace) -> int:
    root = prepare_work_root(args.work_root)
    config = Path(args.config)
    if not config.exists():
        write_text_atomic(
            config,
            "sources:\n  - path: .\n\npublish:\n  output_dir: public\n",
        )
    return _print_result(WorkflowResult(command="init", work_root=root, outputs=[config]))


def _cmd_convert(args: argparse.Namespace) -> int:
    return _print_result(convert_document(args.input, output=args.output, work_root=args.work_root))


def _cmd_format(args: argparse.Namespace) -> int:
    return _print_result(
        format_document(
            args.input,
            output_dir=args.output_dir,
            work_root=args.work_root,
            asset_mode=args.asset_mode,
        )
    )


def _cmd_render(args: argparse.Namespace) -> int:
    """Render one Markdown input to a single KPress HTML file at ``--output``."""

    root = prepare_work_root(args.work_root)
    source = Path(args.input)
    doc = read_document_source(source)
    title = doc.metadata.get("title") or source.stem.replace("-", " ").title()
    page = render_page(
        DocumentInput(
            title=str(title),
            source_text=doc.body,
            body_markdown=doc.body,
            source_path=str(source),
            frontmatter=doc.metadata,
            sidematter=doc.sidematter,
        ),
        RenderOptions(asset_mode=args.asset_mode, asset_url_prefix=STANDALONE_ASSET_PREFIX),
    )
    output = Path(args.output) if args.output else root / "exports" / f"{source.stem}.html"
    write_text_atomic(output, page.html)
    asset_files = emit_standalone_assets(
        output, asset_mode=args.asset_mode, page=page, source=source
    )
    return _print_result(
        WorkflowResult(command="render", work_root=root, outputs=[output, *asset_files])
    )


def _cmd_paste(args: argparse.Namespace) -> int:
    return _print_result(paste_document(title=args.title, text=args.text, work_root=args.work_root))


def _cmd_files(args: argparse.Namespace) -> int:
    return _print_result(
        WorkflowResult(
            command="files",
            work_root=prepare_work_root(args.work_root),
            outputs=sorted(Path(args.work_root).rglob("*")),
        )
    )


def _cmd_export(args: argparse.Namespace) -> int:
    return _print_result(
        export_document(args.input, html=args.html, pdf=args.pdf, work_root=args.work_root)
    )


def _cmd_clean(args: argparse.Namespace) -> int:
    """Remove the build output directory and the work root.

    The output directory resolves relative to the config file (exactly like
    ``build_site``) and is only removed when it carries the KPress build
    manifest (or is empty). The work root is only removed when it has the
    default ``.kpress`` name or carries the KPress work-root marker. Anything
    else is refused so a misconfigured path can never delete unrelated files.
    """

    removed: list[Path] = []
    diagnostics: list[str] = []

    config_path = Path(args.config)
    if config_path.exists():
        config = load_config(str(config_path))
        base = (config.config_path.parent if config.config_path else Path.cwd()).resolve()
        output_dir = base / config.publish.output_dir
        if output_dir.is_dir():
            manifest = output_dir / "_kpress" / "kpress-manifest.json"
            if manifest.exists() or not any(output_dir.iterdir()):
                shutil.rmtree(output_dir)
                removed.append(output_dir)
            else:
                diagnostics.append(
                    f"Refusing to remove {output_dir}: it has no KPress build manifest "
                    "(_kpress/kpress-manifest.json). Remove it manually if intended."
                )

    work_root = Path(args.work_root)
    if work_root.is_dir():
        if work_root.name == ".kpress" or (work_root / WORK_ROOT_MARKER).exists():
            shutil.rmtree(work_root)
            removed.append(work_root)
        else:
            diagnostics.append(
                f"Refusing to remove work root {work_root}: it is not named .kpress and "
                f"has no {WORK_ROOT_MARKER} marker. Remove it manually if intended."
            )

    print(
        json.dumps(
            {
                "command": "clean",
                "diagnostics": diagnostics,
                "removed": [str(path) for path in removed],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 2 if diagnostics else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kpress",
        description="Render Markdown into polished HTML documents and publish static sites.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--work-root", default=".kpress", help="Workspace directory for outputs.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Write a starter kpress.yml config.")
    init.add_argument("--config", default="kpress.yml")
    init.set_defaults(func=_cmd_init)

    convert = sub.add_parser("convert", help="Copy a Markdown-compatible input into the workspace.")
    convert.add_argument("input")
    convert.add_argument("--output")
    convert.set_defaults(func=_cmd_convert)

    # `inline` is deliberately not offered: it is not yet self-contained.
    asset_mode_choices = ["hosted", "linked", "hashed"]

    fmt = sub.add_parser(
        "format", help="Render a Markdown file to paired Markdown and HTML outputs."
    )
    fmt.add_argument("input")
    fmt.add_argument("--output-dir")
    fmt.add_argument("--asset-mode", choices=asset_mode_choices, default="linked")
    fmt.set_defaults(func=_cmd_format)

    render = sub.add_parser("render", help="Render one Markdown input to a single HTML file.")
    render.add_argument("input")
    render.add_argument("--output")
    render.add_argument("--asset-mode", choices=asset_mode_choices, default="linked")
    render.set_defaults(func=_cmd_render)

    paste = sub.add_parser("paste", help="Create a document from pasted or piped text.")
    paste.add_argument("--title", default="Pasted Document")
    paste.add_argument("--text")
    paste.set_defaults(func=_cmd_paste)

    files = sub.add_parser("files", help="List files in the work root.")
    files.set_defaults(func=_cmd_files)

    export = sub.add_parser("export", help="Export a document to HTML and optional PDF.")
    export.add_argument("input")
    export.add_argument("--html")
    export.add_argument("--pdf")
    export.set_defaults(func=_cmd_export)

    clean = sub.add_parser("clean", help="Remove the build output directory and work root.")
    clean.add_argument("--config", default="kpress.yml")
    clean.set_defaults(func=_cmd_clean)

    build = sub.add_parser("build", help="Build the static site from kpress.yml.")
    build.add_argument("--config", default="kpress.yml")
    build.add_argument("--output-dir")
    build.add_argument("--asset-mode", choices=asset_mode_choices)
    build.add_argument("--optimizer", choices=["none", "full"])
    build.add_argument("--precompress", action="append", choices=["gzip", "br"])
    build.set_defaults(func=_cmd_build)

    optimize = sub.add_parser("optimize", help="Minify an HTML/CSS/JS file.")
    optimize.add_argument("input")
    optimize.add_argument("--output")
    optimize.add_argument("--kind", choices=["html", "css", "js"], default="html")
    optimize.add_argument("--backend", choices=["none", "full"], default="none")
    optimize.set_defaults(func=_cmd_optimize)

    doctor = sub.add_parser(
        "doctor", help="Probe optional capabilities (render, publish, optimizer, PDF)."
    )
    doctor.add_argument("--profile", choices=["render", "publish", "optimize", "pdf"])
    doctor.add_argument("--config")
    doctor.add_argument("--allow-network", action="store_true")
    doctor.add_argument("--json", action="store_true", dest="as_json")
    doctor.set_defaults(func=_cmd_doctor)

    return parser


def _cmd_build(args: argparse.Namespace) -> int:
    try:
        report = build_site(
            args.config,
            BuildOptions(
                output_dir=Path(args.output_dir) if args.output_dir else None,
                asset_mode=args.asset_mode,
                optimizer=args.optimizer,
                precompress=args.precompress,
            ),
        )
    except KPressMissingOptionalDependencyError as exc:
        return _print_missing_extra("build", exc)
    print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    return 0


def _cmd_optimize(args: argparse.Namespace) -> int:
    source = Path(args.input)
    output = Path(args.output) if args.output else source
    try:
        optimized = optimize_text(
            source.read_text(encoding="utf-8"),
            kind=args.kind,
            backend=args.backend,
        )
    except KPressMissingOptionalDependencyError as exc:
        return _print_missing_extra("optimize", exc)
    write_text_atomic(output, optimized)
    print(
        json.dumps(
            {
                "backend": args.backend,
                "kind": args.kind,
                "output": str(output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


_DOCTOR_LABELS = {
    "render": "Core render",
    "publish": "Static publish",
    "optimizer_full": "Optimizer full",
    "precompress_brotli": "Brotli precompress",
    "pdf_browser": "PDF browser",
}
_PROFILE_CAPABILITY = {
    "render": "render",
    "publish": "publish",
    "optimize": "optimizer_full",
    "pdf": "pdf_browser",
}


def _required_capabilities(config_path: str) -> set[str]:
    """Capabilities the resolved config actually exercises."""

    config = load_config(config_path)
    required = {"render", "publish"}
    if config.optimizer.mode == "full":
        required.add("optimizer_full")
    if "br" in config.optimizer.precompress:
        required.add("precompress_brotli")
    if config.pdf.enabled:
        required.add("pdf_browser")
    return required


def _cmd_doctor(args: argparse.Namespace) -> int:
    results = probe_all(allow_network=args.allow_network)

    required: set[str]
    if args.profile:
        required = {_PROFILE_CAPABILITY[args.profile]}
    elif args.config:
        required = _required_capabilities(args.config)
    else:
        required = set()  # bare discovery never fails

    if args.as_json:
        payload = {
            **platform_info(),
            "capabilities": {
                name: (
                    {"status": r.status, "reason": r.reason} if r.reason else {"status": r.status}
                )
                for name, r in results.items()
            },
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for name in CAPABILITY_NAMES:
            r = results[name]
            detail = f" - {r.reason}" if r.reason else ""
            print(f"{_DOCTOR_LABELS[name] + ':':<20}{r.status}{detail}")

    failed = [n for n in required if results[n].status != "ok"]
    return 2 if failed else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = cast(Callable[[argparse.Namespace], int], args.func)
    try:
        return handler(args)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
