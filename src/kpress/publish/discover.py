"""Source discovery for static KPress builds."""

from __future__ import annotations

from pathlib import Path

from kpress.errors import KPressPublishError
from kpress.publish.config import KPressConfig


def _is_excluded(relative_path: str, patterns: list[str]) -> bool:
    """Match source-relative excludes, including every descendant of ``dir/**``."""

    path = Path(relative_path)
    for pattern in patterns:
        if path.match(pattern):
            return True
        if pattern.endswith("/**"):
            prefix = pattern.removesuffix("/**").rstrip("/")
            if relative_path == prefix or relative_path.startswith(f"{prefix}/"):
                return True
    return False


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
        # base_dir is str | Path (like the sibling path fields); normalize here.
        return Path(config.base_dir).resolve()
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
                if _is_excluded(rel, source.exclude):
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
                if _is_excluded(rel, source.exclude):
                    continue
                found.setdefault(path, root)
    return sorted(found.items())
