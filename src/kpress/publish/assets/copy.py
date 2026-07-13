"""Package-asset copy helpers.

These read KPress's own vendored CSS/JS/font assets (and the KaTeX
bundle when a built document contains math) and write them into the
publish output tree under ``_kpress/assets/``. They are the only asset
graph KPress owns and rewrites in v1.

Document-local refs (``./image.png``) and external URLs
(``https://cdn.example.com/foo.js``) are emitted into the rendered HTML
verbatim and handled by the deploy layer (CDN, static host, reverse
proxy). The v2 roadmap brings sealing back behind a real parser or a JS
bundler — see ``docs/kpress-design.md`` § "Asset sealing:
deferred for v1".
"""

from __future__ import annotations

import mimetypes
from collections.abc import Callable
from pathlib import Path, PurePosixPath

from kpress.format.assets import (
    content_hash,
    katex_asset_manifest,
    package_asset_manifest,
    read_package_bytes,
)
from kpress.format.model import AssetMode
from kpress.output import write_bytes_atomic
from kpress.publish.manifest import ManifestAsset, OutputFile

AssetOptimizer = Callable[[str, str], tuple[str, list[str]]]


def _guess_media_type(path: str) -> str:
    media_type, _ = mimetypes.guess_type(path)
    return media_type or "application/octet-stream"


def text_asset_kind(media_type: str) -> str | None:
    """Map a media type to the rewrite kind a downstream optimizer cares about."""

    if media_type == "text/css":
        return "css"
    if media_type in {"text/javascript", "application/javascript"}:
        return "js"
    return None


def maybe_optimize_asset(
    data: bytes, *, media_type: str, optimizer: AssetOptimizer | None
) -> tuple[bytes, list[str]]:
    kind = text_asset_kind(media_type)
    if optimizer is None or kind is None:
        return data, []
    optimized, applied = optimizer(data.decode("utf-8"), kind)
    return optimized.encode("utf-8"), applied


def _package_output_path_for_data(rel_path: str, *, mode: AssetMode, data: bytes) -> str:
    rel = rel_path.strip("/")
    if mode != "hashed" or rel.startswith("fonts/"):
        return rel
    posix = PurePosixPath(rel)
    return str(posix.with_name(f"{posix.stem}.{content_hash(data)}{posix.suffix}"))


def copy_package_assets(
    output_dir: Path, *, asset_mode: AssetMode, optimizer: AssetOptimizer | None = None
) -> tuple[list[OutputFile], list[ManifestAsset]]:
    """Copy package-owned KPress assets into the static output tree."""

    files: list[OutputFile] = []
    assets: list[ManifestAsset] = []
    manifest_assets = package_asset_manifest(mode=asset_mode).assets

    # Optimize every asset once up front so the hashed filename reflects the final bytes.
    optimized: dict[str, tuple[bytes, str, list[str]]] = {}
    for asset in manifest_assets:
        raw = read_package_bytes(asset.path)
        media_type = asset.media_type or _guess_media_type(asset.path)
        data, applied = maybe_optimize_asset(raw, media_type=media_type, optimizer=optimizer)
        optimized[asset.path] = (data, media_type, applied)

    for asset in manifest_assets:
        data, media_type, applied = optimized[asset.path]
        if asset_mode == "inline" and text_asset_kind(media_type) in {"css", "js"}:
            assets.append(
                ManifestAsset(
                    path=asset.path,
                    kind="package-inline",
                    source="package",
                    output_path=f"inline:{asset.path}",
                    content_hash=content_hash(data),
                    media_type=media_type,
                )
            )
            continue
        # JS hashes by its own bytes, exactly like CSS. Inter-module `import "./x.js"`
        # specifiers stay untouched; the emitted import map remaps them to the hashed
        # files, so the JS source is never parsed or rewritten here.
        output_path = _package_output_path_for_data(asset.path, mode=asset_mode, data=data)
        destination = output_dir / "_kpress" / "assets" / output_path
        write_bytes_atomic(destination, data)
        rel = destination.relative_to(output_dir).as_posix()
        files.append(
            OutputFile(
                path=rel,
                kind=destination.suffix.lstrip("."),
                content_hash=content_hash(data),
                size=len(data),
                applied_pipeline=applied,
            )
        )
        assets.append(
            ManifestAsset(
                path=asset.path,
                kind=asset.kind,
                source="package",
                output_path=rel,
                content_hash=content_hash(data),
                media_type=media_type,
            )
        )
    return files, assets


def copy_katex_assets(
    output_dir: Path,
) -> tuple[list[OutputFile], list[ManifestAsset]]:
    """Copy the vendored KaTeX bundle into the static output tree.

    Only called when a built document contains math, so no-math sites stay
    free of any KaTeX asset. Paths are stable (unhashed) so the stylesheet's
    relative ``fonts/`` URLs keep resolving offline.
    """

    files: list[OutputFile] = []
    assets: list[ManifestAsset] = []
    for asset in katex_asset_manifest().assets:
        data = read_package_bytes(asset.path)
        media_type = asset.media_type or _guess_media_type(asset.path)
        destination = output_dir / "_kpress" / "assets" / asset.path
        write_bytes_atomic(destination, data)
        rel = destination.relative_to(output_dir).as_posix()
        files.append(
            OutputFile(
                path=rel,
                kind=destination.suffix.lstrip("."),
                content_hash=content_hash(data),
                size=len(data),
            )
        )
        assets.append(
            ManifestAsset(
                path=asset.path,
                kind=asset.kind,
                source="package",
                output_path=rel,
                content_hash=content_hash(data),
                media_type=media_type,
            )
        )
    return files, assets
