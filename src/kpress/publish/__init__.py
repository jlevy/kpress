"""Static publishing API for KPress."""

from __future__ import annotations

from kpress.publish.build import build_html, build_site, export_document
from kpress.publish.capability import ProbeResult, probe_capability
from kpress.publish.config import (
    BuildOptions,
    KPressConfig,
    OptimizerOptions,
    PdfPublishConfig,
    PublishConfig,
    load_config,
)
from kpress.publish.manifest import BuildReport, OutputFile
from kpress.publish.optimize import get_optimizer, optimize_text

__all__ = [
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
]
