"""Optional static optimization stage."""

from __future__ import annotations

import fcntl
import gzip
import importlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, cast

from kpress.errors import KPressMissingOptionalDependencyError, KPressOptimizerError
from kpress.format.assets import content_hash
from kpress.output import write_bytes_atomic, write_text_atomic
from kpress.publish.manifest import OutputFile

ContentKind = Literal["html", "css", "js", "other"]


@dataclass(frozen=True)
class OptimizerResult:
    """Result returned by an optimizer backend."""

    content: str
    backend: str
    changed: bool


class OptimizerBackend(Protocol):
    """Protocol implemented by static optimizer backends."""

    name: str

    def optimize(self, content: str, *, kind: ContentKind) -> OptimizerResult:
        """Optimize content and return a stable result."""
        raise NotImplementedError


class NoneOptimizer:
    """Zero-optimizer mode: content is published unchanged.

    This is the default. It requires no Node toolchain; production builds
    still gain wire savings from gzip/Brotli precompression.
    """

    name: str = "none"

    def optimize(self, content: str, *, kind: ContentKind) -> OptimizerResult:
        _ = kind
        return OptimizerResult(content=content, backend=self.name, changed=False)


FULL_OPTIMIZER_PACKAGE = "html-minifier-next"
"""The npm package used by the ``full`` optimizer backend."""

FULL_OPTIMIZER_VERSION = "6.2.3"
"""The pinned version of the ``full`` optimizer npm package."""

_FULL_OPTIMIZER_SPEC = f"{FULL_OPTIMIZER_PACKAGE}@{FULL_OPTIMIZER_VERSION}"

MISSING_FULL_OPTIMIZER_MESSAGE = (
    f"The KPress full optimizer requires Node.js with npm and npx on PATH and "
    f"{FULL_OPTIMIZER_PACKAGE}. Install Node.js (the package is installed into a "
    f"managed cache via npm ci, no project setup needed), or select optimizer 'none'."
)

_FULL_HTML_FLAGS = [
    "--collapse-whitespace",
    "--remove-comments",
    "--remove-redundant-attributes",
    "--remove-empty-attributes",
    "--minify-css",
    "true",
    "--minify-js",
    "true",
    "--collapse-boolean-attributes",
    "--sort-attributes",
    "--sort-class-names",
]


def _default_cache_root() -> Path:
    """Return the default cache root for KPress npm tool caches.

    Uses ``$XDG_CACHE_HOME/kpress/npm`` if set, otherwise ``~/.cache/kpress/npm``.
    """

    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "kpress" / "npm"


def _npm_env() -> dict[str, str]:
    """Return an environment dict carrying the repo npm age-gate settings.

    Mirrors ``scripts/package_policy.py::npm_env()`` so the managed cache
    install respects the same minimum-release-age and lockfile policy without
    importing the devtools path at runtime.
    """

    env = os.environ.copy()
    env["NPM_CONFIG_MINIMUM_RELEASE_AGE"] = "20160"
    env["NPM_CONFIG_SAVE_EXACT"] = "true"
    env["NPM_CONFIG_PACKAGE_LOCK"] = "true"
    return env


_CACHE_PACKAGE_JSON = json.dumps(
    {
        "name": "kpress-optimizer-cache",
        "version": "0.0.0",
        "private": True,
        "dependencies": {
            FULL_OPTIMIZER_PACKAGE: FULL_OPTIMIZER_VERSION,
        },
    },
    indent=2,
    sort_keys=True,
)


def ensure_tool_cache(cache_root: Path | None = None) -> Path:
    """Ensure the locked npm tool cache is installed and return its path.

    Creates a package-owned directory with a pinned ``package.json``, then
    installs via ``npm ci`` (when a lockfile from a prior install exists)
    or ``npm install --ignore-scripts`` (first-time bootstrap) under a file
    lock so concurrent callers do not corrupt the ``node_modules`` tree.
    """

    root = cache_root or _default_cache_root()
    cache_dir = root / _FULL_OPTIMIZER_SPEC
    cache_dir.mkdir(parents=True, exist_ok=True)

    pkg_json = cache_dir / "package.json"
    lock_json = cache_dir / "package-lock.json"

    write_text_atomic(pkg_json, _CACHE_PACKAGE_JSON)

    bin_path = cache_dir / "node_modules" / ".bin" / FULL_OPTIMIZER_PACKAGE
    if bin_path.exists():
        return cache_dir

    lock_file = cache_dir / ".install.lock"
    # `with` guarantees the lock_fd closes even if flock raises (interrupted
    # system call, lock-table exhaustion). Inner try/finally then unlocks
    # whether the install succeeded or raised.
    with lock_file.open("w") as lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            if bin_path.exists():
                return cache_dir

            npm = shutil.which("npm")
            if npm is None:
                raise KPressMissingOptionalDependencyError(MISSING_FULL_OPTIMIZER_MESSAGE)

            if lock_json.exists():
                install_cmd = [npm, "ci", "--ignore-scripts"]
            else:
                install_cmd = [npm, "install", "--ignore-scripts"]

            result = subprocess.run(
                install_cmd,
                cwd=cache_dir,
                env=_npm_env(),
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                raise KPressOptimizerError(
                    f"npm install for {_FULL_OPTIMIZER_SPEC} failed "
                    f"(exit {result.returncode}): {stderr}"
                )
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)

    return cache_dir


def full_optimizer_available() -> bool:
    """Return whether the optional `full` optimizer toolchain (npx) is present."""

    return shutil.which("npx") is not None


def _run_full_optimizer(
    content: str,
    *,
    extra_flags: list[str],
    wrap: str | None,
    cache_dir: Path,
) -> str:
    """Run html-minifier-next from the locked cache. Any failure is a hard error.

    The binary is resolved from the cache's ``node_modules/.bin/`` tree.
    The full optimizer never silently returns the input: if it is selected it
    must actually run, otherwise the caller gets an explicit error.
    """

    payload = f"<{wrap}>{content}</{wrap}>" if wrap else content
    bin_path = cache_dir / "node_modules" / ".bin" / FULL_OPTIMIZER_PACKAGE
    cmd = [str(bin_path), *extra_flags]

    try:
        result = subprocess.run(
            cmd, input=payload, capture_output=True, text=True, check=False, timeout=60
        )
    except FileNotFoundError as exc:
        raise KPressMissingOptionalDependencyError(MISSING_FULL_OPTIMIZER_MESSAGE) from exc
    except subprocess.TimeoutExpired as exc:
        raise KPressOptimizerError(f"{FULL_OPTIMIZER_PACKAGE} timed out after 60 seconds.") from exc
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise KPressOptimizerError(
            f"{FULL_OPTIMIZER_PACKAGE} exited with code {result.returncode}: {stderr}"
        )
    output = strip_exact_wrapper(result.stdout.strip(), wrap)
    return output.strip() + "\n"


def strip_exact_wrapper(output: str, wrap: str | None) -> str:
    """Strip the exact ``<wrap>``/``</wrap>`` envelope added around a CSS/JS payload.

    The minifier must return the wrapper byte-for-byte; if it ever rewrote the
    tag (attributes, case), slicing would silently corrupt the payload, so a
    missing exact wrapper is a hard error instead.
    """

    if not wrap:
        return output
    prefix, suffix = f"<{wrap}>", f"</{wrap}>"
    if not (output.startswith(prefix) and output.endswith(suffix)):
        raise KPressOptimizerError(
            f"{FULL_OPTIMIZER_PACKAGE} returned output without the exact <{wrap}> wrapper."
        )
    return output.removeprefix(prefix).removesuffix(suffix)


class FullOptimizer:
    """Full optimizer: html-minifier-next (HTML) plus its clean-css and terser
    engines for CSS and JavaScript.

    The package is installed deterministically into a managed, file-locked
    cache directory via ``npm ci`` with a pinned lockfile. Callers maintain
    no project ``package.json``. If the Node toolchain (npm/npx) or the
    package is unavailable, optimization raises
    ``KPressMissingOptionalDependencyError``. There is no silent fallback.
    Dynamic rendering never imports or calls this optimizer.
    """

    name: str = "full"

    def __init__(self, *, cache_root: Path | None = None) -> None:
        self._cache_root = cache_root
        self._cache_dir: Path | None = None

    def _get_cache_dir(self) -> Path:
        if self._cache_dir is None:
            if not full_optimizer_available():
                raise KPressMissingOptionalDependencyError(MISSING_FULL_OPTIMIZER_MESSAGE)
            self._cache_dir = ensure_tool_cache(cache_root=self._cache_root)
        return self._cache_dir

    def optimize(self, content: str, *, kind: ContentKind) -> OptimizerResult:
        if kind not in {"html", "css", "js"}:
            return OptimizerResult(content=content, backend=self.name, changed=False)
        cache_dir = self._get_cache_dir()
        if kind == "html":
            optimized = _run_full_optimizer(
                content, extra_flags=_FULL_HTML_FLAGS, wrap=None, cache_dir=cache_dir
            )
        elif kind == "css":
            optimized = _run_full_optimizer(
                content,
                extra_flags=["--collapse-whitespace", "--minify-css", "true"],
                wrap="style",
                cache_dir=cache_dir,
            )
        else:
            optimized = _run_full_optimizer(
                content,
                extra_flags=["--collapse-whitespace", "--minify-js", "true"],
                wrap="script",
                cache_dir=cache_dir,
            )
        return OptimizerResult(content=optimized, backend=self.name, changed=optimized != content)


OPTIMIZER_MODES = ("none", "full")


def get_optimizer(name: str | None = None) -> OptimizerBackend:
    """Return the optimizer for a mode: ``none`` or ``full``.

    There is no implicit fallback. An unknown mode is an error, and the
    ``full`` optimizer raises if its optional Node toolchain is unavailable.
    """

    mode = name or "none"
    if mode == "none":
        return NoneOptimizer()
    if mode == "full":
        return FullOptimizer()
    raise KPressOptimizerError(
        f"Unknown KPress optimizer mode {mode!r}; expected one of {OPTIMIZER_MODES}."
    )


def optimize_text(content: str, *, kind: ContentKind | str, backend: str | None = "none") -> str:
    """Optimize HTML/CSS/JS text with the selected optimizer mode."""

    normalized = cast(ContentKind, kind if kind in {"html", "css", "js"} else "other")
    return get_optimizer(backend).optimize(content, kind=normalized).content


def optimize_file(
    path: Path, *, kind: ContentKind | str, backend: str | None = "none"
) -> OutputFile:
    """Optimize one file in place and return its output-file record."""

    content = path.read_text(encoding="utf-8")
    original_size = len(content.encode("utf-8"))
    resolved_backend = backend or "none"
    optimized = optimize_text(content, kind=kind, backend=resolved_backend)
    write_text_atomic(path, optimized)
    return OutputFile(
        path=path.name,
        kind=path.suffix.lstrip("."),
        content_hash=content_hash(optimized),
        size=len(optimized.encode("utf-8")),
        original_size=original_size,
        optimizer_backend=resolved_backend,
    )


def _deterministic_gzip(data: bytes) -> bytes:
    """Gzip with a normalized OS byte so output is byte-identical across zlib
    builds. Different Python distributions stamp different `OS` values in the
    gzip header (RFC 1952 §2.3.1 byte 9) — system zlib on Linux writes `03`,
    python-build-standalone writes `ff`, etc. Normalize to `ff` (Unknown) so
    sha256 of `.gz` outputs is reproducible across CI and developer machines.
    """

    raw = gzip.compress(data, compresslevel=9, mtime=0)
    return raw[:9] + b"\xff" + raw[10:]


def precompress_file(path: Path, *, methods: list[str]) -> list[OutputFile]:
    """Write deterministic precompressed variants for one file."""

    data = path.read_bytes()
    source_name = path.name
    outputs: list[OutputFile] = []
    for method in methods:
        if method == "gzip":
            compressed = _deterministic_gzip(data)
            destination = path.with_name(f"{path.name}.gz")
        elif method == "br":
            try:
                brotli = importlib.import_module("brotli")
            except ModuleNotFoundError as exc:
                raise KPressMissingOptionalDependencyError(
                    "Brotli precompression requires the kpress[optimize] optional extra."
                ) from exc
            compressed = cast(bytes, brotli.compress(data))
            destination = path.with_name(f"{path.name}.br")
        else:
            raise KPressOptimizerError(f"Unsupported precompression method: {method}")
        write_bytes_atomic(destination, compressed)
        outputs.append(
            OutputFile(
                path=destination.name,
                kind=destination.suffix.lstrip("."),
                content_hash=content_hash(compressed),
                size=len(compressed),
                compression=method,
                source_path=source_name,
            )
        )
    return outputs
