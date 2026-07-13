"""Optional static optimization stage."""

from __future__ import annotations

import fcntl
import gzip
import importlib
import os
import shutil
import subprocess
from dataclasses import dataclass
from hashlib import sha256
from importlib import resources
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
_NPM_INSTALL_TIMEOUT_SECONDS = 120
_OPTIMIZER_RUN_TIMEOUT_SECONDS = 60
_NPM_MIN_RELEASE_AGE_DAYS = "14"
"""npm 11.10+ minimum-release-age value, expressed in days."""

MISSING_FULL_OPTIMIZER_MESSAGE = (
    f"The KPress full optimizer requires Node.js with npm on PATH and "
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
    env.pop("NPM_CONFIG_MINIMUM_RELEASE_AGE", None)
    # npm 11.10+ interprets this value in days. It is defense in depth only:
    # integrity pins in the reviewed lock are the effective gate for `npm ci`.
    env["NPM_CONFIG_MIN_RELEASE_AGE"] = _NPM_MIN_RELEASE_AGE_DAYS
    env["NPM_CONFIG_SAVE_EXACT"] = "true"
    env["NPM_CONFIG_PACKAGE_LOCK"] = "true"
    return env


def _optimizer_tool_text(name: str) -> str:
    """Read one reviewed optimizer-tool manifest shipped in the wheel."""

    return (
        resources.files("kpress.publish")
        .joinpath("optimizer_tool", name)
        .read_text(encoding="utf-8")
    )


def _cache_bin(cache_dir: Path) -> Path:
    return cache_dir / "node_modules" / ".bin" / FULL_OPTIMIZER_PACKAGE


def _optimizer_lock_digest() -> str:
    return sha256(_optimizer_tool_text("package-lock.json").encode("utf-8")).hexdigest()


def _cache_matches_shipped_lock(cache_dir: Path) -> bool:
    marker = cache_dir / ".kpress-lock-sha256"
    try:
        recorded = marker.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    return _cache_bin(cache_dir).exists() and recorded == _optimizer_lock_digest()


def optimizer_cache_ready(cache_root: Path | None = None) -> bool:
    """Return whether Node and a cache matching the shipped lock are ready."""

    root = cache_root or _default_cache_root()
    return shutil.which("node") is not None and _cache_matches_shipped_lock(
        root / _FULL_OPTIMIZER_SPEC
    )


def ensure_tool_cache(cache_root: Path | None = None, *, allow_network: bool = False) -> Path:
    """Ensure the locked npm tool cache is installed and return its path.

    Copies the package-owned, reviewed ``package.json`` and ``package-lock.json``
    into the cache and installs only via ``npm ci``. A cold cache requires explicit
    network permission. Installation is file-locked so concurrent callers cannot
    corrupt ``node_modules``.
    """

    root = cache_root or _default_cache_root()
    cache_dir = root / _FULL_OPTIMIZER_SPEC
    if shutil.which("node") is None:
        raise KPressMissingOptionalDependencyError(MISSING_FULL_OPTIMIZER_MESSAGE)
    if _cache_matches_shipped_lock(cache_dir):
        return cache_dir
    if not allow_network:
        raise KPressMissingOptionalDependencyError(
            "The KPress full optimizer cache is cold. Run `kpress doctor --profile "
            "optimize --allow-network` once, or select optimizer 'none'."
        )
    npm = shutil.which("npm")
    if npm is None:
        raise KPressMissingOptionalDependencyError(MISSING_FULL_OPTIMIZER_MESSAGE)

    cache_dir.mkdir(parents=True, exist_ok=True)
    write_text_atomic(cache_dir / "package.json", _optimizer_tool_text("package.json"))
    write_text_atomic(cache_dir / "package-lock.json", _optimizer_tool_text("package-lock.json"))

    lock_file = cache_dir / ".install.lock"
    # `with` guarantees the lock_fd closes even if flock raises (interrupted
    # system call, lock-table exhaustion). Inner try/finally then unlocks
    # whether the install succeeded or raised.
    with lock_file.open("w") as lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            if _cache_matches_shipped_lock(cache_dir):
                return cache_dir

            try:
                result = subprocess.run(
                    [npm, "ci", "--ignore-scripts"],
                    cwd=cache_dir,
                    env=_npm_env(),
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=_NPM_INSTALL_TIMEOUT_SECONDS,
                )
            except FileNotFoundError as exc:
                raise KPressMissingOptionalDependencyError(MISSING_FULL_OPTIMIZER_MESSAGE) from exc
            except subprocess.TimeoutExpired as exc:
                raise KPressOptimizerError(
                    f"npm ci for {_FULL_OPTIMIZER_SPEC} timed out after "
                    f"{_NPM_INSTALL_TIMEOUT_SECONDS} seconds."
                ) from exc
            if result.returncode != 0:
                stderr = result.stderr.strip()
                raise KPressOptimizerError(
                    f"npm ci for {_FULL_OPTIMIZER_SPEC} failed (exit {result.returncode}): {stderr}"
                )
            if not _cache_bin(cache_dir).exists():
                raise KPressOptimizerError(
                    f"npm ci for {_FULL_OPTIMIZER_SPEC} succeeded but did not install "
                    f"the {FULL_OPTIMIZER_PACKAGE} executable."
                )
            write_text_atomic(cache_dir / ".kpress-lock-sha256", _optimizer_lock_digest() + "\n")
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)

    return cache_dir


def full_optimizer_available() -> bool:
    """Return whether Node and npm can bootstrap the optional full optimizer."""

    return shutil.which("node") is not None and shutil.which("npm") is not None


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
            cmd,
            input=payload,
            capture_output=True,
            text=True,
            check=False,
            timeout=_OPTIMIZER_RUN_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise KPressMissingOptionalDependencyError(MISSING_FULL_OPTIMIZER_MESSAGE) from exc
    except subprocess.TimeoutExpired as exc:
        raise KPressOptimizerError(
            f"{FULL_OPTIMIZER_PACKAGE} timed out after {_OPTIMIZER_RUN_TIMEOUT_SECONDS} seconds."
        ) from exc
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
    no project ``package.json``. If the Node/npm toolchain or the
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
            self._cache_dir = ensure_tool_cache(
                cache_root=self._cache_root,
                allow_network=False,
            )
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


# Built-in pipeline stage names a host may reference in BuildExtensions.pipeline
# (pinned by contract.PUBLIC_PIPELINE_STAGES).
BUILTIN_PIPELINE_STAGES = ("none", "full")


def resolve_stage(stage: OptimizerBackend | str) -> OptimizerBackend:
    """Resolve one build-pipeline stage: a built-in name or a stage object.

    Stage objects share the optimizer-backend shape (``name`` +
    ``optimize(content, *, kind) -> OptimizerResult``). An unknown name is an
    error, never a silent skip — same strictness as optimizer.mode.
    """

    if not isinstance(stage, str):
        return stage
    if stage == "none":
        return NoneOptimizer()
    if stage == "full":
        return FullOptimizer()
    from kpress.errors import KPressPublishError

    msg = (
        f"Unknown pipeline stage {stage!r}; built-in stages are "
        f"{', '.join(repr(name) for name in BUILTIN_PIPELINE_STAGES)} "
        f"(or pass a stage object)"
    )
    raise KPressPublishError(msg)


def optimize_file(
    path: Path, *, kind: ContentKind | str, backend: str | None = "none"
) -> OutputFile:
    """Optimize one file in place and return its output-file record."""

    content = path.read_text(encoding="utf-8")
    original_size = len(content.encode("utf-8"))
    resolved_backend = backend or "none"
    normalized = cast(ContentKind, kind if kind in {"html", "css", "js"} else "other")
    result = get_optimizer(resolved_backend).optimize(content, kind=normalized)
    write_text_atomic(path, result.content)
    return OutputFile(
        path=path.name,
        kind=path.suffix.lstrip("."),
        content_hash=content_hash(result.content),
        size=len(result.content.encode("utf-8")),
        original_size=original_size,
        applied_pipeline=[resolved_backend] if result.changed else [],
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
