"""Typed document format models for KPress."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from kpress.models import PrintProfile, ThemeMode

DocumentProfile = PrintProfile
TrustMode = Literal["trusted-local", "sanitized-local", "public-static", "untrusted"]
TocMode = Literal["off", "auto", "on"]
MathMode = Literal["off", "auto"]
DiagramMode = Literal["off", "auto", "mermaid"]
FontMode = Literal["custom", "system"]
AssetMode = Literal["hosted", "linked", "hashed", "inline", "sealed"]
OptimizerMode = Literal["none", "full"]


@dataclass(frozen=True)
class Diagnostic:
    """Stable render/build diagnostic."""

    type: str
    message: str
    severity: Literal["info", "warning", "error"] = "warning"
    location: str | None = None

    def as_dict(self) -> dict[str, str]:
        out = {"type": self.type, "message": self.message, "severity": self.severity}
        if self.location:
            out["location"] = self.location
        return out


@dataclass(frozen=True)
class Heading:
    """Heading discovered while normalizing a document."""

    level: int
    title: str
    id: str


@dataclass(frozen=True)
class TocEntry:
    """TOC entry emitted for a heading."""

    level: int
    title: str
    href: str


@dataclass(frozen=True)
class Footnote:
    """Footnote definition after Markdown normalization."""

    id: str
    html: str


@dataclass(frozen=True)
class DocumentInput:
    """Normalized document payload passed into KPress formatting."""

    title: str
    source_text: str
    source_path: str
    logical_path: str | None = None
    body_markdown: str | None = None
    body_html: str | None = None
    frontmatter: dict[str, Any] = field(default_factory=dict)
    sidematter: dict[str, Any] = field(default_factory=dict)
    frontmatter_error: str | None = None
    profile: DocumentProfile = "document"
    document_profile: DocumentProfile = "document"
    trust_mode: TrustMode = "trusted-local"
    host: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def path(self) -> Path:
        return Path(self.source_path)


@dataclass(frozen=True)
class RenderOptions:
    """Host-neutral render options for a KPress fragment or page."""

    profile: DocumentProfile = "document"
    print_profile: PrintProfile = "document"
    view: str = "document"
    host: str | None = None
    theme_mode: ThemeMode = "system"
    font_mode: FontMode = "custom"
    # Named palette preset: a built-in bundle of the host-var contract, stamped as
    # data-kpress-palette on the .kpress wrapper. "neutral" is the default (no
    # overrides); "warm" applies the tan-paper ramp. Hosts may still override any
    # individual --kpress-host-* var on top.
    palette: str = "neutral"
    resolved_theme: Literal["light", "dark"] = "light"
    asset_url_prefix: str = "/kpress-static/"
    asset_mode: AssetMode = "hosted"
    include_assets: bool = True
    include_toc: TocMode = "auto"
    toc_min_headings: int = 4
    # The document profile renders an <h1> doc header from the title. Hosts
    # that already show the title in their own chrome (e.g. an embedding app's
    # file header) pass False to suppress it, rather than hiding it with host CSS.
    show_doc_header: bool = True
    # Render frontmatter as a collapsible "Metadata" disclosure. Sites that treat
    # frontmatter as build-only metadata (not reader-facing) pass False to omit it.
    show_frontmatter: bool = True
    # Render the standalone gear-icon settings popover (theme chooser) in the page
    # shell. On by default; hosts that drive theme through their own chrome, or want
    # no settings UI at all, pass False to omit it. Position is host-overridable via
    # the --kpress-host-settings-inset-* CSS vars; this is the on/off switch.
    show_settings: bool = True
    math: MathMode = "auto"
    diagrams: DiagramMode = "auto"
    printable: bool = True
    # Page chrome slots: opaque site-owned HTML emitted verbatim by render_page
    # (head extra inside <head>; header/footer wrapped in .kpress-site-header /
    # .kpress-site-footer). KPress styles the wrappers but never interprets the
    # content; empty slots emit nothing.
    head_extra_html: str = ""
    header_html: str = ""
    footer_html: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentTree:
    """Normalized document tree used by renderers and tests."""

    title: str
    html: str
    profile: DocumentProfile
    headings: list[Heading] = field(default_factory=list)
    toc: list[TocEntry] = field(default_factory=list)
    footnotes: list[Footnote] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    has_math: bool = False


@dataclass(frozen=True)
class RenderedDocument:
    """Rendered KPress fragment returned to dynamic hosts."""

    html: str
    profile: PrintProfile
    printable: bool = True
    assets: dict[str, list[str]] = field(default_factory=dict)
    diagnostics: list[Any] = field(default_factory=list)
    toc: list[TocEntry] = field(default_factory=list)
    has_math: bool = False


@dataclass(frozen=True)
class RenderedPage:
    """Complete HTML page rendered by KPress."""

    html: str
    profile: PrintProfile
    title: str
    assets: dict[str, list[str]] = field(default_factory=dict)
    diagnostics: list[Any] = field(default_factory=list)
    has_math: bool = False


# Host-facing alias for the dynamic render result type.
RenderResult = RenderedDocument
