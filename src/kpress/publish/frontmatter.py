"""Shared document frontmatter/sidematter contract for KPress publishing.

KPress reads document metadata through the ``frontmatter-format`` library
rather than a KPress-specific parser. Every source may carry in-document YAML
frontmatter and, optionally, an adjacent sidematter file ``<stem>.meta.yml``
(or ``.meta.yaml``). The merged metadata drives routing (``public_path`` /
``public_slug`` overrides), rendering, and the build manifest from one place.

Precedence: in-document frontmatter wins over sidematter. Frontmatter travels
with the content, so it is the authoritative source; sidematter supplies
defaults that an author can override inline without editing the sidecar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from frontmatter_format import fmf_read, read_yaml_file

from kpress.publish.routes import (
    normalize_route,
    validate_public_route,
    validate_public_slug,
)

_SIDEMATTER_SUFFIXES = (".meta.yml", ".meta.yaml")


@dataclass(frozen=True)
class DocumentSource:
    """A discovered source with its body and merged metadata.

    ``body`` is the document content with any in-document frontmatter removed.
    ``metadata`` is sidematter merged under frontmatter (frontmatter wins).
    """

    path: Path
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)
    frontmatter: dict[str, Any] = field(default_factory=dict)
    sidematter: dict[str, Any] = field(default_factory=dict)


def _as_str_keyed(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    items = cast("dict[Any, Any]", value).items()
    return {str(key): item for key, item in items}


def _sidematter_for(path: Path) -> dict[str, Any]:
    for suffix in _SIDEMATTER_SUFFIXES:
        sidecar = path.with_name(path.stem + suffix)
        if sidecar.is_file():
            return _as_str_keyed(read_yaml_file(sidecar))
    return {}


def read_document_source(path: Path) -> DocumentSource:
    """Read a source file's body and merged frontmatter/sidematter metadata."""

    body, frontmatter = fmf_read(path)
    fm = _as_str_keyed(frontmatter)
    sidematter = _sidematter_for(path)
    metadata = {**sidematter, **fm}
    return DocumentSource(
        path=path,
        body=body,
        metadata=metadata,
        frontmatter=fm,
        sidematter=sidematter,
    )


def route_override(metadata: dict[str, Any], *, base_route: str) -> str | None:
    """Return a frontmatter-driven route override, or ``None``.

    ``public_path`` is an explicit site-absolute route and takes precedence
    over ``public_slug``, which replaces the leaf segment of the derived
    route. Both are case-normalized like every other route.
    """

    public_path = metadata.get("public_path")
    if isinstance(public_path, str) and public_path.strip():
        # validate_public_route raises KPressPublishError on traversal, control
        # chars, scheme-prefixed values, empty interior components, or `.` /
        # `..` segments — see `routes.validate_public_route`.
        return validate_public_route(public_path)

    public_slug = metadata.get("public_slug")
    if isinstance(public_slug, str):
        slug = validate_public_slug(public_slug)
        if slug is None:
            return None
        trailing_slash = base_route.endswith("/") and base_route != "/"
        segments = [segment for segment in base_route.strip("/").split("/") if segment]
        if not segments:
            return normalize_route(f"/{slug}.html")
        if segments[-1].endswith(".html"):
            segments[-1] = f"{slug}.html"
        else:
            segments[-1] = slug
        route = "/" + "/".join(segments) + ("/" if trailing_slash else "")
        return normalize_route(route)

    return None
