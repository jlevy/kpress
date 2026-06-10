"""Route derivation and collision checking for KPress static sources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kpress.errors import KPressPublishError

# Output paths KPress owns for site infrastructure. Source documents may not
# resolve onto these names or into the package asset tree.
RESERVED_OUTPUT_FILES = ("sitemap.xml", "robots.txt", "_redirects")
RESERVED_OUTPUT_PREFIXES = ("_kpress/",)

# Characters that must never appear in a public route, even after URL
# unescaping: NUL and the rest of the C0 control range, DEL, and the
# Windows path-separator backslash. We compare against the raw `route` (any
# %-escapes the author chose to write are taken literally) — the goal is to
# stop pathological frontmatter input, not to do general URL parsing.
_FORBIDDEN_ROUTE_CHARS = frozenset(chr(c) for c in range(0x20)) | frozenset(("\x7f", "\\"))


def validate_public_route(raw: str) -> str:
    """Convert a raw frontmatter route into a safe, normalized public route.

    Rejects path traversal (`..`), current-directory components (`.`),
    backslashes, NUL/control chars, empty interior components (`/a//b`),
    absolute-looking interior segments (a route with a drive letter or a
    scheme), and any value that would resolve outside the site root. The
    result is always a forward-slash route starting with `/` and is safe to
    convert to an output-relative `Path` without further checking.

    Raises :class:`KPressPublishError` with the offending value when the
    route is unsafe. Defaults are not changed; this only fires when an
    explicit `public_path` / route override is supplied.
    """

    if not raw.strip():
        msg = f"public_path must be a non-empty string, got {raw!r}"
        raise KPressPublishError(msg)
    route = raw.strip()
    bad_chars = sorted({c for c in route if c in _FORBIDDEN_ROUTE_CHARS})
    if bad_chars:
        msg = f"public_path {raw!r} contains forbidden characters {bad_chars!r}"
        raise KPressPublishError(msg)
    # Reject scheme-prefixed values like `http://...` or drive letters like
    # `C:/foo` outright. A site route is filesystem-relative inside the
    # output_dir; anything else is an authoring error or an attack.
    if "://" in route or (len(route) >= 2 and route[1] == ":"):
        msg = f"public_path {raw!r} is not a site-root-relative route"
        raise KPressPublishError(msg)
    if not route.startswith("/"):
        route = "/" + route
    trailing_slash = route.endswith("/") and route != "/"
    segments = route.strip("/").split("/") if route.strip("/") else []
    for segment in segments:
        if segment == "":
            msg = f"public_path {raw!r} has an empty interior component"
            raise KPressPublishError(msg)
        if segment in {".", ".."}:
            msg = f"public_path {raw!r} contains a path-traversal component {segment!r}"
            raise KPressPublishError(msg)
    cleaned = "/" + "/".join(segments) + ("/" if trailing_slash else "")
    if not segments:
        cleaned = "/"
    return normalize_route(cleaned)


def validate_public_slug(raw: str) -> str | None:
    """Sanitize a frontmatter ``public_slug`` value or return ``None`` to skip.

    Slug semantics intentionally differ from a public route: a slug is a
    single leaf segment, not a path. Embedded ``/``, ``.``, and ``..`` are
    treated as ``"not a slug"`` and the caller falls back to the path-derived
    route. Control characters, ``\\x7f``, and ``\\\\`` are rejected hard via
    :class:`KPressPublishError` — those would silently land on the filesystem
    in slug-built output paths.
    """

    if not raw.strip():
        return None
    slug = raw.strip().strip("/")
    if not slug or "/" in slug or slug in {".", ".."}:
        return None
    bad_chars = sorted({c for c in slug if c in _FORBIDDEN_ROUTE_CHARS})
    if bad_chars:
        msg = f"public_slug {raw!r} contains forbidden characters {bad_chars!r}"
        raise KPressPublishError(msg)
    return slug


def normalize_route(route: str) -> str:
    """Return the canonical, case-normalized form of a route."""

    if not route.startswith("/"):
        route = "/" + route
    return route.lower()


def route_for_source(path: Path, *, root: Path) -> str:
    """Return a stable, case-normalized public route for a source path."""

    rel = path.relative_to(root)
    if rel.name == "index.md":
        out = rel.with_suffix("")
    else:
        out = rel.with_suffix(".html")
    route = "/" + out.as_posix()
    if route.endswith("/index"):
        route = route[: -len("index")]
    return normalize_route(route)


def output_path_for_route(output_dir: Path, route: str) -> Path:
    """Return the output file path for a route."""

    if route.endswith("/"):
        clean_dir = route.strip("/")
        return output_dir / clean_dir / "index.html" if clean_dir else output_dir / "index.html"
    clean = route.strip("/")
    if not clean:
        return output_dir / "index.html"
    return output_dir / clean


def _relative_output_path(route: str) -> Path:
    if route.endswith("/"):
        clean_dir = route.strip("/")
        return Path(clean_dir) / "index.html" if clean_dir else Path("index.html")
    clean = route.strip("/")
    return Path(clean) if clean else Path("index.html")


def reserved_output_reason(rel_output: str) -> str | None:
    if rel_output in RESERVED_OUTPUT_FILES:
        return f"matches a reserved site file ({rel_output})"
    for prefix in RESERVED_OUTPUT_PREFIXES:
        if rel_output == prefix.rstrip("/") or rel_output.startswith(prefix):
            return f"falls inside the reserved {prefix} asset tree"
    return None


@dataclass(frozen=True)
class RoutePlanEntry:
    """One resolved source document and its sealed output location."""

    source: Path
    route: str
    output_path: Path


def plan_site_routes(
    sources: list[tuple[Path, Path]],
    output_dir: Path,
    *,
    overrides: dict[Path, str] | None = None,
) -> list[RoutePlanEntry]:
    """Resolve every source to a unique, non-reserved route.

    ``sources`` is a list of ``(source_path, source_root)`` pairs. ``overrides``
    maps a source path to a frontmatter-driven route (``public_path`` /
    ``public_slug``) that replaces the path-derived route while keeping the same
    collision and reserved-path guarantees. Raises :class:`KPressPublishError`
    with an actionable message on case-insensitive route collisions or
    reserved-path conflicts.
    """

    overrides = overrides or {}
    by_route: dict[str, RoutePlanEntry] = {}
    plan: list[RoutePlanEntry] = []
    for source, root in sources:
        override = overrides.get(source)
        route = (
            normalize_route(override)
            if override is not None
            else route_for_source(source, root=root.resolve())
        )
        rel_output = _relative_output_path(route).as_posix()
        reason = reserved_output_reason(rel_output)
        if reason is not None:
            msg = f"Source {source} resolves to route {route} which {reason}"
            raise KPressPublishError(msg)
        existing = by_route.get(route)
        if existing is not None:
            msg = (
                f"Route collision on {route}: {existing.source} and {source} "
                f"resolve to the same case-normalized route"
            )
            raise KPressPublishError(msg)
        entry = RoutePlanEntry(source=source, route=route, output_path=_relative_output_path(route))
        by_route[route] = entry
        plan.append(entry)
    return plan
