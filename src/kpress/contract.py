"""Current public KPress contract constants.

KPress is new enough that the package does not need compatibility shims.
These names describe the current supported surface; changing them requires updating
this contract, docs, tests, and accepted goldens in the same patch.
"""

from __future__ import annotations

CONTRACT_VERSION = "kpress-contract-v1"
ASSET_MANIFEST_SCHEMA_VERSION = "kpress-asset-manifest-v1"
BUILD_MANIFEST_SCHEMA_VERSION = "kpress-build-manifest-v1"

PUBLIC_PACKAGE_API = (
    "ASSET_MANIFEST_SCHEMA_VERSION",
    "BUILD_MANIFEST_SCHEMA_VERSION",
    "CONTRACT_VERSION",
    "KPressAsset",
    "KPressAssetNotFoundError",
    "KPressExportRequest",
    "KPressInvalidRequestError",
    "KPressMissingOptionalDependencyError",
    "KPressOptimizerError",
    "KPressPublishError",
    "KPressRenderError",
    "KPressRenderRequest",
    "PrintProfile",
    "ThemeMode",
    "__version__",
    "clear_render_cache",
    "export_document",
    "get_static_asset",
    "render_view",
    "set_static_root_for_tests",
)

PUBLIC_FORMAT_API = (
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
)

PUBLIC_PUBLISH_API = (
    "BuildExtensions",
    "BuildOptions",
    "BuildReport",
    "KPressConfig",
    "OptimizerOptions",
    "OutputFile",
    "PdfPublishConfig",
    "ProbeResult",
    "PublishConfig",
    "build_html",
    "build_site",
    "export_document",
    "get_optimizer",
    "load_config",
    "optimize_text",
    "probe_capability",
    "resolve_stage",
)

PUBLIC_CSS_CLASSES = (
    "annotated-para",
    "boxed-text",
    "centered-headers",
    "citation",
    "claim",
    "concepts",
    "debug",
    "description",
    "frame-capture",
    "full-text",
    "hero",
    "highlight",
    "hidden",
    "justify",
    "key-claims",
    "kpress",
    "kpress-code",
    "kpress-code-copy",
    "kpress-code-scroll",
    "kpress-content-with-toc",
    "kpress-doc",
    "kpress-doc-header",
    "kpress-doc-layout",
    "kpress-footnotes",
    "kpress-frontmatter-error",
    "kpress-frontmatter",
    "kpress-diagram",
    "kpress-diagram-rendered",
    "kpress-diagram-source",
    "kpress-header-actions",
    "kpress-header-grow",
    "kpress-header-row",
    "kpress-long-list",
    "kpress-long-text",
    "kpress-math",
    "kpress-math-display",
    "kpress-math-inline",
    "kpress-math-render",
    "kpress-math-semantic",
    "kpress-menu",
    "kpress-menu-chooser",
    "kpress-menu-seg",
    "kpress-menu-select",
    "kpress-mermaid",
    "kpress-metadata",
    "kpress-no-print",
    "kpress-page-spacer",
    "kpress-page-main",
    "kpress-print-only",
    "kpress-print-surface",
    "kpress-prose",
    "kpress-settings",
    "kpress-settings-btn",
    "kpress-settings-menu",
    "kpress-site-footer",
    "kpress-site-header",
    "kpress-source",
    "kpress-source-header",
    "kpress-source-meta",
    "kpress-source-truncation-warning",
    "kpress-svg-diagram",
    "kpress-tab-button",
    "kpress-tab-list",
    "kpress-tab-panel",
    "kpress-tabs",
    "kpress-table",
    "kpress-table-wrap",
    "kpress-task",
    "kpress-toc",
    "kpress-toc-backdrop",
    "kpress-toc-title",
    "kpress-toc-toggle",
    "kpress-tooltip",
    "kpress-video-backdrop",
    "kpress-video-popover",
    "kpress-widget",
    "para",
    "para-caption",
    "shaded-text",
    "summary",
    "subtitle",
    "tab-button-active",
    "tab-button-inactive",
    "thumbnail",
    "video-gallery",
    "video-item",
)

PUBLIC_CSS_VARIABLES = (
    "--kpress-doc-accent",
    "--kpress-doc-bg",
    "--kpress-doc-border",
    "--kpress-doc-code-bg",
    "--kpress-doc-link",
    "--kpress-doc-muted",
    "--kpress-doc-surface-bg",
    "--kpress-doc-surface-hover",
    "--kpress-doc-surface-selected",
    "--kpress-doc-text",
    "--kpress-font-body",
    "--kpress-font-features-sans",
    "--kpress-font-footnote",
    "--kpress-font-size-mono",
    "--kpress-font-size-normal",
    "--kpress-font-size-small",
    "--kpress-font-mono",
    "--kpress-font-prose",
    "--kpress-font-punctuation",
    "--kpress-font-sans",
    "--kpress-font-table",
    "--kpress-font-weight-sans-bold",
    "--kpress-font-weight-sans-medium",
    "--kpress-caps-heading-size-multiplier",
    "--kpress-caps-spacing",
    "--kpress-caps-transform",
    "--kpress-measure",
    "--kpress-settings-inset-block",
    "--kpress-settings-inset-inline",
    "--kpress-print-font-size",
    "--kpress-print-footer",
    "--kpress-print-page-margin",
)

# Stable per-cell table data-* hooks kpress emits for downstream enrichment. These are
# part of the public contract: kpress emits them so a downstream decorator (a host app's
# table plugin, a future static-site builder) can select a column by name and detect
# numeric columns. kpress itself never consumes them and never imports a decorator.
PUBLIC_DATA_ATTRIBUTES = (
    "data-col",
    "data-kpress-numeric",
)

PUBLIC_TEMPLATE_VARIABLES: dict[str, tuple[str, ...]] = {
    "fragment.html.jinja": ("body_html",),
    "page.html.jinja": (
        "asset_tags",
        "footer_html",
        "fragment_html",
        "head_extra_html",
        "header_html",
        "theme_mode",
        "title",
    ),
    "components/code-block.html.jinja": ("code", "language_class"),
    "components/footnotes.html.jinja": ("footnote_items",),
    "components/frontmatter.html.jinja": ("metadata_rows",),
    "components/metadata.html.jinja": ("title",),
    "components/source.html.jinja": ("source_text",),
    "components/table.html.jinja": ("table_html",),
    "components/toc.html.jinja": ("toc_items",),
}

# Built-in build-pipeline stage names (BuildExtensions.pipeline entries).
PUBLIC_PIPELINE_STAGES = ("kpress:none", "kpress:full")

# Extension-model name contracts (kpress-design.md "Extension and Injection
# Model"): the same discipline as PUBLIC_CSS_* applied to the client seams.

# Built-in chrome widget ids registered through kpress.widgets.
PUBLIC_WIDGETS = ("settings",)

# Built-in behavior ids registered through kpress.behaviors (bindings over
# server-rendered markup; each is overridable by id).
PUBLIC_BEHAVIORS = (
    "toc",
    "tooltip",
    "footnote-preview",
    "code-copy",
    "video",
    "tables",
    "tabs",
    "diagrams",
)

# Keys of the #kpress-page-model JSON block (layer A published data).
PUBLIC_PAGE_MODEL_KEYS = (
    "version",
    "title",
    "route",
    "profile",
    "headings",
    "widgets",
)

# Stability-pinned ES-module exports (the wrap-one-aspect seam). Start narrow:
# only what the documented demos exercise; an export is a contract, so names
# are added deliberately, not by reflex.
PUBLIC_JS_EXPORTS: dict[str, tuple[str, ...]] = {
    "js/runtime.js": ("getModel", "on", "off", "emit", "storage", "widgets", "behaviors"),
    "js/theme.js": ("setKpressTheme", "initKpressTheme", "bindThemeToggleControls"),
    "js/menu.js": ("bindMenu", "markChecked"),
    "js/toc.js": ("initKpressToc", "TOC_TOGGLE_SCROLL_THRESHOLD_PX", "defaultTocToggleVisible"),
    "js/tooltips.js": (
        "initKpressTooltips",
        "chooseTooltipPosition",
        "positionTooltip",
        "TOOLTIP_SHOW_DELAY_MS",
    ),
    "js/settings-widget.js": ("mountSettings",),
}

BUILD_MANIFEST_REQUIRED_KEYS = (
    "schema_version",
    "output_dir",
    "files",
    "assets",
    "routes",
    "diagnostics",
)

ASSET_MANIFEST_REQUIRED_KEYS = ("schema_version", "assets")

__all__ = [
    "ASSET_MANIFEST_REQUIRED_KEYS",
    "ASSET_MANIFEST_SCHEMA_VERSION",
    "BUILD_MANIFEST_REQUIRED_KEYS",
    "BUILD_MANIFEST_SCHEMA_VERSION",
    "CONTRACT_VERSION",
    "PUBLIC_BEHAVIORS",
    "PUBLIC_CSS_CLASSES",
    "PUBLIC_CSS_VARIABLES",
    "PUBLIC_DATA_ATTRIBUTES",
    "PUBLIC_FORMAT_API",
    "PUBLIC_JS_EXPORTS",
    "PUBLIC_PACKAGE_API",
    "PUBLIC_PAGE_MODEL_KEYS",
    "PUBLIC_PIPELINE_STAGES",
    "PUBLIC_PUBLISH_API",
    "PUBLIC_TEMPLATE_VARIABLES",
    "PUBLIC_WIDGETS",
]
