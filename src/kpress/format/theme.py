"""KPress theme and font configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

from kpress.models import ThemeMode


@dataclass(frozen=True)
class FontSpec:
    """CSS font-family hooks for a KPress theme."""

    body: str = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    prose: str = "Georgia, 'Times New Roman', serif"
    sans: str = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    mono: str = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    punctuation: str | None = None


@dataclass(frozen=True)
class ThemeSpec:
    """Document theme options."""

    name: str = "default"
    color_mode: ThemeMode = "system"
    fonts: FontSpec = FontSpec()


@dataclass(frozen=True)
class ResolvedTheme:
    """Theme values resolved for a concrete render."""

    mode: ThemeMode
    resolved: Literal["light", "dark"]
    fonts: FontSpec = FontSpec()


def normalize_theme_mode(value: str | None) -> ThemeMode:
    """Normalize user-facing theme values."""

    raw = (value or "system").strip().lower()
    if raw == "auto":
        raw = "system"
    if raw not in {"system", "light", "dark"}:
        msg = "theme mode must be one of: system, light, dark"
        raise ValueError(msg)
    return cast(ThemeMode, raw)
