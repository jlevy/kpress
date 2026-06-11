"""KPress publisher configuration."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from kpress.errors import KPressPublishError
from kpress.format.model import AssetMode, MathMode, OptimizerMode, TocMode

YamlDict = dict[str, object]


@dataclass(frozen=True)
class SourceConfig:
    """Source tree discovery configuration."""

    path: str = "."
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
    toc: TocMode = "auto"
    toc_min_headings: int = 4
    math: MathMode = "auto"
    diagrams: str = "auto"
    show_frontmatter: bool = True
    # Widget presence + opaque config map (extension model layer D). Keys are
    # widget ids; values normalize to "on" | "off" | "auto" or pass through as
    # the widget's config dict (which implies on). KPress never interprets the
    # config (schema-with-the-code rule).
    widgets: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PublishConfig:
    """Static output settings."""

    output_dir: str = "public"
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
    format: FormatConfig = FormatConfig()
    publish: PublishConfig = PublishConfig()
    pdf: PdfPublishConfig = PdfPublishConfig()
    optimizer: OptimizerOptions = OptimizerOptions()
    config_path: Path | None = None


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
    pipeline: Sequence[Any] | None = None
    # Document-tree transform, applied after parsing and before the TOC/page
    # model are derived (so injected headings show up in both).
    transform_tree: Callable[[Any], Any] | None = None
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


def _validated_optimizer_mode(optimizer: dict[str, object]) -> str:
    """Return the optimizer.mode value, raising on invalid provided values.

    Omitted → default `"none"`. Provided-but-invalid → `KPressPublishError`
    so a typo in production config fails the build instead of silently
    downgrading (orig-1tkb).
    """

    if "mode" not in optimizer:
        return "none"
    mode = optimizer.get("mode")
    if mode not in {"none", "full"}:
        msg = f"Invalid optimizer.mode {mode!r}; expected one of 'none', 'full'"
        raise KPressPublishError(msg)
    return cast(str, mode)


def _validated_precompress(value: object) -> list[str]:
    """Return optimizer.precompress as a list, raising on invalid methods."""

    if value is None:
        return []
    methods = _string_list(value, [])
    for method in methods:
        if method not in {"gzip", "br"}:
            msg = f"Invalid optimizer.precompress method {method!r}; expected 'gzip' or 'br'"
            raise KPressPublishError(msg)
    return methods


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
        "toc",
        "toc_min_headings",
        "math",
        "diagrams",
        "show_frontmatter",
        "widgets",
    }
)
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


def _parse_widgets(value: object) -> dict[str, Any]:
    """Normalize ``format.widgets``: presence scalars + opaque config dicts.

    Each value becomes "on" | "off" | "auto" (bools normalize to on/off) or
    passes through verbatim as the widget's config dict (which implies on).
    Anything else fails loudly — consistent with the strict format.math /
    asset_mode stance (orig-1tkb): a typo must not silently ship different
    chrome than the operator intended.
    """

    widgets: dict[str, Any] = {}
    for widget_id, raw in _as_dict(value).items():
        if isinstance(raw, bool):
            widgets[str(widget_id)] = "on" if raw else "off"
        elif isinstance(raw, str) and raw in {"on", "off", "auto"}:
            widgets[str(widget_id)] = raw
        elif isinstance(raw, dict):
            widgets[str(widget_id)] = raw
        else:
            msg = (
                f"Invalid format.widgets value for {widget_id!r}: {raw!r}; "
                f"expected 'on', 'off', 'auto', a boolean, or a config mapping"
            )
            raise KPressPublishError(msg)
    return widgets


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
    _reject_unknown_keys("site", site, _KNOWN_SITE_KEYS)
    _reject_unknown_keys("publish", publish, _KNOWN_PUBLISH_KEYS)
    _reject_unknown_keys("format", fmt, _KNOWN_FORMAT_KEYS)
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
    toc = str(fmt.get("toc", "auto"))
    if toc not in {"off", "auto", "on"}:
        toc = "auto"
    # Omitted enum-like fields default; provided-but-invalid values fail
    # loudly. A typo in production config silently shipping a different
    # asset/optimizer/math policy than the operator intended is a real
    # publishing risk and inconsistent with KPress's elsewhere-strict
    # reserved-path / collision / unsafe-asset stance (orig-1tkb).
    if "math" in fmt:
        math = str(fmt.get("math"))
        if math not in {"off", "auto"}:
            msg = f"Invalid format.math {math!r}; expected one of 'off', 'auto'"
            raise KPressPublishError(msg)
    else:
        math = "auto"
    if "asset_mode" in publish:
        asset_mode = publish.get("asset_mode")
        # `inline` is rejected at the config surface until it is truly
        # self-contained (orig-7ehk): inlined ES modules still import
        # sibling files, so the published pages would silently lose reader
        # features. The programmatic BuildOptions override keeps accepting it
        # for the equivalence harness and future single-file work.
        if asset_mode == "inline":
            msg = (
                "publish.asset_mode 'inline' is not yet supported for site builds: the "
                "output would not be self-contained (ES-module imports and fonts stay "
                "external). Use 'sealed' for a fully offline site."
            )
            raise KPressPublishError(msg)
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
            color_mode=str(fmt.get("color_mode", "system")),
            toc=cast(TocMode, toc),
            toc_min_headings=_int_value(fmt.get("toc_min_headings"), 4),
            math=cast(MathMode, math),
            diagrams=str(fmt.get("diagrams", "auto")),
            show_frontmatter=_bool_value(fmt.get("show_frontmatter"), True),
            widgets=_parse_widgets(fmt.get("widgets")),
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
