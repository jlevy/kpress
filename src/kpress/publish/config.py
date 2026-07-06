"""KPress publisher configuration."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, cast

from kpress.errors import KPressPublishError
from kpress.format.model import (
    AssetMode,
    DocumentTree,
    MathMode,
    OptimizerMode,
    ProseFont,
    TocMode,
    parse_widgets,
)
from kpress.publish.optimize import OptimizerBackend

YamlDict = dict[str, object]


@dataclass(frozen=True)
class SourceConfig:
    """Source tree discovery configuration."""

    path: str | Path = "."
    include: list[str] = field(default_factory=lambda: ["**/*.md"])
    exclude: list[str] = field(default_factory=lambda: ["public/**", ".kpress/**"])
    # Verbatim-copy glob patterns (logos, favicons, images). Matched files are
    # copied to the output at their source-relative paths, collision-checked
    # against rendered routes and reserved paths, and listed in the manifest.
    static: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FormatConfig:
    """Default document rendering configuration."""

    theme: str = "default"
    palette: str = "neutral"
    color_mode: str = "system"
    # Site default for the reading-font chooser (see RenderOptions.prose_font):
    # readers' persisted choices still win.
    prose_font: ProseFont = "serif"
    # Content card on the reading column (see RenderOptions.content_card).
    content_card: bool = True
    # Render the doc-title <h1> header (see RenderOptions.show_doc_header).
    # Sites whose pages open with their own heading structure (or whose chrome
    # already shows the title) pass False.
    show_doc_header: bool = True
    toc: TocMode = "auto"
    toc_min_headings: int = 4
    math: MathMode = "auto"
    diagrams: str = "auto"
    show_frontmatter: bool = True
    # Whitelist of additional pass-through HTML/XML tag names (YAML:
    # format.html.extra_tags). Unioned with the always-on <span>/<div> defaults and
    # admitted across every trust mode, carrying class/data-* but never style/on*/unsafe
    # URLs. Threaded into RenderOptions.extra_tags. Empty by default (output unchanged).
    extra_tags: tuple[str, ...] = ()
    # Widget presence + opaque config map (extension model layer D). Keys are
    # widget ids; values normalize to "on" | "off" | "auto" or pass through as
    # the widget's config dict (which implies on). KPress never interprets the
    # config (schema-with-the-code rule).
    widgets: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PublishConfig:
    """Static output settings."""

    output_dir: str | Path = "public"
    asset_mode: AssetMode = "linked"

    def resolved_asset_mode(self) -> AssetMode:
        return self.asset_mode


@dataclass(frozen=True)
class PdfPublishConfig:
    """Publisher PDF settings.

    Disambiguated from ``kpress.format.pdf.PdfOptions`` (the per-render
    options carrying ``output``/``backend``/``page_size``/etc.). The
    config dataclass declares what the *site* enables; the render
    dataclass parameterizes a single ``render_pdf`` call.
    """

    enabled: bool = False
    page_size: str = "Letter"


@dataclass(frozen=True)
class OptimizerOptions:
    """Optimizer settings.

    ``mode`` is ``none`` (publish content unchanged, no Node required) or
    ``full`` (run the optional html-minifier-next toolchain). There is no
    fallback: selecting ``full`` without the toolchain is an error.
    """

    mode: OptimizerMode = "none"
    precompress: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class KPressConfig:
    """Complete KPress static site config."""

    title: str = "KPress Site"
    base_url: str = ""
    build_date: str = ""
    # Page chrome slots: opaque site-owned HTML, resolved to strings at load
    # time (inline value or the *_file variant read relative to the config
    # file). KPress emits them verbatim and never interprets the content.
    head_extra_html: str = ""
    header_html: str = ""
    footer_html: str = ""
    redirects: list[dict[str, object]] = field(default_factory=list)
    sources: list[SourceConfig] = field(default_factory=lambda: [SourceConfig()])
    # Nested configs use default_factory: a shared default instance would leak
    # one caller's mutations (e.g. the widgets map) into every other config.
    format: FormatConfig = field(default_factory=FormatConfig)
    publish: PublishConfig = field(default_factory=PublishConfig)
    pdf: PdfPublishConfig = field(default_factory=PdfPublishConfig)
    optimizer: OptimizerOptions = field(default_factory=OptimizerOptions)
    config_path: Path | None = None
    # Path anchor for relative sources/output and the document-asset boundary.
    # File-based configs anchor on the config file's directory; programmatic
    # configs (no file) set this explicitly — otherwise the current directory
    # is the anchor, and staged content outside it would lose its media.
    # Mutually exclusive with config_path: the build rejects a config with both.
    base_dir: str | Path | None = None


@dataclass(frozen=True)
class BuildOptions:
    """Per-build options, including CLI overrides."""

    output_dir: Path | None = None
    asset_mode: AssetMode | None = None
    optimizer: OptimizerMode | None = None
    precompress: list[str] | None = None


@dataclass(frozen=True)
class BuildExtensions:
    """Host build-pipeline extensions (the extension model's layer E; see
    kpress-design.md "Extension and Injection Model").

    These are callables and stage objects, not config-file values: the pipeline
    is the Python-side extension seam (whole-artifact, build-time work). It
    stays an explicit ordered list — no priorities, no hook lifecycle.
    """

    # Ordered stages run over each deployable text artifact (html/css/js).
    # Entries are built-in stage names ("kpress:none" / "kpress:full") or stage
    # objects with the optimizer-backend shape. None derives the list from
    # optimizer.mode — full back-compat.
    pipeline: Sequence[str | OptimizerBackend] | None = None
    # Document-tree transform, applied right after parsing. The tree's `toc`
    # is already derived by then: a transform that adds or changes headings
    # must rebuild `tree.toc` itself for the TOC/page model to reflect it.
    transform_tree: Callable[[DocumentTree], DocumentTree] | None = None
    # Whole-page transform `(html, route) -> html`, applied to each rendered
    # page before the pipeline stages.
    transform_page_html: Callable[[str, str], str] | None = None


def _as_dict(value: object) -> YamlDict:
    if isinstance(value, dict):
        return cast(YamlDict, value)
    return {}


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return cast(list[object], value)
    return []


def _string_list(value: object, default: list[str]) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in cast(list[object], value)]
    if isinstance(value, str):
        return [value]
    return list(default)


# Closed value sets, shared by the YAML loader and validate_config so both
# dialects accept and reject exactly the same values. Open strings (theme,
# palette — hosts may ship their own preset CSS) are deliberately absent.
_TOC_MODES = ("off", "auto", "on")
_MATH_MODES = ("off", "auto")
_DIAGRAM_MODES = ("off", "auto", "mermaid")
_COLOR_MODES = ("system", "light", "dark")
_PROSE_FONTS = ("serif", "sans")
_ASSET_MODES = ("hosted", "linked", "hashed", "sealed")
_OPTIMIZER_MODES = ("none", "full")
_PRECOMPRESS_METHODS = ("gzip", "br")


def _checked_choice(name: str, value: object, allowed: tuple[str, ...]) -> str:
    """Membership-check a closed enum-like config value.

    Provided-but-invalid → `KPressPublishError` so a typo in production
    config fails the build instead of silently shipping a different policy
    (orig-1tkb). Omitted-value defaults are the caller's concern.
    """

    if not isinstance(value, str) or value not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"Invalid {name} {value!r}; expected one of {expected}"
        raise KPressPublishError(msg)
    return value


def _validated_optimizer_mode(optimizer: dict[str, object]) -> str:
    """Return the optimizer.mode value, raising on invalid provided values.

    Omitted → default `"none"`. Provided-but-invalid → `KPressPublishError`
    so a typo in production config fails the build instead of silently
    downgrading (orig-1tkb).
    """

    if "mode" not in optimizer:
        return "none"
    return _checked_choice("optimizer.mode", optimizer.get("mode"), _OPTIMIZER_MODES)


def _validated_precompress(value: object) -> list[str]:
    """Return optimizer.precompress as a list, raising on invalid methods."""

    if value is None:
        return []
    methods = _string_list(value, [])
    for method in methods:
        _ = _checked_choice("optimizer.precompress method", method, _PRECOMPRESS_METHODS)
    return methods


# A valid pass-through tag name: a standard HTML inline/flow element or a custom-element
# name — lowercase, starting with a letter, optionally containing digits/hyphens. The
# same shape markdown-it / nh3 will accept; an entry that is not a valid tag name fails
# the build loudly rather than silently admitting nothing.
_TAG_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")

# Tag names that must NEVER be admitted as pass-through, even though they match the shape
# regex. `script`/`style` are in nh3's clean-content set: admitting either makes ammonia
# raise (a hard render-time failure), so rejecting them at config time turns a confusing
# crash into a clear error. The rest are active/embedding/metadata elements that carry
# real risk (script execution, navigation, form capture, parser-context confusion) and
# have no place in a *styling* whitelist. Custom elements (hyphenated) are inert by the
# HTML spec, so the escape hatch for genuinely custom markup stays open.
_FORBIDDEN_EXTRA_TAGS = frozenset(
    {
        "script",
        "style",
        "iframe",
        "object",
        "embed",
        "base",
        "meta",
        "link",
        "noscript",
        "template",
        "textarea",
        "select",
        "option",
        "form",
        "title",
        "xmp",
        "plaintext",
        "noembed",
        "noframes",
    }
)


def _validated_extra_tags(value: object) -> tuple[str, ...]:
    """Return format.html.extra_tags as a tuple, raising on invalid or forbidden names."""

    if value is None:
        return ()
    tags = _string_list(value, [])
    for tag in tags:
        if not _TAG_NAME_RE.match(tag):
            msg = (
                f"Invalid format.html.extra_tags entry {tag!r}; expected a lowercase "
                f"HTML or custom-element tag name (letters, digits, hyphens)"
            )
            raise KPressPublishError(msg)
        if tag in _FORBIDDEN_EXTRA_TAGS:
            msg = (
                f"Forbidden format.html.extra_tags entry {tag!r}: active, embedding, and "
                f"metadata elements cannot be admitted as styleable pass-through tags. "
                f"Use a hyphenated custom-element name (e.g. 'x-callout') for custom markup."
            )
            raise KPressPublishError(msg)
    # De-duplicate while preserving order so the config round-trips deterministically.
    return tuple(dict.fromkeys(tags))


def _int_value(value: object, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _bool_value(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "on", "1"}:
            return True
        if normalized in {"false", "no", "off", "0"}:
            return False
    return default


_KNOWN_TOP_LEVEL_KEYS = frozenset({"site", "publish", "format", "pdf", "optimizer", "sources"})
_KNOWN_PUBLISH_KEYS = frozenset({"output_dir", "asset_mode"})
_KNOWN_FORMAT_KEYS = frozenset(
    {
        "theme",
        "palette",
        "color_mode",
        "prose_font",
        "content_card",
        "show_doc_header",
        "toc",
        "toc_min_headings",
        "math",
        "diagrams",
        "show_frontmatter",
        "widgets",
        "html",
    }
)
_KNOWN_FORMAT_HTML_KEYS = frozenset({"extra_tags"})
_KNOWN_OPTIMIZER_KEYS = frozenset({"mode", "precompress"})
_KNOWN_PDF_KEYS = frozenset({"enabled", "page_size"})
_CHROME_SLOT_NAMES = ("head_extra_html", "header_html", "footer_html")
_KNOWN_SITE_KEYS = frozenset(
    {"title", "base_url", "build_date", "redirects"}
    | set(_CHROME_SLOT_NAMES)
    | {f"{name}_file" for name in _CHROME_SLOT_NAMES}
)


def _reject_unknown_keys(section: str, data: YamlDict, allowed: frozenset[str]) -> None:
    """Raise on unrecognized YAML keys.

    Silent key-drop is dangerous after the v1 seal removal: a user with a
    stale ``assets: { external: { allowlist: [...] } }`` block thinks the
    allowlist still applies and gets a confidently broken build (no fetch,
    no allowlist enforcement). Surfacing unknown keys catches that, plus
    typos in current keys (`asset_mod` → `asset_mode`).
    """

    unknown = sorted(set(data) - allowed)
    if unknown:
        scope = section or "top-level"
        msg = (
            f"Unknown KPress config key(s) under {scope}: {unknown!r}. "
            f"Recognized keys: {sorted(allowed)!r}"
        )
        raise KPressPublishError(msg)


def _parse_yaml_text(text: str) -> YamlDict:
    """Parse a KPress config YAML string into a top-level mapping.

    Routes through ``frontmatter_format.from_yaml_string`` (which uses
    ``ruamel.yaml`` under the hood — the same parser the frontmatter /
    sidematter path uses) so multi-line scalars, anchors, quoted colons,
    and duplicate-key detection all work identically across config and
    document metadata. Raises :class:`KPressPublishError` when the YAML
    document is not a top-level mapping.
    """

    from frontmatter_format import from_yaml_string

    parsed: object = from_yaml_string(text) if text.strip() else {}
    if not isinstance(parsed, dict):
        msg = f"KPress config must be a YAML mapping at the top level, got {type(parsed).__name__}"
        raise KPressPublishError(msg)
    return cast(YamlDict, parsed)


_INLINE_ASSET_MODE_ERROR = (
    "publish.asset_mode 'inline' is not yet supported for site builds: the "
    "output would not be self-contained (ES-module imports and fonts stay "
    "external). Use 'sealed' for a fully offline site."
)


def validate_config(config: KPressConfig) -> KPressConfig:
    """Semantic invariants for every KPressConfig, however constructed.

    ``load_config`` enforces these for the YAML dialect at parse time; the
    typed (programmatic) dialect must fail just as loudly — a type-legal value
    like ``asset_mode="inline"`` silently ships a feature-broken site
    (orig-7ehk), a widget-presence typo must not silently ship different
    chrome (orig-1tkb), and every closed value set (asset/optimizer/math/toc/
    diagrams/color-mode/precompress) is membership-checked so a cast-away typo
    cannot ship a different publish policy. Returns the config with widget
    presence scalars normalized, so both dialects publish identical page-model
    data. The ``BuildOptions.asset_mode`` override remains the deliberate
    escape hatch (it is applied from options, after this check).
    """

    if config.publish.asset_mode == "inline":
        raise KPressPublishError(_INLINE_ASSET_MODE_ERROR)
    _ = _checked_choice("publish.asset_mode", config.publish.asset_mode, _ASSET_MODES)
    _ = _checked_choice("optimizer.mode", config.optimizer.mode, _OPTIMIZER_MODES)
    for method in config.optimizer.precompress:
        _ = _checked_choice("optimizer.precompress method", method, _PRECOMPRESS_METHODS)
    _ = _checked_choice("format.toc", config.format.toc, _TOC_MODES)
    _ = _checked_choice("format.math", config.format.math, _MATH_MODES)
    _ = _checked_choice("format.diagrams", config.format.diagrams, _DIAGRAM_MODES)
    _ = _checked_choice("format.color_mode", config.format.color_mode, _COLOR_MODES)
    _ = _checked_choice("format.prose_font", config.format.prose_font, _PROSE_FONTS)
    extra_tags = _validated_extra_tags(list(config.format.extra_tags))
    widgets = parse_widgets(config.format.widgets)
    if widgets != config.format.widgets or extra_tags != config.format.extra_tags:
        config = replace(
            config, format=replace(config.format, widgets=widgets, extra_tags=extra_tags)
        )
    return config


def _resolve_chrome_slot(site: YamlDict, name: str, config_dir: Path) -> str:
    """Resolve one chrome slot: the inline value or the ``*_file`` variant.

    File paths resolve relative to the config file's directory. Setting both
    forms for the same slot is an error.
    """

    inline = site.get(name)
    file_key = f"{name}_file"
    file_value = site.get(file_key)
    if inline is not None and file_value is not None:
        msg = f"site.{name} and site.{file_key} are mutually exclusive; set one"
        raise KPressPublishError(msg)
    if file_value is not None:
        slot_path = config_dir / str(file_value)
        if not slot_path.is_file():
            msg = f"site.{file_key} not found: {slot_path}"
            raise KPressPublishError(msg)
        return slot_path.read_text(encoding="utf-8")
    return str(inline) if inline is not None else ""


def load_config(path: Path | str = "kpress.yml") -> KPressConfig:
    """Load a KPress config file."""

    config_path = Path(path)
    data = _parse_yaml_text(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    _reject_unknown_keys("", data, _KNOWN_TOP_LEVEL_KEYS)
    site = _as_dict(data.get("site", {}))
    publish = _as_dict(data.get("publish", {}))
    fmt = _as_dict(data.get("format", {}))
    pdf = _as_dict(data.get("pdf", {}))
    optimizer = _as_dict(data.get("optimizer", {}))
    fmt_html = _as_dict(fmt.get("html", {}))
    _reject_unknown_keys("site", site, _KNOWN_SITE_KEYS)
    _reject_unknown_keys("publish", publish, _KNOWN_PUBLISH_KEYS)
    _reject_unknown_keys("format", fmt, _KNOWN_FORMAT_KEYS)
    _reject_unknown_keys("format.html", fmt_html, _KNOWN_FORMAT_HTML_KEYS)
    _reject_unknown_keys("pdf", pdf, _KNOWN_PDF_KEYS)
    _reject_unknown_keys("optimizer", optimizer, _KNOWN_OPTIMIZER_KEYS)
    raw_sources = _as_list(data.get("sources", [])) or [{"path": "."}]
    sources: list[SourceConfig] = []
    for raw_source in raw_sources:
        item = _as_dict(raw_source)
        if not item:
            continue
        sources.append(
            SourceConfig(
                path=str(item.get("path", ".")),
                include=_string_list(item.get("include"), ["**/*.md"]),
                exclude=_string_list(item.get("exclude"), ["public/**", ".kpress/**"]),
                static=_string_list(item.get("static"), []),
            )
        )
    # Omitted enum-like fields default; provided-but-invalid values fail
    # loudly. A typo in production config silently shipping a different
    # asset/optimizer/math policy than the operator intended is a real
    # publishing risk and inconsistent with KPress's elsewhere-strict
    # reserved-path / collision / unsafe-asset stance (orig-1tkb).
    toc = _checked_choice("format.toc", fmt.get("toc"), _TOC_MODES) if "toc" in fmt else "auto"
    math = _checked_choice("format.math", fmt.get("math"), _MATH_MODES) if "math" in fmt else "auto"
    diagrams = (
        _checked_choice("format.diagrams", fmt.get("diagrams"), _DIAGRAM_MODES)
        if "diagrams" in fmt
        else "auto"
    )
    color_mode = (
        _checked_choice("format.color_mode", fmt.get("color_mode"), _COLOR_MODES)
        if "color_mode" in fmt
        else "system"
    )
    prose_font = (
        _checked_choice("format.prose_font", fmt.get("prose_font"), _PROSE_FONTS)
        if "prose_font" in fmt
        else "serif"
    )
    if "asset_mode" in publish:
        asset_mode = publish.get("asset_mode")
        # `inline` is rejected at the config surface until it is truly
        # self-contained (orig-7ehk): inlined ES modules still import
        # sibling files, so the published pages would silently lose reader
        # features. The programmatic BuildOptions override keeps accepting it
        # for the equivalence harness and future single-file work.
        if asset_mode == "inline":
            raise KPressPublishError(_INLINE_ASSET_MODE_ERROR)
        if asset_mode not in {"hosted", "linked", "hashed", "sealed"}:
            msg = (
                f"Invalid publish.asset_mode {asset_mode!r}; "
                f"expected one of 'hosted', 'linked', 'hashed', 'sealed'"
            )
            raise KPressPublishError(msg)
    else:
        asset_mode = "linked"
    redirects = [_as_dict(rule) for rule in _as_list(site.get("redirects", [])) if _as_dict(rule)]
    config_dir = config_path.parent
    return KPressConfig(
        title=str(site.get("title", "KPress Site")),
        base_url=str(site.get("base_url", "")),
        build_date=str(site.get("build_date", "")),
        head_extra_html=_resolve_chrome_slot(site, "head_extra_html", config_dir),
        header_html=_resolve_chrome_slot(site, "header_html", config_dir),
        footer_html=_resolve_chrome_slot(site, "footer_html", config_dir),
        redirects=redirects,
        sources=sources or [SourceConfig()],
        format=FormatConfig(
            theme=str(fmt.get("theme", "default")),
            palette=str(fmt.get("palette", "neutral")),
            color_mode=color_mode,
            prose_font=cast(ProseFont, prose_font),
            content_card=_bool_value(fmt.get("content_card"), True),
            show_doc_header=_bool_value(fmt.get("show_doc_header"), True),
            toc=cast(TocMode, toc),
            toc_min_headings=_int_value(fmt.get("toc_min_headings"), 4),
            math=cast(MathMode, math),
            diagrams=diagrams,
            show_frontmatter=_bool_value(fmt.get("show_frontmatter"), True),
            widgets=parse_widgets(fmt.get("widgets")),
            extra_tags=_validated_extra_tags(fmt_html.get("extra_tags")),
        ),
        publish=PublishConfig(
            output_dir=str(publish.get("output_dir", "public")),
            asset_mode=cast(AssetMode, asset_mode),
        ),
        pdf=PdfPublishConfig(
            enabled=bool(pdf.get("enabled", False)),
            page_size=str(pdf.get("page_size", "Letter")),
        ),
        optimizer=OptimizerOptions(
            mode=cast(OptimizerMode, _validated_optimizer_mode(optimizer)),
            precompress=_validated_precompress(optimizer.get("precompress")),
        ),
        config_path=config_path,
    )
