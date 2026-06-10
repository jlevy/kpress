"""KPress public exception types."""

from __future__ import annotations


class KPressRenderError(RuntimeError):
    """Raised when KPress cannot render the requested input."""


class KPressInvalidRequestError(ValueError):
    """Raised when a KPress request is malformed (e.g. unknown print profile)."""


class KPressAssetNotFoundError(FileNotFoundError):
    """Raised when a KPress package asset path is missing or unsafe."""


class KPressPublishError(RuntimeError):
    """Raised when static publishing cannot complete safely."""


class KPressMissingOptionalDependencyError(KPressPublishError):
    """Raised when an optional publishing backend is requested but unavailable."""


class KPressOptimizerError(KPressPublishError):
    """Raised when an optimizer backend fails."""
