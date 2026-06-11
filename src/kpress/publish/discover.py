"""Source discovery for static KPress builds."""

from __future__ import annotations

from pathlib import Path

from kpress.errors import KPressPublishError
from kpress.publish.config import KPressConfig


def config_base_dir(config: KPressConfig) -> Path:
    """The one path anchor for relative sources/output and the asset boundary.

    File-loaded configs anchor on the config file's directory; programmatic
    configs supply ``base_dir``. Setting both is rejected (mutual exclusion,
    like the chrome-slot ``*_file`` variants): a split anchor would discover
    sources against one tree while bounding assets against another.
    """

    if config.base_dir is not None:
        if config.config_path is not None:
            msg = (
                "KPressConfig.config_path and KPressConfig.base_dir are mutually "
                "exclusive path anchors; set one (file-loaded configs anchor on "
                "the config file's directory)"
            )
            raise KPressPublishError(msg)
        return config.base_dir.resolve()
    return (config.config_path.parent if config.config_path else Path.cwd()).resolve()


def discover_sources(config: KPressConfig) -> list[Path]:
    """Discover Markdown sources for a config."""

    base = config_base_dir(config)
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

    base = config_base_dir(config)
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
