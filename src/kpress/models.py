"""Public KPress runtime data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

PrintProfile = Literal["document", "source", "table", "tree", "plain"]
ThemeMode = Literal["system", "light", "dark"]


@dataclass(frozen=True)
class KPressAsset:
    """Resolved KPress package asset ready for a host response."""

    content: bytes
    media_type: str
    etag: str
    cache_control: str = "no-cache"


@dataclass(frozen=True)
class KPressRenderRequest:
    """Normalized dynamic render request accepted by KPress hosts."""

    source_text: str
    source_path: str
    kind: str
    view: str
    ext: str
    mtime_hash: str
    size: int
    frontmatter: dict[str, Any] = field(default_factory=dict)
    frontmatter_error: str | None = None
    profile: str | None = None
    theme_mode: ThemeMode = "system"
    resolved_theme: Literal["light", "dark"] = "light"
    host: str = "host"
    asset_url_prefix: str = "/kpress-static/"
    # Hosts that show the document title in their own chrome suppress the
    # rendered <h1> doc header (default keeps it, as standalone pages want it).
    show_doc_header: bool = True
    # Collapsible TOC — the dynamic-path counterpart of
    # RenderOptions.toc_collapse_depth / toc_expand_on_scroll, so a host's
    # embeds collapse the same way its static publish does. None keeps the
    # fully expanded TOC; an int >= 1 collapses deeper entries (validated).
    toc_collapse_depth: int | None = None
    toc_expand_on_scroll: bool = True
    # Widget presence + opaque config map (same shape as format.widgets);
    # echoed in the render payload so host-mounted widgets read the same
    # config the standalone page model carries.
    widgets: dict[str, Any] = field(default_factory=dict)
    # Whitelist of additional pass-through HTML/XML tag names — the dynamic-path
    # counterpart of RenderOptions.extra_tags / format.html.extra_tags, so a host
    # admits the same tags in embeds that its static publish admits and one document
    # renders identically both ways. Same policy (unioned with <span>/<div>, carrying
    # class/data-* only) and validated by the sanitizer (shape + forbidden set).
    extra_tags: tuple[str, ...] = ()
    # Extra inert attribute names admitted on whitelist-only pass-through tags —
    # the counterpart of RenderOptions.extra_attributes / format.html.extra_attributes,
    # so embeds and exports carry the same attribute policy as static publish.
    extra_attributes: tuple[str, ...] = ()


@dataclass(frozen=True)
class KPressExportRequest:
    """Request to render a KPress document into a publishable artifact."""

    path: str
    kind: str
    view: str
    source_text: str | None = None
    print_profile: PrintProfile = "document"
    theme_mode: ThemeMode = "system"
    export_mode: Literal["page", "single-file", "static-hosted", "hashed-static-hosted", "pdf"] = (
        "page"
    )
    asset_mode: Literal["linked", "inline", "hashed"] = "linked"
    optimize: bool = False
    destination: str | Path | None = None
    # Whitelist of additional pass-through HTML/XML tag names — same contract as
    # KPressRenderRequest.extra_tags, so a single-document export admits the same
    # tags as the host's static builds and embeds.
    extra_tags: tuple[str, ...] = ()
    # Extra inert attribute names admitted on whitelist-only pass-through tags —
    # the counterpart of RenderOptions.extra_attributes / format.html.extra_attributes,
    # so embeds and exports carry the same attribute policy as static publish.
    extra_attributes: tuple[str, ...] = ()
