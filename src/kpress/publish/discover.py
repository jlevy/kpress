"""Source discovery for static KPress builds."""

from __future__ import annotations

from pathlib import Path

from kpress.publish.config import KPressConfig


def discover_sources(config: KPressConfig) -> list[Path]:
    """Discover Markdown sources for a config."""

    base = (config.config_path.parent if config.config_path else Path.cwd()).resolve()
    found: list[Path] = []
    for source in config.sources:
        root = (base / source.path).resolve()
        if not root.exists():
            continue
        for pattern in source.include:
            for path in root.glob(pattern):
                if not path.is_file():
                    continue
                rel = path.relative_to(root).as_posix()
                if any(Path(rel).match(excluded) for excluded in source.exclude):
                    continue
                found.append(path)
    return sorted(set(found))


def discover_static_files(config: KPressConfig) -> list[tuple[Path, Path]]:
    """Discover verbatim-copy files for every source's ``static`` patterns.

    Returns sorted ``(file, source_root)`` pairs; the file's path relative to
    its root is its output path. The source's ``exclude`` patterns apply to
    static matches the same way they apply to Markdown discovery.
    """

    base = (config.config_path.parent if config.config_path else Path.cwd()).resolve()
    found: dict[Path, Path] = {}
    for source in config.sources:
        root = (base / source.path).resolve()
        if not root.exists():
            continue
        for pattern in source.static:
            for path in root.glob(pattern):
                if not path.is_file():
                    continue
                rel = path.relative_to(root).as_posix()
                if any(Path(rel).match(excluded) for excluded in source.exclude):
                    continue
                found.setdefault(path, root)
    return sorted(found.items())
