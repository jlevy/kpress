"""KPress static build pipeline."""

from __future__ import annotations

import json
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

from kpress.errors import KPressPublishError
from kpress.format import DocumentInput, RenderedPage, RenderOptions, render_page
from kpress.format.assets import content_hash, package_asset_output_path
from kpress.format.model import AssetMode, DiagramMode, OptimizerMode, ThemeMode
from kpress.models import KPressExportRequest
from kpress.output import write_bytes_atomic, write_text_atomic
from kpress.publish.config import (
    BuildExtensions,
    BuildOptions,
    KPressConfig,
    load_config,
    validate_config,
)
from kpress.publish.discover import config_base_dir, discover_sources, discover_static_files
from kpress.publish.frontmatter import DocumentSource, read_document_source, route_override
from kpress.publish.manifest import BuildReport, ManifestAsset, OutputFile
from kpress.publish.optimize import (
    ContentKind,
    FullOptimizer,
    NoneOptimizer,
    OptimizerBackend,
    optimize_text,
    precompress_file,
    resolve_stage,
)
from kpress.publish.routes import (
    RoutePlanEntry,
    plan_site_routes,
    reserved_output_reason,
    route_for_source,
)
from kpress.publish.seal import copy_katex_assets, copy_package_assets
from kpress.publish.site_files import write_site_files


def _base_dir(config: KPressConfig) -> Path:
    # One resolver for all three anchors (sources, output, asset boundary):
    # discovery and the build must never disagree on where the project tree is.
    return config_base_dir(config)


def package_asset_prefix(base_url: str) -> str:
    """Return the root-relative package-asset prefix for a deployment.

    A path-bearing ``base_url`` (e.g. ``https://site.example/docs/``) is a
    subpath deployment: package assets live under that path
    (``/docs/_kpress/assets/``) so the same root-relative URLs resolve there.
    A bare host or empty ``base_url`` keeps the site-root prefix.
    """

    path = urlparse(base_url).path.strip("/") if base_url else ""
    if not path:
        return "/_kpress/assets/"
    return f"/{path}/_kpress/assets/"


def _output_dir(config: KPressConfig, options: BuildOptions | None) -> Path:
    if options and options.output_dir:
        return options.output_dir
    return _base_dir(config) / config.publish.output_dir


def _asset_mode(config: KPressConfig, options: BuildOptions | None) -> AssetMode:
    if options and options.asset_mode:
        return options.asset_mode
    return config.publish.resolved_asset_mode()


def _optimizer(config: KPressConfig, options: BuildOptions | None) -> OptimizerMode:
    """Resolve the optimizer mode. Default is ``none`` (no Node required)."""

    if options and options.optimizer is not None:
        return options.optimizer
    return config.optimizer.mode


def _precompress(config: KPressConfig, options: BuildOptions | None) -> list[str]:
    """Precompression is explicit and orthogonal: off unless requested.

    It is independent of the optimizer and needs no Node.
    """

    if options and options.precompress is not None:
        return options.precompress
    return list(config.optimizer.precompress)


def _resolve_pipeline(
    extensions: BuildExtensions | None, optimizer: OptimizerMode
) -> list[OptimizerBackend]:
    """The ordered stage list for this build.

    A host pipeline (BuildExtensions.pipeline) wins; otherwise the list derives
    from optimizer.mode — `none` is an empty pipeline (byte-identical output),
    `full` is the single built-in `kpress:full` stage. Identity stages
    (NoneOptimizer) are dropped: they change nothing and would pollute the
    manifest's stage names.
    """

    if extensions is not None and extensions.pipeline is not None:
        stages = [resolve_stage(stage) for stage in extensions.pipeline]
    elif optimizer == "none":
        stages = []
    elif optimizer == "full":
        stages = [resolve_stage("kpress:full")]
    else:
        # An unknown mode must never fall through to the full optimizer: a
        # typo'd cast-away value would silently rewrite every artifact.
        msg = f"Invalid optimizer.mode {optimizer!r}; expected one of 'none', 'full'"
        raise KPressPublishError(msg)
    return [stage for stage in stages if not isinstance(stage, NoneOptimizer)]


def _run_stages(stages: list[OptimizerBackend], content: str, kind: str) -> tuple[str, str | None]:
    """Run the pipeline over one artifact; return (content, joined names).

    The joined names cover stages that actually changed the content (the
    manifest's `optimizer_backend`); None when nothing was rewritten.
    """

    normalized = cast(ContentKind, kind if kind in {"html", "css", "js"} else "other")
    applied: list[str] = []
    for stage in stages:
        try:
            result = stage.optimize(content, kind=normalized)
        except Exception as e:
            # Prior outputs were already purged when stages run, so a bare
            # stage traceback leaves the operator with nothing actionable:
            # name the failing stage and artifact kind.
            msg = f"Build pipeline stage {stage.name!r} failed on a {kind!r} artifact: {e}"
            raise KPressPublishError(msg) from e
        if result.changed:
            applied.append(stage.name)
        content = result.content
    return content, "+".join(applied) if applied else None


def _asset_optimizer(stages: list[OptimizerBackend]) -> Callable[[str, str], str] | None:
    if not stages:
        return None

    def optimize_asset(content: str, kind: str) -> str:
        content, _names = _run_stages(stages, content, kind)
        return content

    return optimize_asset


def _package_asset_rewrites(
    assets: list[ManifestAsset], *, asset_mode: AssetMode
) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    for asset in assets:
        if asset.source != "package" or asset.output_path.startswith("inline:"):
            continue
        old = package_asset_output_path(asset.path, mode=asset_mode)
        new = asset.output_path.removeprefix("_kpress/assets/")
        if old != new:
            rewrites[old] = new
    return rewrites


def _rewrite_package_asset_urls(html: str, rewrites: dict[str, str]) -> str:
    for old, new in sorted(rewrites.items(), key=lambda item: len(item[0]), reverse=True):
        html = html.replace(f"/_kpress/assets/{old}", f"/_kpress/assets/{new}")
    return html


def _output_file(
    path: Path,
    output_dir: Path,
    *,
    kind: str | None = None,
    original_size: int | None = None,
    optimizer_backend: str | None = None,
) -> OutputFile:
    data = path.read_bytes()
    return OutputFile(
        path=path.relative_to(output_dir).as_posix(),
        kind=kind or path.suffix.lstrip("."),
        content_hash=content_hash(data),
        size=len(data),
        original_size=original_size,
        optimizer_backend=optimizer_backend,
    )


# Author media that the Markdown body references but the source globs (`**/*.md`) do
# not collect. Copied verbatim into the output so figures/embeds resolve.
_DOCUMENT_ASSET_SUFFIXES = frozenset(
    {
        ".svg",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".avif",
        ".ico",
        ".bmp",
        ".mp4",
        ".webm",
        ".ogg",
        ".mp3",
        ".wav",
    }
)
_ASSET_REF_RE = re.compile(r'(?:src|href|content)="([^"]+)"')


def _collect_document_assets(
    html: str,
    *,
    source: Path,
    out_path: Path,
    output_dir: Path,
    base: Path,
    copied: set[Path],
) -> list[Path]:
    """Copy local media referenced by a rendered document into the build output.

    KPress sources collect Markdown only, so author media referenced via
    ``![](assets/x.svg)`` or raw ``<img>``/``<iframe>`` is never picked up by the
    glob. This copies each relative media reference, preserving its path so the
    document's own relative URLs keep resolving. Only relative refs to existing files
    inside the project tree, with a known media suffix, are copied; external URLs,
    anchors, and generated page routes are skipped.
    """
    results: list[Path] = []
    source_dir = source.parent.resolve()
    out_dir = out_path.parent.resolve()
    output_dir_resolved = output_dir.resolve()
    base_resolved = base.resolve()
    raw_refs: list[str] = _ASSET_REF_RE.findall(html)
    for raw_ref in raw_refs:
        ref = raw_ref.split("#", 1)[0].split("?", 1)[0]
        if not ref or ref.startswith(("/", "data:", "mailto:", "tel:")):
            continue
        parsed = urlparse(ref)
        if parsed.scheme or parsed.netloc:
            continue
        if Path(ref).suffix.lower() not in _DOCUMENT_ASSET_SUFFIXES:
            continue
        src_asset = (source_dir / ref).resolve()
        if not src_asset.is_file() or not src_asset.is_relative_to(base_resolved):
            continue
        dest_resolved = (out_dir / ref).resolve()
        if not dest_resolved.is_relative_to(output_dir_resolved) or dest_resolved in copied:
            continue
        # Copy to the unresolved path under output_dir so callers can take
        # `relative_to(output_dir)` without tripping over symlinked temp roots.
        dest = out_path.parent / ref
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_asset, dest)
        copied.add(dest_resolved)
        results.append(dest)
    return results


def _source_root_for(config: KPressConfig, base: Path, source: Path) -> Path:
    roots = [(base / item.path).resolve() for item in config.sources]
    for idx, root in enumerate(roots):
        if source.resolve().is_relative_to(root):
            return root if idx == 0 else base
    return roots[0] if roots else base


def _precompress_outputs(
    output_dir: Path, files: list[OutputFile], methods: list[str]
) -> list[OutputFile]:
    outputs: list[OutputFile] = []
    if not methods:
        return outputs
    for file in files:
        if file.kind not in {"html", "css", "js", "json"}:
            continue
        source = output_dir / file.path
        source_relpath = file.path
        for compressed in precompress_file(source, methods=methods):
            destination = source.with_name(compressed.path)
            rel_path = destination.relative_to(output_dir).as_posix()
            data = destination.read_bytes()
            outputs.append(
                OutputFile(
                    path=rel_path,
                    kind=compressed.kind,
                    content_hash=content_hash(data),
                    size=len(data),
                    compression=compressed.compression,
                    source_path=source_relpath,
                )
            )
    return outputs


def _purge_prior_kpress_outputs(output_dir: Path) -> None:
    """Delete KPress-owned outputs from a previous build of this site.

    Reads the previous build's manifest (`_kpress/kpress-manifest.json`) and
    removes only those files KPress claimed to own — page HTML, manifests,
    sitemap/robots/_redirects, and the package `_kpress/` asset tree.
    Files in `output_dir` that aren't in the prior manifest (operator
    additions, screenshots, deploy metadata) are untouched.

    On a first build (no prior manifest) this is a no-op. On a build that
    crashed mid-write previously, the partial `_kpress/` tree is still
    purged because we always wipe that subtree wholesale — it's
    package-owned.
    """

    if not output_dir.exists():
        return

    manifest_path = output_dir / "_kpress" / "kpress-manifest.json"
    prior_files: list[str] = []
    if manifest_path.is_file():
        try:
            data: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        files_field: object = data.get("files", [])
        if isinstance(files_field, list):
            for entry in cast("list[object]", files_field):
                if isinstance(entry, dict):
                    entry_dict = cast("dict[str, object]", entry)
                    path = entry_dict.get("path")
                    if isinstance(path, str):
                        prior_files.append(path)

    output_dir_resolved = output_dir.resolve()

    # Wipe the package-owned `_kpress/` infrastructure tree wholesale.
    kpress_dir = output_dir / "_kpress"
    if kpress_dir.exists():
        shutil.rmtree(kpress_dir, ignore_errors=True)

    # Delete each previously-claimed file, plus the site-files KPress writes
    # outside `_kpress/` (sitemap/robots/_redirects).
    candidates = set(prior_files) | {"sitemap.xml", "robots.txt", "_redirects"}
    for rel in candidates:
        if not rel or rel.startswith("_kpress/"):
            continue  # already wiped above or empty
        target = (output_dir / rel).resolve()
        # Defense in depth: never delete a path that resolves outside output_dir.
        if not target.is_relative_to(output_dir_resolved):
            continue
        if target.is_file():
            target.unlink()
        # Clean up newly-empty parent dirs up to output_dir, but never delete
        # output_dir itself or anything outside it.
        parent = target.parent
        while parent != output_dir_resolved and parent.is_relative_to(output_dir_resolved):
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent


def _copy_static_passthrough(
    config: KPressConfig,
    route_plan: list[RoutePlanEntry],
    output_dir: Path,
) -> list[OutputFile]:
    """Copy ``sources[].static`` files verbatim into the output tree.

    Each file lands at its source-relative path. Reserved paths and collisions
    with rendered routes or other static files are hard errors; like rendered
    pages, nothing may resolve outside ``output_dir``.
    """

    rendered_outputs = {entry.output_path.as_posix().lower(): entry for entry in route_plan}
    seen: dict[str, Path] = {}
    output_dir_resolved = output_dir.resolve()
    copied: list[OutputFile] = []
    for static_file, root in discover_static_files(config):
        # Source-root boundary: a symlink matched by a static glob must not
        # publish bytes from outside its source root (local-file leak).
        if not static_file.resolve().is_relative_to(root.resolve()):
            msg = (
                f"Static file {static_file} resolves to {static_file.resolve()}, "
                f"outside its source root {root}; refusing to publish it"
            )
            raise KPressPublishError(msg)
        rel = static_file.relative_to(root).as_posix()
        reason = reserved_output_reason(rel)
        if reason is not None:
            msg = f"Static file {static_file} resolves to {rel} which {reason}"
            raise KPressPublishError(msg)
        key = rel.lower()
        page = rendered_outputs.get(key)
        if page is not None:
            msg = (
                f"Static file {static_file} collides with the rendered page for "
                f"{page.source} at {rel}"
            )
            raise KPressPublishError(msg)
        other = seen.get(key)
        if other is not None and other != static_file:
            msg = f"Static files {other} and {static_file} both resolve to {rel}"
            raise KPressPublishError(msg)
        seen[key] = static_file
        destination = output_dir / rel
        if not destination.resolve().is_relative_to(output_dir_resolved):
            msg = f"Refusing to copy {static_file}: {rel} resolves outside {output_dir_resolved}"
            raise KPressPublishError(msg)
        write_bytes_atomic(destination, static_file.read_bytes())
        copied.append(_output_file(destination, output_dir))
    return copied


def build_site(
    config: KPressConfig | Path | str = "kpress.yml",
    options: BuildOptions | None = None,
    extensions: BuildExtensions | None = None,
) -> BuildReport:
    """Build a static KPress site.

    ``config`` is either a path to a ``kpress.yml`` file or a ``KPressConfig``
    constructed in Python — the library-call path: typed fields instead of
    YAML, chrome slots as plain strings (no ``*_file`` indirection, no
    escaping). Programmatic configs should use absolute source/output paths and
    set ``base_dir`` (the anchor for relative paths and the document-asset
    boundary that a config file's directory would otherwise provide).

    ``extensions`` is the host's build-pipeline seam (ordered stage plugins +
    tree/page-HTML transforms); omitted, the build derives its single stage
    from ``optimizer.mode`` exactly as before.
    """

    if not isinstance(config, KPressConfig):
        config = load_config(config)
    # Semantic invariants hold for BOTH dialects: a typed config must fail as
    # loudly as a YAML one (inline asset mode, widget-value typos) and publish
    # identical page-model data (presence scalars normalized).
    config = validate_config(config)
    base = _base_dir(config)
    output_dir = _output_dir(config, options)
    optimizer = _optimizer(config, options)
    stages = _resolve_pipeline(extensions, optimizer)

    # Preflight: verify the full optimizer toolchain before writing any output.
    if any(isinstance(stage, FullOptimizer) for stage in stages):
        from kpress.publish.capability import preflight_optimizer_full

        preflight_optimizer_full()

    output_dir.mkdir(parents=True, exist_ok=True)
    # Delete KPress-owned outputs from the previous build before writing this
    # one. Without this, deleting a source file leaves its rendered HTML in
    # `output_dir` forever — the static publish output stops being a pure
    # function of the current inputs (orig-8qo4). We only delete files
    # listed in the prior manifest (plus the `_kpress/` infrastructure tree
    # we own); user files that happen to share the directory are untouched.
    _purge_prior_kpress_outputs(output_dir)
    asset_mode = _asset_mode(config, options)
    precompress = _precompress(config, options)
    asset_optimizer = _asset_optimizer(stages)
    files: list[OutputFile] = []
    assets: list[ManifestAsset] = []
    routes: dict[str, str] = {}
    copied_assets: set[Path] = set()
    any_math = False
    package_files, package_assets = copy_package_assets(
        output_dir, asset_mode=asset_mode, optimizer=asset_optimizer
    )
    package_rewrites = _package_asset_rewrites(package_assets, asset_mode=asset_mode)
    files.extend(package_files)
    assets.extend(package_assets)

    source_roots = [
        (source, _source_root_for(config, base, source)) for source in discover_sources(config)
    ]
    doc_sources: dict[Path, DocumentSource] = {
        source: read_document_source(source) for source, _root in source_roots
    }
    overrides: dict[Path, str] = {}
    for source, root in source_roots:
        base_route = route_for_source(source, root=root.resolve())
        override = route_override(doc_sources[source].metadata, base_route=base_route)
        if override is not None:
            overrides[source] = override
    route_plan = plan_site_routes(source_roots, output_dir, overrides=overrides)
    files.extend(_copy_static_passthrough(config, route_plan, output_dir))
    asset_prefix = package_asset_prefix(config.base_url)
    lastmods: dict[str, str] = (
        {entry.route: config.build_date for entry in route_plan} if config.build_date else {}
    )
    output_dir_resolved = output_dir.resolve()
    for entry in route_plan:
        source = entry.source
        route = entry.route
        out_path = output_dir / entry.output_path
        # Defense in depth: even though `validate_public_route` already
        # rejects traversal at the source, refuse to write any page that
        # resolves outside `output_dir`. Stops a future bug in any other
        # code path (slug override, source-derived routing, custom
        # publishers) from escaping the output tree.
        if not out_path.resolve().is_relative_to(output_dir_resolved):
            msg = (
                f"Refusing to write {out_path} for route {route!r}: "
                f"resolves outside output_dir {output_dir_resolved}"
            )
            raise KPressPublishError(msg)
        doc = doc_sources[source]
        title = doc.metadata.get("title") or source.stem.replace("-", " ").title()
        page = render_page(
            DocumentInput(
                title=str(title),
                source_text=doc.body,
                body_markdown=doc.body,
                source_path=str(source),
                logical_path=route,
                frontmatter=doc.metadata,
                sidematter=doc.sidematter,
                trust_mode="sanitized",
            ),
            RenderOptions(
                asset_url_prefix=asset_prefix,
                asset_mode=asset_mode,
                palette=config.format.palette,
                prose_font=config.format.prose_font,
                content_card=config.format.content_card,
                show_doc_header=config.format.show_doc_header,
                include_toc=config.format.toc,
                toc_min_headings=config.format.toc_min_headings,
                math=config.format.math,
                # diagrams/color_mode are validated against _DIAGRAM_MODES/_COLOR_MODES
                # in validate_config, so the value is a valid DiagramMode/ThemeMode here;
                # the FormatConfig fields are typed plainly (str) and named color_mode.
                diagrams=cast(DiagramMode, config.format.diagrams),
                theme_mode=cast(ThemeMode, config.format.color_mode),
                show_frontmatter=config.format.show_frontmatter,
                widgets=config.format.widgets,
                extra_tags=config.format.extra_tags,
                extra_attributes=config.format.extra_attributes,
                transform_tree=extensions.transform_tree if extensions else None,
                head_extra_html=config.head_extra_html,
                header_html=config.header_html,
                footer_html=config.footer_html,
            ),
        )
        any_math = any_math or page.has_math
        rendered_html = _rewrite_package_asset_urls(page.html, package_rewrites)
        # Whole-page host transform (BuildExtensions.transform_page_html),
        # applied before the pipeline stages so stages see the final page.
        if extensions is not None and extensions.transform_page_html is not None:
            rendered_html = extensions.transform_page_html(rendered_html, route)
        rendered_bytes = rendered_html.encode("utf-8")
        html, applied_stages = _run_stages(stages, rendered_html, "html")
        write_text_atomic(out_path, html)
        routes[route] = out_path.relative_to(output_dir).as_posix()
        files.append(
            _output_file(
                out_path,
                output_dir,
                kind="html",
                original_size=len(rendered_bytes) if applied_stages else None,
                optimizer_backend=applied_stages,
            )
        )
        for asset_path in _collect_document_assets(
            rendered_html,
            source=source,
            out_path=out_path,
            output_dir=output_dir,
            base=base,
            copied=copied_assets,
        ):
            files.append(_output_file(asset_path, output_dir))

    if any_math:
        katex_files, katex_assets = copy_katex_assets(output_dir)
        files.extend(katex_files)
        assets.extend(katex_assets)

    for path in write_site_files(
        output_dir,
        routes,
        base_url=config.base_url,
        lastmods=lastmods,
        redirects=config.redirects,
    ):
        files.append(_output_file(path, output_dir))

    files.extend(_precompress_outputs(output_dir, files, precompress))

    pipeline_names = "+".join(stage.name for stage in stages) if stages else None
    report = BuildReport(
        output_dir=output_dir,
        files=files,
        assets=assets,
        routes=routes,
        diagnostics=[],
        optimizer_backend=pipeline_names,
        precompress=precompress,
    )
    manifest = report.write_manifest()
    files.append(_output_file(manifest, output_dir, kind="json"))
    return BuildReport(
        output_dir=output_dir,
        files=files,
        assets=assets,
        routes=routes,
        diagnostics=[],
        optimizer_backend=pipeline_names,
        precompress=precompress,
    )


def build_html(src_html: str, dest_html: Path, options: BuildOptions | None = None) -> BuildReport:
    """Write one HTML artifact through the build pipeline."""

    optimizer: OptimizerMode = options.optimizer if options and options.optimizer else "none"
    do_optimize = optimizer != "none"

    # Preflight: verify the full optimizer toolchain before writing any output.
    if optimizer == "full":
        from kpress.publish.capability import preflight_optimizer_full

        preflight_optimizer_full()

    original_bytes = src_html.encode("utf-8")
    original_size = len(original_bytes)
    html = optimize_text(src_html, kind="html", backend=optimizer) if do_optimize else src_html
    write_text_atomic(dest_html, html)
    files = [
        _output_file(
            dest_html,
            dest_html.parent,
            kind="html",
            original_size=original_size if do_optimize else None,
            optimizer_backend=optimizer if do_optimize else None,
        )
    ]
    precompress_methods = list(options.precompress) if options and options.precompress else []
    if precompress_methods:
        files.extend(_precompress_outputs(dest_html.parent, files, precompress_methods))
    report = BuildReport(
        output_dir=dest_html.parent,
        files=files,
        optimizer_backend=optimizer if do_optimize else None,
        precompress=precompress_methods,
    )
    return report


# Relative asset prefix for standalone single-document outputs: package
# assets are emitted beside the HTML under ./_kpress/assets so the file opens
# without a matching asset server.
STANDALONE_ASSET_PREFIX = "./_kpress/assets/"


def emit_standalone_assets(
    dest_html: Path,
    *,
    asset_mode: AssetMode,
    page: RenderedPage | None = None,
    source: Path | None = None,
) -> list[Path]:
    """Emit the asset tree beside a standalone HTML artifact.

    Single-document outputs reference ``./_kpress/assets`` with a relative
    prefix. ``inline`` output is already self-contained and needs nothing on
    disk; every other mode must materialize the referenced bundle next to the
    HTML so the document opens without a separate asset server.

    When ``page`` is given and contains math, the vendored KaTeX bundle is
    emitted too (a no-math document stays KaTeX-free). When ``source`` is also
    given, local media the document references (``![](assets/x.svg)``, raw
    ``<img>``/``<iframe>``) is copied next to the HTML so figures resolve.
    """

    if asset_mode == "inline":
        return []
    files, _assets = copy_package_assets(dest_html.parent, asset_mode=asset_mode)
    emitted = [dest_html.parent / file.path for file in files]
    if page is not None and page.has_math:
        katex_files, _katex_assets = copy_katex_assets(dest_html.parent)
        emitted.extend(dest_html.parent / file.path for file in katex_files)
    if page is not None and source is not None:
        emitted.extend(
            _collect_document_assets(
                page.html,
                source=source,
                out_path=dest_html,
                output_dir=dest_html.parent,
                base=source.parent,
                copied=set(),
            )
        )
    return emitted


def export_document(request: KPressExportRequest) -> dict[str, object]:
    """Export one document through the static page path."""

    source = Path(request.path)
    if not source.exists():
        msg = f"Cannot export missing KPress document: {source}"
        raise FileNotFoundError(msg)
    destination = Path(request.destination) if request.destination else source.with_suffix(".html")
    source_text = source.read_text(encoding="utf-8")
    # `single-file` is not yet truly self-contained: inlined ES modules still
    # import sibling `./x.js` files and fonts stay external (orig-7ehk), so
    # a relocated single file would silently lose its reader features. Refuse
    # rather than emit a broken artifact; `sealed` is the supported
    # self-contained output.
    if request.export_mode == "single-file":
        msg = (
            "Export mode 'single-file' is not yet supported: the output would not be "
            "self-contained (ES-module imports and fonts stay external). Use a sealed "
            "static build for a fully offline artifact."
        )
        raise KPressPublishError(msg)
    asset_mode: AssetMode = request.asset_mode
    page = render_page(
        DocumentInput(
            title=source.stem.replace("-", " ").title(),
            source_text=source_text,
            body_markdown=source_text,
            source_path=str(source),
            trust_mode="sanitized",
        ),
        RenderOptions(
            print_profile=request.print_profile,
            asset_mode=asset_mode,
            asset_url_prefix=STANDALONE_ASSET_PREFIX,
            extra_tags=request.extra_tags,
            extra_attributes=request.extra_attributes,
        ),
    )
    report = build_html(
        page.html,
        destination,
        BuildOptions(optimizer="full" if request.optimize else "none"),
    )
    emit_standalone_assets(destination, asset_mode=asset_mode, page=page, source=source)
    return report.as_dict()
