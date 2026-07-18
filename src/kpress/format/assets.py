"""Asset model and package asset helpers."""

from __future__ import annotations

import hashlib
import mimetypes
import os
import tempfile
from contextlib import suppress
from dataclasses import dataclass, field, replace
from importlib import resources
from pathlib import Path, PurePosixPath
from typing import Literal
from urllib.parse import quote

from kpress.contract import ASSET_MANIFEST_SCHEMA_VERSION
from kpress.format.model import AssetMode

AssetKind = Literal["package", "document-local", "local-file", "external-url", "generated", "media"]
AssetLoading = Literal["stylesheet", "module", "classic", "resource"]


@dataclass(frozen=True)
class AssetRef:
    """Reference to a package, local, generated, or external asset."""

    id: str
    kind: AssetKind
    path: str
    media_type: str | None = None
    content_hash: str | None = None
    output_path: str | None = None
    public_url: str | None = None
    entry_point: bool = False
    loading: AssetLoading = "resource"
    mode: AssetMode = "hosted"

    @property
    def url(self) -> str:
        return self.public_url or self.output_path or self.path


@dataclass(frozen=True)
class AssetManifest:
    """Stable manifest of assets required by a rendered document or build."""

    assets: list[AssetRef] = field(default_factory=list)
    import_map: dict[str, str] = field(default_factory=dict)

    def by_id(self) -> dict[str, AssetRef]:
        return {asset.id: asset for asset in self.assets}

    def browser_entry_points(self) -> list[AssetRef]:
        """Return browser-loaded entry points in deterministic manifest order."""

        return [asset for asset in self.assets if asset.entry_point]

    def merged(self, *others: AssetManifest) -> AssetManifest:
        """Merge compatible manifests and union their browser entry-point roles."""

        by_id = self.by_id()
        import_map = dict(self.import_map)
        for other in others:
            for asset in other.assets:
                existing = by_id.get(asset.id)
                if existing is not None:
                    if replace(existing, entry_point=False) != replace(asset, entry_point=False):
                        msg = f"Conflicting KPress asset manifest entry: {asset.id}"
                        raise ValueError(msg)
                    if asset.entry_point and not existing.entry_point:
                        by_id[asset.id] = replace(existing, entry_point=True)
                    continue
                by_id[asset.id] = asset
            for source, target in other.import_map.items():
                existing_target = import_map.get(source)
                if existing_target is not None and existing_target != target:
                    msg = f"Conflicting KPress import-map entry: {source}"
                    raise ValueError(msg)
                import_map[source] = target
        return AssetManifest(
            assets=list(by_id.values()),
            import_map=dict(sorted(import_map.items())),
        )

    def as_dict(self) -> dict[str, object]:
        rows: list[dict[str, object]] = []
        for asset in self.assets:
            row: dict[str, object] = {
                "id": asset.id,
                "kind": asset.kind,
                "path": asset.path,
                "mode": asset.mode,
            }
            if asset.media_type:
                row["media_type"] = asset.media_type
            if asset.content_hash:
                row["content_hash"] = asset.content_hash
            if asset.output_path:
                row["output_path"] = asset.output_path
            if asset.public_url:
                row["public_url"] = asset.public_url
            row["entry_point"] = asset.entry_point
            row["loading"] = asset.loading
            rows.append(row)
        return {
            "schema_version": ASSET_MANIFEST_SCHEMA_VERSION,
            "assets": rows,
            "import_map": dict(sorted(self.import_map.items())),
        }


DEFAULT_CSS_ASSETS = [
    "css/style-tokens.css",
    "css/theme-light.css",
    "css/theme-dark.css",
    "css/syntax.css",
    "css/document.css",
    "css/components.css",
    "css/print.css",
]
DEFAULT_JS_ASSETS = [
    # runtime.js loads first: it owns the kpress global (registries, storage,
    # events, page model) that every other module registers through.
    "js/runtime.js",
    "js/theme.js",
    "js/settings-widget.js",
    "js/toc.js",
    "js/tooltips.js",
    "js/history.js",
    "js/tables.js",
    "js/code-copy.js",
    "js/diagrams.js",
    "js/video-popover.js",
    "js/tabs.js",
    "js/host.js",
]
# Transitive ESM dependencies that the JS modules in DEFAULT_JS_ASSETS import
# at runtime. They are copied into the output tree (so the relative
# `import "./overlay.js"` resolves), but not injected as top-level `<script>`
# tags — the entry-point modules pull them in.
TRANSITIVE_JS_ASSETS = [
    "js/icons.js",
    "js/menu.js",
    "js/overlay.js",
    "js/viewport.js",
]
PACKAGE_JS_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "js/code-copy.js": ("js/icons.js", "js/runtime.js"),
    "js/diagrams.js": ("js/runtime.js",),
    "js/history.js": ("js/runtime.js", "js/viewport.js"),
    "js/host.js": ("js/runtime.js",),
    "js/icons.js": (),
    "js/menu.js": (),
    "js/overlay.js": ("js/viewport.js",),
    "js/runtime.js": (),
    "js/settings-widget.js": (
        "js/icons.js",
        "js/menu.js",
        "js/runtime.js",
        "js/theme.js",
    ),
    "js/tables.js": ("js/runtime.js",),
    "js/tabs.js": ("js/runtime.js",),
    "js/theme.js": ("js/runtime.js",),
    "js/toc.js": ("js/overlay.js", "js/runtime.js", "js/viewport.js"),
    "js/tooltips.js": ("js/overlay.js", "js/runtime.js", "js/viewport.js"),
    "js/video-popover.js": ("js/runtime.js",),
    "js/viewport.js": (),
}
DEFAULT_FONT_ASSETS = [
    "fonts/pt-serif-latin-400-normal.woff2",
    "fonts/pt-serif-latin-700-normal.woff2",
    "fonts/pt-serif-latin-400-italic.woff2",
    "fonts/pt-serif-latin-700-italic.woff2",
    "fonts/source-sans-3-latin-wght-normal.woff2",
    "fonts/source-sans-3-latin-wght-italic.woff2",
]


# Vendored, version-pinned KaTeX 0.16.45 (last release before the supply-chain
# cutoff). Emitted only for documents that contain math (lazy `auto`); never part
# of the default package manifest, so no-math output stays math-asset-free.
# `katex.min.css` is the upstream stylesheet reduced to its woff2 @font-face
# sources, with one deliberate modification: every `font-display` is `swap`
# (upstream ships `block`) so a late math face is a clean repaint instead of an
# invisible-text gap. KaTeX lays out from precomputed metrics, so layout never
# waits on fonts and `swap` is safe. The woff2 faces are vendored alongside it.
# Paths stay stable in every asset mode so the stylesheet's relative `fonts/`
# URLs keep resolving offline.
KATEX_VERSION = "0.16.45"
KATEX_CSS_ASSETS = [
    "katex/katex.min.css",
]
KATEX_JS_ASSETS = [
    "katex/katex.min.js",
    "katex/auto-render.min.js",
    "katex/katex-init.js",
]
KATEX_FONT_ASSETS = [
    "katex/fonts/KaTeX_AMS-Regular.woff2",
    "katex/fonts/KaTeX_Caligraphic-Bold.woff2",
    "katex/fonts/KaTeX_Caligraphic-Regular.woff2",
    "katex/fonts/KaTeX_Fraktur-Bold.woff2",
    "katex/fonts/KaTeX_Fraktur-Regular.woff2",
    "katex/fonts/KaTeX_Main-Bold.woff2",
    "katex/fonts/KaTeX_Main-BoldItalic.woff2",
    "katex/fonts/KaTeX_Main-Italic.woff2",
    "katex/fonts/KaTeX_Main-Regular.woff2",
    "katex/fonts/KaTeX_Math-BoldItalic.woff2",
    "katex/fonts/KaTeX_Math-Italic.woff2",
    "katex/fonts/KaTeX_SansSerif-Bold.woff2",
    "katex/fonts/KaTeX_SansSerif-Italic.woff2",
    "katex/fonts/KaTeX_SansSerif-Regular.woff2",
    "katex/fonts/KaTeX_Script-Regular.woff2",
    "katex/fonts/KaTeX_Size1-Regular.woff2",
    "katex/fonts/KaTeX_Size2-Regular.woff2",
    "katex/fonts/KaTeX_Size3-Regular.woff2",
    "katex/fonts/KaTeX_Size4-Regular.woff2",
    "katex/fonts/KaTeX_Typewriter-Regular.woff2",
]


def katex_asset_refs() -> dict[str, list[str]]:
    """Return KaTeX document asset paths grouped by type (stable, unhashed)."""

    return {"css": list(KATEX_CSS_ASSETS), "js": list(KATEX_JS_ASSETS)}


def katex_asset_manifest(
    *, mode: AssetMode = "hosted", prefix: str = "/kpress-static/"
) -> AssetManifest:
    """Return the complete resolved KaTeX asset closure."""

    refs: list[AssetRef] = []
    for rel_path in [*KATEX_CSS_ASSETS, *KATEX_JS_ASSETS, *KATEX_FONT_ASSETS]:
        data = read_package_bytes(rel_path)
        media_type, _ = mimetypes.guess_type(rel_path)
        output_path = package_asset_output_path(rel_path, mode=mode)
        if rel_path in KATEX_CSS_ASSETS:
            loading: AssetLoading = "stylesheet"
        elif rel_path in KATEX_JS_ASSETS:
            loading = "classic"
        else:
            loading = "resource"
        refs.append(
            AssetRef(
                id=rel_path,
                kind="package",
                path=rel_path,
                media_type=media_type or "application/octet-stream",
                content_hash=content_hash(data),
                output_path=output_path,
                public_url=package_asset_url(output_path, prefix=prefix),
                entry_point=rel_path in {*KATEX_CSS_ASSETS, *KATEX_JS_ASSETS},
                loading=loading,
                mode=mode,
            )
        )
    return AssetManifest(assets=refs)


def _safe_asset_parts(rel_path: str) -> tuple[str, ...]:
    raw = rel_path.strip("/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        msg = f"Unsafe KPress resource path: {rel_path}"
        raise FileNotFoundError(msg)
    return path.parts


def package_asset_url(path: str, *, prefix: str = "/kpress-static/") -> str:
    """Return a host URL for a package asset."""

    return prefix.rstrip("/") + "/" + quote(path.lstrip("/"))


def package_asset_output_path(path: str, *, mode: AssetMode = "hosted") -> str:
    """Return the static output path for a package asset in an asset mode.

    In hashed mode every asset -- CSS and JS alike -- gets a content-hashed
    filename built from its own bytes. JS modules are emitted byte-for-byte as they
    ship in the package: their relative ``import "./x.js"`` specifiers are *not*
    rewritten. The browser resolves those specifiers to the hashed files through an
    emitted import map (see ``package_js_import_map``) -- the web-standard alternative
    to Python parsing and rewriting the JS source.
    """

    rel = path.strip("/")
    # KaTeX is a pinned, hashed vendor bundle: its stylesheet references font
    # faces by relative `fonts/` URL, so the whole `katex/` subtree must keep
    # stable, unhashed names in every asset mode for those URLs to resolve.
    if mode != "hashed" or rel.startswith(("fonts/", "katex/")):
        return rel
    digest = content_hash(read_package_bytes(rel))
    posix = PurePosixPath(rel)
    return str(posix.with_name(f"{posix.stem}.{digest}{posix.suffix}"))


def package_js_import_map(*, mode: AssetMode, prefix: str) -> dict[str, str]:
    """Map each package JS module's natural URL to its emitted URL, for an import map.

    In hashed mode the emitted module files carry content-hashed names while
    their ``import "./x.js"`` specifiers are left untouched. A
    ``<script type="importmap">`` built from this mapping lets the browser resolve those
    specifiers to the hashed files, so KPress never has to parse or rewrite the JS.

    Keys and values both carry the caller's asset ``prefix``. An import-map key is
    resolved against the *document* base URL; a module's ``./x.js`` import is resolved
    against the *module* URL. Sharing one ``prefix`` makes the two land on the same
    absolute URL in both root-relative (``/_kpress/assets/``) and standalone-relative
    (``./_kpress/assets/``) layouts, so the remap matches.

    Every module is listed (entry points and their transitive deps) so any inter-module
    ``./x.js`` import resolves without KPress having to analyze the import graph. Returns
    an empty mapping for modes that do not hash filenames (nothing to remap).
    """

    if mode != "hashed":
        return {}
    base = prefix.rstrip("/") + "/"
    return {
        base + path: base + package_asset_output_path(path, mode=mode)
        for path in (*DEFAULT_JS_ASSETS, *TRANSITIVE_JS_ASSETS)
    }


def package_asset_refs(*, mode: AssetMode = "hosted") -> dict[str, list[str]]:
    """Return default document asset paths grouped by type."""

    return {
        "css": [package_asset_output_path(path, mode=mode) for path in DEFAULT_CSS_ASSETS],
        "js": [package_asset_output_path(path, mode=mode) for path in DEFAULT_JS_ASSETS],
    }


def package_asset_manifest(
    *, mode: AssetMode = "hosted", prefix: str = "/kpress-static/"
) -> AssetManifest:
    """Return the complete resolved package asset closure for a render or build."""

    refs: list[AssetRef] = []
    for rel_path in [
        *DEFAULT_CSS_ASSETS,
        *DEFAULT_JS_ASSETS,
        *TRANSITIVE_JS_ASSETS,
        *DEFAULT_FONT_ASSETS,
    ]:
        data = read_package_bytes(rel_path)
        media_type, _ = mimetypes.guess_type(rel_path)
        output_path = package_asset_output_path(rel_path, mode=mode)
        if rel_path in DEFAULT_CSS_ASSETS:
            loading: AssetLoading = "stylesheet"
            entry_point = True
        elif rel_path in DEFAULT_JS_ASSETS:
            loading = "module"
            entry_point = True
        elif rel_path in TRANSITIVE_JS_ASSETS:
            loading = "module"
            entry_point = False
        else:
            loading = "resource"
            entry_point = False
        refs.append(
            AssetRef(
                id=rel_path,
                kind="package",
                path=rel_path,
                media_type=media_type or "application/octet-stream",
                content_hash=content_hash(data),
                output_path=output_path,
                public_url=package_asset_url(output_path, prefix=prefix),
                entry_point=entry_point,
                loading=loading,
                mode=mode,
            )
        )
    return AssetManifest(
        assets=refs,
        import_map=package_js_import_map(mode=mode, prefix=prefix),
    )


def resolve_package_asset_manifest(
    entry_points: set[str],
    *,
    mode: AssetMode,
    prefix: str,
    include_base: bool = True,
) -> AssetManifest:
    """Resolve selected browser entry points and their declared package closure."""

    unknown = entry_points.difference(PACKAGE_JS_DEPENDENCIES)
    if unknown:
        msg = f"Unknown KPress browser entry points: {', '.join(sorted(unknown))}"
        raise ValueError(msg)

    selected_modules: set[str] = set()
    pending = sorted(entry_points, reverse=True)
    while pending:
        module = pending.pop()
        if module in selected_modules:
            continue
        selected_modules.add(module)
        pending.extend(
            dependency
            for dependency in reversed(PACKAGE_JS_DEPENDENCIES[module])
            if dependency not in selected_modules
        )

    full = package_asset_manifest(mode=mode, prefix=prefix)
    selected_assets: list[AssetRef] = []
    for asset in full.assets:
        if asset.loading == "stylesheet" or asset.loading == "resource":
            if include_base:
                selected_assets.append(asset)
            continue
        if asset.id in selected_modules:
            selected_assets.append(
                replace(
                    asset,
                    entry_point=asset.id in entry_points,
                )
            )

    selected_urls = {asset.public_url for asset in selected_assets if asset.public_url is not None}
    return AssetManifest(
        assets=selected_assets,
        import_map={
            source: target for source, target in full.import_map.items() if target in selected_urls
        },
    )


def materialize_package_assets(
    manifest: AssetManifest,
    destination: Path,
) -> list[AssetRef]:
    """Write and verify every package file declared by a resolved manifest.

    ``destination`` is the host-selected root corresponding to the manifest's
    output paths. Files are written atomically, and neither package paths nor
    output paths may escape their respective roots.
    """

    planned: list[tuple[AssetRef, tuple[str, ...], bytes, str]] = []
    claimed_output_paths: set[str] = set()
    for asset in manifest.assets:
        if asset.kind != "package":
            msg = f"Cannot materialize non-package KPress asset: {asset.id}"
            raise ValueError(msg)
        if asset.output_path is None:
            msg = f"KPress asset has no output path: {asset.id}"
            raise ValueError(msg)
        try:
            output_parts = _safe_asset_parts(asset.output_path)
        except FileNotFoundError as exc:
            msg = f"Unsafe KPress asset output path: {asset.output_path}"
            raise ValueError(msg) from exc
        normalized_output_path = PurePosixPath(*output_parts).as_posix()
        if normalized_output_path in claimed_output_paths:
            msg = f"Duplicate KPress asset output path: {normalized_output_path}"
            raise ValueError(msg)
        claimed_output_paths.add(normalized_output_path)
        _reject_symlinked_output_path(destination, output_parts)

        data = read_package_bytes(asset.path)
        actual_hash = content_hash(data)
        if asset.content_hash != actual_hash:
            msg = (
                f"KPress asset hash mismatch for {asset.id}: "
                f"expected {asset.content_hash}, got {actual_hash}"
            )
            raise ValueError(msg)
        planned.append((asset, output_parts, data, actual_hash))

    emitted: list[AssetRef] = []
    for asset, output_parts, data, actual_hash in planned:
        output_file = destination.joinpath(*output_parts)
        _write_bytes_atomic(output_file, data)
        written_hash = content_hash(output_file.read_bytes())
        if written_hash != actual_hash:
            msg = f"KPress asset verification failed after writing {asset.id}"
            raise OSError(msg)
        emitted.append(asset)
    return emitted


def _reject_symlinked_output_path(destination: Path, output_parts: tuple[str, ...]) -> None:
    """Reject an output whose root or existing component is a symbolic link."""

    candidate = destination
    for part in (None, *output_parts):
        if part is not None:
            candidate = candidate / part
        if candidate.is_symlink():
            msg = f"KPress asset output path traverses a symlink: {candidate}"
            raise ValueError(msg)


def _write_bytes_atomic(path: Path, data: bytes) -> None:
    """Write one core-format asset atomically without importing publish helpers."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            _ = handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except Exception:
        with suppress(OSError):
            os.close(descriptor)
        temporary_path.unlink(missing_ok=True)
        raise


def content_hash(data: bytes | str) -> str:
    """Return a stable short content hash."""

    raw = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(raw).hexdigest()[:16]


def read_package_bytes(rel_path: str) -> bytes:
    """Read a packaged KPress format resource as bytes."""

    parts = _safe_asset_parts(rel_path)
    package_files = resources.files("kpress")
    for prefix in (("format", "static"), ("format",)):
        resource = package_files.joinpath(*prefix, *parts)
        if resource.is_file():
            return resource.read_bytes()
    msg = f"KPress resource not found: {rel_path}"
    raise FileNotFoundError(msg)


def read_package_text(rel_path: str) -> str:
    """Read a packaged KPress format resource as text."""

    return read_package_bytes(rel_path).decode("utf-8")
