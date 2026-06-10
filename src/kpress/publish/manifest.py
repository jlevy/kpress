"""Build manifest models."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from kpress.contract import BUILD_MANIFEST_SCHEMA_VERSION
from kpress.output import write_text_atomic


@dataclass(frozen=True)
class OutputFile:
    """One file written by a KPress build."""

    path: str
    kind: str
    content_hash: str | None = None
    size: int | None = None
    original_size: int | None = None
    optimizer_backend: str | None = None
    compression: str | None = None
    source_path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"path": self.path, "kind": self.kind}
        if self.content_hash:
            out["content_hash"] = self.content_hash
        if self.size is not None:
            out["size"] = self.size
        if self.original_size is not None:
            out["original_size"] = self.original_size
        if self.optimizer_backend is not None:
            out["optimizer_backend"] = self.optimizer_backend
        if self.compression is not None:
            out["compression"] = self.compression
        if self.source_path is not None:
            out["source_path"] = self.source_path
        return out


@dataclass(frozen=True)
class ManifestAsset:
    """One asset copied, sealed, or generated during a KPress build."""

    path: str
    kind: str
    source: str
    output_path: str
    content_hash: str
    media_type: str | None = None
    sealed: bool = True

    def _public_path(self) -> str:
        if self.kind != "external-url":
            return self.path
        return f"external-asset:{_stable_identifier(self.path)}"

    def _public_source(self) -> str:
        if self.kind != "external-url":
            return self.source
        return f"external-asset:{_stable_identifier(self.source)}"

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "content_hash": self.content_hash,
            "kind": self.kind,
            "output_path": self.output_path,
            "path": self._public_path(),
            "sealed": self.sealed,
            "source": self._public_source(),
        }
        if self.media_type:
            out["media_type"] = self.media_type
        return out


def _stable_identifier(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


_REMOTE_URL_PATTERN = re.compile(r"https?://\S+")


def _redact_remote_urls(value: str) -> str:
    """Replace remote URLs with stable identifiers for safe manifest output."""
    return _REMOTE_URL_PATTERN.sub(
        lambda m: f"external-asset:{_stable_identifier(m.group(0))}", value
    )


def redact_diagnostic(diag: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of a diagnostic dict with remote URLs redacted."""
    redacted: dict[str, Any] = {}
    for key, val in diag.items():
        if isinstance(val, str) and _REMOTE_URL_PATTERN.search(val):
            redacted[key] = _redact_remote_urls(val)
        else:
            redacted[key] = val
    return redacted


@dataclass(frozen=True)
class BuildReport:
    """Static build report returned by publisher APIs."""

    output_dir: Path
    files: list[OutputFile] = field(default_factory=list)
    assets: list[ManifestAsset] = field(default_factory=list)
    routes: dict[str, str] = field(default_factory=dict)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    optimizer_backend: str | None = None
    precompress: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "schema_version": BUILD_MANIFEST_SCHEMA_VERSION,
            "output_dir": str(self.output_dir),
            "files": [file.as_dict() for file in sorted(self.files, key=lambda item: item.path)],
            "assets": [
                asset.as_dict() for asset in sorted(self.assets, key=lambda item: item.output_path)
            ],
            "routes": dict(sorted(self.routes.items())),
            "diagnostics": [redact_diagnostic(d) for d in self.diagnostics],
        }
        if self.optimizer_backend is not None:
            out["optimizer_backend"] = self.optimizer_backend
        if self.precompress:
            out["precompress"] = list(self.precompress)
        return out

    def write_manifest(self) -> Path:
        path = self.output_dir / "_kpress" / "kpress-manifest.json"
        write_text_atomic(path, json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n")
        return path
