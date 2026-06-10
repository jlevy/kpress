"""KPress cache path helpers."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kpress.output import write_text_atomic


def cache_key(*parts: object) -> str:
    """Return a stable cache key for render/build artifacts."""

    digest = hashlib.sha256()
    for part in parts:
        digest.update(str(part).encode("utf-8", errors="replace"))
        digest.update(b"\0")
    return digest.hexdigest()


def cache_dir(root: Path, bucket: str) -> Path:
    """Return and create a cache bucket."""

    path = root / ".kpress" / "cache" / bucket
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_path(root: Path, bucket: str, key: str, *, suffix: str = ".json") -> Path:
    """Return a cache path for a bucket/key pair."""

    safe_key = cache_key(bucket, key) if "/" in key or "\\" in key else key
    return cache_dir(root, bucket) / f"{safe_key}{suffix}"


def reset_cache_bucket(root: Path, bucket: str) -> Path:
    """Clear and recreate a cache bucket for explicit refetch/rerun flows."""

    path = root / ".kpress" / "cache" / bucket
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass(frozen=True)
class CacheRecord:
    """Small stable cache record used by publisher tests and workflows."""

    key: str
    kind: str
    value: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {"key": self.key, "kind": self.kind, "value": self.value}


def write_cache_record(root: Path, bucket: str, record: CacheRecord) -> Path:
    """Write a deterministic JSON cache record."""

    path = cache_path(root, bucket, record.key)
    write_text_atomic(path, json.dumps(record.as_dict(), indent=2, sort_keys=True) + "\n")
    return path


def read_cache_record(root: Path, bucket: str, key: str) -> CacheRecord | None:
    """Read a deterministic JSON cache record if present."""

    path = cache_path(root, bucket, key)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return CacheRecord(key=str(data["key"]), kind=str(data["kind"]), value=dict(data["value"]))
