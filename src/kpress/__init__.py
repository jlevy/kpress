"""KPress document rendering and publishing package."""

from __future__ import annotations

from kpress._version import __version__
from kpress.contract import (
    ASSET_MANIFEST_SCHEMA_VERSION,
    BUILD_MANIFEST_SCHEMA_VERSION,
    CONTRACT_VERSION,
)
from kpress.errors import (
    KPressAssetNotFoundError,
    KPressInvalidRequestError,
    KPressMissingOptionalDependencyError,
    KPressOptimizerError,
    KPressPublishError,
    KPressRenderError,
)
from kpress.models import (
    KPressAsset,
    KPressExportRequest,
    KPressRenderRequest,
    PrintProfile,
    ThemeMode,
)
from kpress.runtime import (
    clear_render_cache,
    export_document,
    get_static_asset,
    render_view,
    set_static_root_for_tests,
)

__all__ = [
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
]
