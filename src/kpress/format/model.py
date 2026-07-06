"""Typed document format models for KPress."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, cast

from kpress.errors import KPressPublishError
from kpress.models import PrintProfile, ThemeMode

DocumentProfile = PrintProfile
# Trust modes: who wrote the content and where the output lands. See the
# "Trust Modes and the Sanitization Threat Model" section of kpress-design.md
# for the threat model and the entry-point → mode mapping.
TrustMode = Literal["trusted-local", "sanitized-local", "public-static"]
TocMode = Literal["off", "auto", "on"]
MathMode = Literal["off", "auto"]
DiagramMode = Literal["off", "auto", "mermaid"]
FontMode = Literal["custom", "system"]
ProseFont = Literal["serif", "sans"]
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
    # Site default for the reading-font chooser: the serif reading face or the
    # sans stack. Stamped as data-kpress-prose-font on <html> by the standalone
    # page, where the pre-paint bootstrap and the settings widget read it as
    # the unstored default; a reader's persisted choice (kpress.proseFont)
    # still wins. Deliberately NOT stamped on the .kpress wrapper: the wrapper
    # selector would tie with the root one and the reader could never switch
    # back. Embedding hosts stamp their own root attribute instead.
    prose_font: ProseFont = "serif"
    # Content card: render the reading column as a bordered sheet floating over
    # the page (textpress's long-text card; chrome only appears at md+ widths).
    # Stamped as data-kpress-card on the document article; the CSS lives in
    # components.css "Content card". On by default; pass False (or
    # `format.content_card: false`) for the flat full-bleed page.
    content_card: bool = True
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
    math: MathMode = "auto"
    diagrams: DiagramMode = "auto"
    # Whitelist of additional pass-through HTML/XML tag names the host activates
    # (config: format.html.extra_tags). Unioned with the always-on <span>/<div> defaults
    # and admitted across every sanitizing trust mode, carrying class/data-* (never
    # style/on*/unsafe URLs). See kpress.contract.PUBLIC_PASS_THROUGH_TAGS. Empty by
    # default: with no extra tags, output is unchanged.
    extra_tags: tuple[str, ...] = ()
    printable: bool = True
    # Widget presence + opaque config map (the extension model's layer D; see
    # kpress-design.md "Extension and Injection Model"). Keys are widget ids;
    # values are "on" | "off" | "auto" | bool | a config dict (dict implies on).
    # KPress never interprets the config — it is serialized verbatim into the
    # #kpress-page-model block for the widget's own JS (schema-with-the-code).
    # Defaults merge under this map (settings is on unless turned off here).
    widgets: dict[str, Any] = field(default_factory=dict)
    # Optional document-tree transform (a callable, never serialized): applied
    # right after parsing. The parsed tree's `toc` (and the page-model headings
    # derived from it) is ALREADY computed at that point — a transform that
    # adds or changes headings must rebuild `tree.toc` itself (see the
    # transform-tree test for the pattern). Threaded from
    # BuildExtensions.transform_tree by the publisher.
    transform_tree: Callable[[DocumentTree], DocumentTree] | None = None
    # Page chrome slots: opaque site-owned HTML emitted verbatim by render_page
    # (head extra inside <head>; header/footer wrapped in .kpress-site-header /
    # .kpress-site-footer). KPress styles the wrappers but never interprets the
    # content; empty slots emit nothing.
    head_extra_html: str = ""
    header_html: str = ""
    footer_html: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# Built-in widget defaults, merged UNDER a host's widgets map: the settings
# gear ships on unless the host turns it off (widgets={"settings": "off"}).
DEFAULT_WIDGETS: dict[str, Any] = {"settings": "on"}


def parse_widgets(value: object) -> dict[str, Any]:
    """Normalize a widgets map: presence scalars + opaque config dicts.

    Each value becomes "on" | "off" | "auto" (bools normalize to on/off) or
    passes through verbatim as the widget's config dict (which implies on).
    Anything else fails loudly — consistent with the strict format.math /
    asset_mode stance (orig-1tkb): a typo must not silently ship different
    chrome than the operator intended. Every dialect (YAML ``format.widgets``,
    typed configs, dynamic ``KPressRenderRequest.widgets``) runs this so all
    surfaces publish identical widget data.
    """

    widgets: dict[str, Any] = {}
    raw_map: Mapping[object, object] = (
        cast("Mapping[object, object]", value) if isinstance(value, Mapping) else {}
    )
    for widget_id, raw in raw_map.items():
        if isinstance(raw, bool):
            widgets[str(widget_id)] = "on" if raw else "off"
        elif (isinstance(raw, str) and raw in {"on", "off", "auto"}) or isinstance(raw, dict):
            widgets[str(widget_id)] = raw
        else:
            msg = (
                f"Invalid format.widgets value for {widget_id!r}: {raw!r}; "
                f"expected 'on', 'off', 'auto', a boolean, or a config mapping"
            )
            raise KPressPublishError(msg)
    return widgets


def resolve_widgets(widgets: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve a widget presence map: defaults under host values, "off" removed.

    Values pass through verbatim (a dict is the widget's opaque config and
    implies on; "on"/"auto"/True are presence markers). KPress never interprets
    configs — they ride the #kpress-page-model block (or the dynamic render
    payload) to the widget's own JS.
    """

    merged: dict[str, Any] = {**DEFAULT_WIDGETS, **dict(widgets)}
    # Only explicit off markers remove a widget: `value not in ("off", False)`
    # would also drop integer 0 via `0 == False`.
    return {
        widget_id: value
        for widget_id, value in merged.items()
        if not (value is False or value == "off")
    }


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
