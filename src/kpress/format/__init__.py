"""Core KPress document format primitives."""

from __future__ import annotations

from kpress.format.assets import AssetManifest, AssetRef, read_package_text
from kpress.format.markdown import parse_markdown
from kpress.format.model import (
    AssetMode,
    Diagnostic,
    DiagramMode,
    DocumentInput,
    DocumentProfile,
    DocumentTree,
    Footnote,
    Heading,
    MathMode,
    RenderedDocument,
    RenderedPage,
    RenderOptions,
    RenderResult,
    TocEntry,
    TocMode,
    TrustMode,
)
from kpress.format.render import render_document_from_text, render_fragment, render_page
from kpress.format.theme import FontSpec, ResolvedTheme, ThemeSpec, normalize_theme_mode

__all__ = [
    "AssetManifest",
    "AssetMode",
    "AssetRef",
    "Diagnostic",
    "DiagramMode",
    "DocumentInput",
    "DocumentProfile",
    "DocumentTree",
    "FontSpec",
    "Footnote",
    "Heading",
    "MathMode",
    "RenderedDocument",
    "RenderedPage",
    "RenderOptions",
    "RenderResult",
    "ResolvedTheme",
    "ThemeSpec",
    "TocEntry",
    "TocMode",
    "TrustMode",
    "normalize_theme_mode",
    "parse_markdown",
    "read_package_text",
    "render_document_from_text",
    "render_fragment",
    "render_page",
]
