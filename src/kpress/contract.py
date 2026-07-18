"""Current public KPress contract constants.

KPress is new enough that the package does not need compatibility shims.
These names describe the current supported surface; changing them requires updating
this contract, docs, tests, and accepted goldens in the same patch.
"""

from __future__ import annotations

CONTRACT_VERSION = "kpress-contract-v1"
ASSET_MANIFEST_SCHEMA_VERSION = "kpress-asset-manifest-v2"
BUILD_MANIFEST_SCHEMA_VERSION = "kpress-build-manifest-v2"

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
    "AssetPolicy",
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
    "materialize_package_assets",
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
    "FormatConfig",
    "KPressConfig",
    "OptimizerOptions",
    "OutputFile",
    "PdfPublishConfig",
    "ProbeResult",
    "PublishConfig",
    "SourceConfig",
    "build_html",
    "build_site",
    "export_document",
    "get_optimizer",
    "load_config",
    "optimize_text",
    "probe_capability",
    "resolve_stage",
    "validate_config",
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
    "kpress-figcaption",
    "kpress-figure",
    "kpress-frontmatter-error",
    "kpress-frontmatter",
    "kpress-diagram",
    "kpress-diagram-rendered",
    "kpress-diagram-source",
    "kpress-header-actions",
    "kpress-header-grow",
    "kpress-header-row",
    "kpress-image",
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
    "--kpress-doc-danger",
    "--kpress-doc-link",
    "--kpress-doc-muted",
    "--kpress-doc-success",
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
    "--kpress-page-margin-block-start",
    "--kpress-page-margin-inline",
    "--kpress-radius-none",
    "--kpress-radius-sm",
    "--kpress-radius-md",
    "--kpress-radius-lg",
    "--kpress-radius-pill",
    "--kpress-transition-fast",
    "--kpress-transition-med",
    "--kpress-transition-slow",
    "--kpress-transition-fade",
    "--kpress-card-border",
    "--kpress-card-shadow",
    "--kpress-settings-inset-block",
    "--kpress-settings-inset-inline",
    "--kpress-print-font-size",
    "--kpress-print-footer",
    "--kpress-print-page-margin",
)

# The deliberately narrow fragment-hosting seam. PUBLIC_CSS_CLASSES and
# PUBLIC_CSS_VARIABLES pin the complete reader contract; embedding applications
# should prefer these subsets so they do not couple their shell to KPress chrome
# or component internals. The data attributes on public tables are pinned
# separately by PUBLIC_DATA_ATTRIBUTES.
PUBLIC_FRAGMENT_CSS_CLASSES = (
    "kpress",
    "kpress-content-with-toc",
    "kpress-doc",
    "kpress-doc-layout",
    "kpress-figcaption",
    "kpress-figure",
    "kpress-image",
    "kpress-long-text",
    "kpress-no-print",
    "kpress-print-only",
    "kpress-print-surface",
    "kpress-prose",
    "kpress-table",
    "kpress-table-wrap",
)

PUBLIC_FRAGMENT_CSS_VARIABLES = (
    "--kpress-doc-accent",
    "--kpress-doc-bg",
    "--kpress-doc-border",
    "--kpress-doc-code-bg",
    "--kpress-doc-danger",
    "--kpress-doc-link",
    "--kpress-doc-muted",
    "--kpress-doc-success",
    "--kpress-doc-surface-bg",
    "--kpress-doc-surface-hover",
    "--kpress-doc-surface-selected",
    "--kpress-doc-text",
    "--kpress-font-body",
    "--kpress-font-footnote",
    "--kpress-font-mono",
    "--kpress-font-prose",
    "--kpress-font-sans",
    "--kpress-font-table",
    "--kpress-measure",
    "--kpress-page-margin-block-start",
    "--kpress-page-margin-inline",
    "--kpress-print-font-size",
    "--kpress-print-footer",
    "--kpress-print-page-margin",
)

# The host-override seam: tokens KPress CSS *consumes* (never declares) via
# `var(--kpress-host-X, <default>)`, so an embedding host or site can theme
# documents from outside. Consumed-only means the declared-variable scan that
# covers PUBLIC_CSS_VARIABLES cannot pin these; the contract test scans the
# shipped CSS for var() consumption sites instead.
# Host-override seam: tokens consumed via var(--kpress-host-X, <default>). The COLOR
# tokens were retired when the palette moved to the direct, per-theme×palette model
# (see style-tokens.css "Palette options"): an embedding host now re-themes by setting
# the resolved --kpress-doc-* / --color-* tokens directly, not through a --kpress-host-*
# color fallback. The font and settings-inset seams remain.
PUBLIC_HOST_CSS_VARIABLES = (
    "--kpress-host-font-body",
    "--kpress-host-font-footnote",
    "--kpress-host-font-mono",
    "--kpress-host-font-prose",
    "--kpress-host-font-prose-sans",
    "--kpress-host-font-sans",
    "--kpress-host-font-table",
    "--kpress-host-settings-inset-block",
    "--kpress-host-settings-inset-inline",
)

# Stable per-cell table data-* hooks kpress emits for downstream enrichment. These are
# part of the public contract: kpress emits them so a downstream decorator (a host app's
# table plugin, a future static-site builder) can select a column by name and detect
# numeric columns. kpress itself never consumes them and never imports a decorator.
PUBLIC_DATA_ATTRIBUTES = (
    "data-col",
    "data-kpress-numeric",
)

# Whitelisted pass-through HTML/XML tags: the input contract is "Markdown + a known set
# of HTML tags". These tags reach the rendered output untouched under the sanitized
# trust mode and trivially under trusted. `<span>`/`<div>` are always allowed, matching
# GitHub / CommonMark renderer norms; a host activates more through
# `format.html.extra_tags` (RenderOptions.extra_tags), which is unioned with this
# default set per render.
PUBLIC_PASS_THROUGH_TAGS = (
    "div",
    "span",
)

# Attribute policy on tags admitted only via the whitelist (custom extra_tags): only
# `class` and the `data-*` prefix survive (data-* rides the generic-prefix allowance,
# so it is not enumerated here). `<span>`/`<div>` are also part of the sanitizer's
# standard allow-set and keep its standard global attributes. `style`, `on*` handlers,
# and unsafe-URL attributes stay sanitized on every tag — this is a styleable
# pass-through, never "turn sanitization off".
PUBLIC_PASS_THROUGH_ATTRIBUTES = ("class",)
PUBLIC_PASS_THROUGH_ATTRIBUTE_PREFIXES = ("data-",)

PUBLIC_TEMPLATE_VARIABLES: dict[str, tuple[str, ...]] = {
    "page.html.jinja": (
        "asset_tags",
        "footer_html",
        "fragment_html",
        "head_extra_html",
        "header_html",
        "palette",
        "prose_font",
        "resolved_theme",
        "theme_mode",
        "title",
    ),
}

# Built-in build-pipeline stage names (BuildExtensions.pipeline entries).
PUBLIC_PIPELINE_STAGES = ("none", "full")

# Extension-model name contracts (docs/kpress-design.md "Extension and Injection
# Model"): the same discipline as PUBLIC_CSS_* applied to the client seams.

# Built-in chrome widget ids registered through kpress.widgets.
PUBLIC_WIDGETS = ("settings",)

# Built-in behavior ids registered through kpress.behaviors (bindings over
# server-rendered markup; each is overridable by id). "theme" is the engine's
# initialization (read persisted mode through the live storage adapter, stamp
# root attrs, track OS changes): an embed host that owns theme resolution
# overrides it so kpress never touches the root theme attrs.
PUBLIC_BEHAVIORS = (
    "toc",
    "tooltip",
    "footnote-preview",
    "history",
    "code-copy",
    "video",
    "tables",
    "tabs",
    "diagrams",
    "theme",
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
    "js/history.js": ("initKpressHistory",),
    "js/host.js": ("HOST_BEHAVIOR_ID", "initKpressHost"),
    "js/icons.js": ("icon",),
    "js/overlay.js": (
        "OVERLAY_VIEWPORT_MARGIN_PX",
        "OVERLAY_DEFAULT_GAP_PX",
        "dismissOnEscape",
        "dismissOnResize",
        "toggleBackdrop",
    ),
    "js/viewport.js": (
        "resolveKpressViewport",
        "viewportBounds",
        "rectRelativeToViewport",
        "addViewportResizeListener",
        "viewportScrollContext",
    ),
}

BUILD_MANIFEST_REQUIRED_KEYS = (
    "schema_version",
    "output_dir",
    "files",
    "assets",
    "routes",
    "diagnostics",
    "pipeline",
)

ASSET_MANIFEST_REQUIRED_KEYS = ("schema_version", "assets", "import_map")

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
    "PUBLIC_FRAGMENT_CSS_CLASSES",
    "PUBLIC_FRAGMENT_CSS_VARIABLES",
    "PUBLIC_HOST_CSS_VARIABLES",
    "PUBLIC_JS_EXPORTS",
    "PUBLIC_PACKAGE_API",
    "PUBLIC_PAGE_MODEL_KEYS",
    "PUBLIC_PASS_THROUGH_ATTRIBUTES",
    "PUBLIC_PASS_THROUGH_ATTRIBUTE_PREFIXES",
    "PUBLIC_PASS_THROUGH_TAGS",
    "PUBLIC_PIPELINE_STAGES",
    "PUBLIC_PUBLISH_API",
    "PUBLIC_TEMPLATE_VARIABLES",
    "PUBLIC_WIDGETS",
]
