"""Stable dynamic-host API for KPress document rendering."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import re
from collections import OrderedDict
from collections.abc import Iterable, Mapping
from importlib import resources
from pathlib import Path, PurePosixPath
from threading import RLock
from typing import Any, cast
from urllib.parse import quote

from kpress._version import __version__
from kpress.errors import (
    KPressAssetNotFoundError,
    KPressInvalidRequestError,
    KPressPublishError,
    KPressRenderError,
)
from kpress.format import DocumentInput, RenderOptions, RenderResult, render_fragment
from kpress.format.model import parse_widgets, resolve_widgets
from kpress.format.render import build_page_model, page_title
from kpress.models import (
    KPressAsset,
    KPressExportRequest,
    KPressRenderRequest,
    PrintProfile,
    ThemeMode,
)

_ALLOWED_PROFILES: set[str] = {"document", "source", "table", "tree", "plain"}
_RENDER_CACHE_MAX = 64
_RENDER_CACHE: OrderedDict[tuple[Any, ...], dict[str, Any]] = OrderedDict()
_render_cache_lock = RLock()
_static_root_override: Path | None = None

# A version-addressed URL (`v<version>/...`) namespaces the asset by package
# version, so an upgrade changes the URL and never collides with a cached older
# build. Within a single version it is cacheable for a long time — but it is NOT
# served `immutable`. The version is a coarse fingerprint, not a content hash:
# the same `v<version>` URL can serve different bytes from a source/editable
# checkout, or if a release ever ships changed assets without bumping the
# version. `immutable` would suppress revalidation even on an explicit reload,
# stranding readers on stale CSS/JS until a hard reload. Omitting it keeps the
# in-session cache (zero requests during multi-page browsing) while letting a
# normal reload revalidate against the content-hash ETag below (a cheap 304 when
# unchanged). Content-addressed URLs would let us restore `immutable`; see
# kpress-design.md "Static asset caching".
_ASSET_VERSION_SEGMENT = f"v{__version__}"
_VERSION_SEG_RE = re.compile(r"^v\d[\w.+-]*$")
_VERSIONED_CACHE_CONTROL = "public, max-age=31536000"
_DEFAULT_CACHE_CONTROL = "no-cache"

__all__ = [
    "KPressAsset",
    "KPressAssetNotFoundError",
    "KPressExportRequest",
    "KPressInvalidRequestError",
    "KPressPublishError",
    "KPressRenderError",
    "KPressRenderRequest",
    "PrintProfile",
    "ThemeMode",
    "clear_render_cache",
    "export_document",
    "get_static_asset",
    "normalize_print_profile",
    "render_view",
    "set_static_root_for_tests",
    "static_asset_url",
]


def normalize_print_profile(view: str, profile: str | None = None) -> PrintProfile:
    """Map host view/profile names onto KPress print profiles."""

    raw = (profile or view or "document").strip().lower()
    aliases = {
        "rendered": "document",
        "doc": "document",
        "markdown": "document",
        "text": "source",
        "code": "source",
    }
    normalized = aliases.get(raw, raw)
    if normalized not in _ALLOWED_PROFILES:
        expected = ", ".join(sorted(_ALLOWED_PROFILES))
        raise KPressInvalidRequestError(
            f"Unsupported KPress print profile {raw!r}; expected one of {expected}"
        )
    return cast(PrintProfile, normalized)


def clear_render_cache() -> None:
    """Clear the small in-process KPress render cache."""

    with _render_cache_lock:
        _RENDER_CACHE.clear()


def set_static_root_for_tests(path: Path | None) -> None:
    """Override KPress static asset root for route tests."""

    global _static_root_override
    _static_root_override = path


_FRONTMATTER_BLOCK_RE = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n?", re.DOTALL)


def _strip_leading_frontmatter(source_text: str) -> str:
    """Remove a leading YAML frontmatter block (``---\\n…\\n---``) from text.

    The dynamic-host render path receives the full source bytes so the source
    profile (Pygments) shows the file as written. The document profile, on
    the other hand, must not feed the raw ``---`` block to the markdown
    renderer — markdown-it interprets ``---`` as setext heading underline
    and emits an ``<h2>`` with the frontmatter keys as its text.

    ``frontmatter_format.fmf_strip_frontmatter`` is path-based, so we
    implement the string-based strip inline. Only a frontmatter block at
    the very start of the text is stripped (a stray ``---`` elsewhere in
    the body is left alone so horizontal rules still render).
    """

    return _FRONTMATTER_BLOCK_RE.sub("", source_text, count=1)


def _source_hash(source_text: str) -> str:
    return hashlib.sha256(source_text.encode("utf-8", errors="replace")).hexdigest()


def _cache_get(key: tuple[Any, ...]) -> dict[str, Any] | None:
    with _render_cache_lock:
        value = _RENDER_CACHE.get(key)
        if value is None:
            return None
        _RENDER_CACHE.move_to_end(key)
        return dict(value)


def _cache_put(key: tuple[Any, ...], value: dict[str, Any]) -> None:
    with _render_cache_lock:
        _RENDER_CACHE[key] = dict(value)
        _RENDER_CACHE.move_to_end(key)
        while len(_RENDER_CACHE) > _RENDER_CACHE_MAX:
            _ = _RENDER_CACHE.popitem(last=False)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        mapping = cast(Mapping[object, object], value)
        return {str(k): _jsonable(v) for k, v in mapping.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        iterable = cast(Iterable[object], value)
        return [_jsonable(v) for v in iterable]
    return repr(value)


def _asset_ref_to_url(ref: Any, *, prefix: str) -> str | None:
    if ref is None:
        return None
    if isinstance(ref, str):
        raw = ref
    elif isinstance(ref, dict):
        mapping = cast(Mapping[str, object], ref)
        raw = str(
            mapping.get("url")
            or mapping.get("href")
            or mapping.get("path")
            or mapping.get("id")
            or ""
        )
    else:
        raw = str(
            getattr(ref, "url", None)
            or getattr(ref, "href", None)
            or getattr(ref, "path", None)
            or getattr(ref, "id", None)
            or ""
        )
    raw = raw.strip()
    if not raw:
        return None
    if raw.startswith(("http://", "https://", "/", "data:")):
        return raw
    return prefix.rstrip("/") + "/" + _ASSET_VERSION_SEGMENT + "/" + quote(raw.lstrip("/"))


def static_asset_url(rel_path: str, *, prefix: str = "/kpress-static/") -> str:
    """Version-keyed URL for a packaged static asset.

    Returns e.g. ``/kpress-static/v0.0.1/fonts/source-sans-3-latin-wght-normal.woff2``.
    A host that wants to preload or link a KPress asset from its own page chrome
    (rather than only via an embedded document) uses this so the URL matches the
    one embedded documents request — sharing a single download and cache entry.
    """

    return prefix.rstrip("/") + "/" + _ASSET_VERSION_SEGMENT + "/" + quote(rel_path.lstrip("/"))


def _normalize_assets(result: RenderResult, *, prefix: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"css": [], "js": []}
    css_refs = result.assets.get("css") or result.assets.get("styles") or []
    js_refs = result.assets.get("js") or result.assets.get("scripts") or []
    for bucket, refs in (("css", css_refs), ("js", js_refs)):
        for ref in refs:
            url = _asset_ref_to_url(ref, prefix=prefix)
            if url and url not in out[bucket]:
                out[bucket].append(url)
    return out


def _normalize_render_result(
    result: RenderResult,
    *,
    profile: PrintProfile,
    asset_url_prefix: str,
) -> dict[str, Any]:
    diagnostics = _jsonable(result.diagnostics)
    if diagnostics is None:
        diagnostics = []
    if not isinstance(diagnostics, list):
        diagnostics = [diagnostics]
    return {
        "type": "kpress-rendered-document",
        "html": result.html,
        "profile": result.profile or profile,
        "printable": bool(result.printable),
        "assets": _normalize_assets(result, prefix=asset_url_prefix),
        "diagnostics": diagnostics,
    }


def render_view(request: KPressRenderRequest) -> dict[str, Any]:
    """Render a document through KPress and return a JSON-ready host payload."""

    profile = normalize_print_profile(request.view, request.profile)
    # Same normalization as the static dialects (presence scalars to
    # "on"/"off"/"auto", typos raise): static and dynamic hosts must publish
    # identical widget data, and an invalid value must not be kept truthy.
    widgets = parse_widgets(request.widgets)
    source_digest = _source_hash(request.source_text)
    cache_key = (
        request.source_path,
        request.kind,
        request.view,
        profile,
        request.mtime_hash,
        request.size,
        __version__,
        request.theme_mode,
        request.resolved_theme,
        source_digest,
        # Widgets affect the echoed payload (and any widget-dependent render),
        # so they are part of the identity. Stable-stringified: dicts are not
        # hashable and key order must not matter.
        json.dumps(widgets, sort_keys=True, default=str),
    )
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    metadata = {
        "host": request.host,
        "kind": request.kind,
        "view": request.view,
        "profile": profile,
        "source_path": request.source_path,
        "ext": request.ext,
        "size": request.size,
        "mtime_hash": request.mtime_hash,
        "frontmatter_error": request.frontmatter_error,
    }
    # Hosts pass the parsed frontmatter dict via `request.frontmatter` and
    # the full source text (frontmatter block included) via `source_text`.
    # The markdown renderer treats `---\nkey: value\n---` as a setext H2
    # underlining the previous line — so we strip the leading frontmatter
    # off `body_markdown` before passing it down. `source_text` keeps the
    # raw bytes so the source profile (Pygments) shows the file as written.
    body_markdown = (
        _strip_leading_frontmatter(request.source_text) if profile == "document" else None
    )
    document = DocumentInput(
        title=Path(request.source_path).name,
        body_markdown=body_markdown,
        source_text=request.source_text,
        source_path=request.source_path,
        logical_path=request.source_path,
        frontmatter=request.frontmatter,
        frontmatter_error=request.frontmatter_error,
        profile=profile,
        document_profile=profile,
        # Dynamic host render serves arbitrary documents from the embedder's
        # worktree. The body must be treated as untrusted: switch from
        # `trusted-local` (raw HTML passthrough) to `sanitized-local` so
        # `<script>`, event-handler attributes, and `javascript:` URLs are
        # stripped before the host injects the fragment into its shell.
        trust_mode="sanitized-local",
        host=request.host,
        metadata=metadata,
    )
    options = RenderOptions(
        profile=profile,
        print_profile=profile,
        view=request.view,
        host=request.host,
        theme_mode=request.theme_mode,
        resolved_theme=request.resolved_theme,
        asset_url_prefix=request.asset_url_prefix,
        include_assets=True,
        show_doc_header=request.show_doc_header,
        widgets=widgets,
        printable=True,
        metadata=metadata,
    )
    try:
        result = render_fragment(document, options)
    except KPressRenderError:
        raise
    except Exception as exc:  # noqa: BLE001 - preserve host diagnostics boundary
        raise KPressRenderError(f"{type(exc).__name__}: {exc}") from exc

    normalized = _normalize_render_result(
        result,
        profile=profile,
        asset_url_prefix=request.asset_url_prefix,
    )
    # Echo the resolved widget map (defaults merged, "off" removed, config
    # verbatim) so host-mounted widgets read the same data the standalone
    # page model carries. The fragment itself has no #kpress-page-model block.
    resolved_widgets = resolve_widgets(widgets)
    normalized["widgets"] = resolved_widgets
    # Embeds get the full page model in the payload (same keys and builder as
    # the static #kpress-page-model block), so e.g. a minimap widget reading
    # kpress.model().headings works in an embed. `route` is empty: the request
    # carries no site route — source_path is a worktree file path, and the
    # model does not pretend otherwise.
    normalized["model"] = build_page_model(
        title=page_title(document),
        route="",
        profile=result.profile or profile,
        toc=result.toc,
        widgets=resolved_widgets,
    )
    _cache_put(cache_key, normalized)
    return normalized


def _asset_parts(rel_path: str) -> tuple[str, ...]:
    raw = (rel_path or "").strip("/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise KPressAssetNotFoundError(f"not found: {rel_path}")
    return path.parts


def _asset_media_type(rel_path: str) -> str:
    media_type, _ = mimetypes.guess_type(rel_path)
    return media_type or "application/octet-stream"


def _split_version_segment(rel_path: str) -> tuple[bool, str]:
    """Strip a leading ``v<version>`` segment, signalling an immutable URL."""

    raw = (rel_path or "").strip("/")
    head, slash, rest = raw.partition("/")
    if slash and _VERSION_SEG_RE.match(head):
        return True, rest
    return False, raw


def _asset_from_bytes(
    rel_path: str, content: bytes, *, cache_control: str = _DEFAULT_CACHE_CONTROL
) -> KPressAsset:
    digest = hashlib.sha256(content).hexdigest()
    return KPressAsset(
        content=content,
        media_type=_asset_media_type(rel_path),
        etag=f'"kp-{digest}"',
        cache_control=cache_control,
    )


def get_static_asset(rel_path: str) -> KPressAsset:
    """Read a safe KPress package static asset.

    A version-addressed request (``v<version>/...``) gets a long-lived but
    revalidatable cache policy; an unversioned request keeps the ``no-cache``
    default. Both rely on the content-hash ETag for freshness — see the
    ``_VERSIONED_CACHE_CONTROL`` rationale above.
    """

    versioned, rel_path = _split_version_segment(rel_path)
    cache_control = _VERSIONED_CACHE_CONTROL if versioned else _DEFAULT_CACHE_CONTROL
    parts = _asset_parts(rel_path)
    if _static_root_override is not None:
        root = _static_root_override.resolve()
        candidate = root.joinpath(*parts).resolve()
        try:
            _ = candidate.relative_to(root)
        except ValueError as exc:
            raise KPressAssetNotFoundError(f"not found: {rel_path}") from exc
        if not candidate.is_file():
            raise KPressAssetNotFoundError(f"not found: {rel_path}")
        return _asset_from_bytes(rel_path, candidate.read_bytes(), cache_control=cache_control)

    package_files = resources.files("kpress")
    for prefix in (("format", "static"), ("format", "assets"), ("static",), ("assets",)):
        candidate = package_files.joinpath(*prefix, *parts)
        try:
            if candidate.is_file():
                return _asset_from_bytes(
                    rel_path, candidate.read_bytes(), cache_control=cache_control
                )
        except FileNotFoundError:
            continue
    raise KPressAssetNotFoundError(f"not found: {rel_path}")


def export_document(request: KPressExportRequest) -> Any:
    """Delegate static export requests to the KPress publisher."""

    from kpress.publish import export_document as publish_export_document

    return publish_export_document(request)
