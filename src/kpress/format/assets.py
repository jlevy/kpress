"""Asset model and package asset helpers."""

from __future__ import annotations

import hashlib
import mimetypes
from dataclasses import dataclass, field
from importlib import resources
from pathlib import PurePosixPath
from typing import Literal
from urllib.parse import quote

from kpress.contract import ASSET_MANIFEST_SCHEMA_VERSION
from kpress.format.model import AssetMode

AssetKind = Literal["package", "document-local", "local-file", "external-url", "generated", "media"]


@dataclass(frozen=True)
class AssetRef:
    """Reference to a package, local, generated, or external asset."""

    id: str
    kind: AssetKind
    path: str
    media_type: str | None = None
    content_hash: str | None = None
    output_path: str | None = None
    mode: AssetMode = "hosted"

    @property
    def url(self) -> str:
        return self.output_path or self.path


@dataclass(frozen=True)
class AssetManifest:
    """Stable manifest of assets required by a rendered document or build."""

    assets: list[AssetRef] = field(default_factory=list)

    def by_id(self) -> dict[str, AssetRef]:
        return {asset.id: asset for asset in self.assets}

    def as_dict(self) -> dict[str, object]:
        rows: list[dict[str, str]] = []
        for asset in sorted(self.assets, key=lambda item: item.id):
            row = {
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
            rows.append(row)
        return {"schema_version": ASSET_MANIFEST_SCHEMA_VERSION, "assets": rows}


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
    "js/toc.js",
    "js/tooltips.js",
    "js/tables.js",
    "js/code-copy.js",
    "js/diagrams.js",
    "js/video-popover.js",
    "js/tabs.js",
    "js/host.js",
    "js/print.js",
]
# Transitive ESM dependencies that the JS modules in DEFAULT_JS_ASSETS import
# at runtime. They are copied into the output tree (so the relative
# `import "./overlay.js"` resolves), but not injected as top-level `<script>`
# tags — the entry-point modules pull them in.
TRANSITIVE_JS_ASSETS = [
    "js/icons.js",
    "js/overlay.js",
    "js/viewport.js",
]
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


def katex_asset_manifest() -> AssetManifest:
    """Return stable, sealed KaTeX asset references for a static build."""

    refs: list[AssetRef] = []
    for rel_path in [*KATEX_CSS_ASSETS, *KATEX_JS_ASSETS, *KATEX_FONT_ASSETS]:
        data = read_package_bytes(rel_path)
        media_type, _ = mimetypes.guess_type(rel_path)
        refs.append(
            AssetRef(
                id=rel_path,
                kind="package",
                path=rel_path,
                media_type=media_type or "application/octet-stream",
                content_hash=content_hash(data),
                output_path=rel_path,
                mode="sealed",
            )
        )
    return AssetManifest(refs)


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

    In hashed/sealed mode every asset -- CSS and JS alike -- gets a content-hashed
    filename built from its own bytes. JS modules are emitted byte-for-byte as they
    ship in the package: their relative ``import "./x.js"`` specifiers are *not*
    rewritten. The browser resolves those specifiers to the hashed files through an
    emitted import map (see ``package_js_import_map``) -- the web-standard alternative
    to Python parsing and rewriting the JS source.
    """

    rel = path.strip("/")
    # KaTeX is a pinned, sealed vendor bundle: its stylesheet references font
    # faces by relative `fonts/` URL, so the whole `katex/` subtree must keep
    # stable, unhashed names in every asset mode for those URLs to resolve.
    if mode not in {"hashed", "sealed"} or rel.startswith(("fonts/", "katex/")):
        return rel
    digest = content_hash(read_package_bytes(rel))
    posix = PurePosixPath(rel)
    return str(posix.with_name(f"{posix.stem}.{digest}{posix.suffix}"))


def package_js_import_map(*, mode: AssetMode, prefix: str) -> dict[str, str]:
    """Map each package JS module's natural URL to its emitted URL, for an import map.

    In hashed/sealed mode the emitted module files carry content-hashed names while
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

    if mode not in {"hashed", "sealed"}:
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


def package_asset_manifest(*, mode: AssetMode = "hosted") -> AssetManifest:
    """Return stable package asset references for a static build."""

    refs: list[AssetRef] = []
    for rel_path in [
        *DEFAULT_CSS_ASSETS,
        *DEFAULT_JS_ASSETS,
        *TRANSITIVE_JS_ASSETS,
        *DEFAULT_FONT_ASSETS,
    ]:
        data = read_package_bytes(rel_path)
        media_type, _ = mimetypes.guess_type(rel_path)
        refs.append(
            AssetRef(
                id=rel_path,
                kind="package",
                path=rel_path,
                media_type=media_type or "application/octet-stream",
                content_hash=content_hash(data),
                output_path=package_asset_output_path(rel_path, mode=mode),
                mode=mode,
            )
        )
    return AssetManifest(refs)


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
