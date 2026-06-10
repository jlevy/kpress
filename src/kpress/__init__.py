"""KPress document rendering and publishing package."""

from __future__ import annotations

from kpress._version import __version__  # noqa: E402
from kpress.contract import (  # noqa: E402
    ASSET_MANIFEST_SCHEMA_VERSION,
    BUILD_MANIFEST_SCHEMA_VERSION,
    CONTRACT_VERSION,
)
from kpress.errors import (  # noqa: E402
    KPressAssetNotFoundError,
    KPressInvalidRequestError,
    KPressMissingOptionalDependencyError,
    KPressOptimizerError,
    KPressPublishError,
    KPressRenderError,
)
from kpress.models import (  # noqa: E402
    KPressAsset,
    KPressExportRequest,
    KPressRenderRequest,
    PrintProfile,
    ThemeMode,
)
from kpress.runtime import (  # noqa: E402
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
