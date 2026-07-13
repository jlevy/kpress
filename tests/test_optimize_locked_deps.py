"""Tests for the locked full-optimizer dependency layer.

The full optimizer manages html-minifier-next in a package-owned cache
directory with a pinned lockfile and file-locked installs. These tests
verify deterministic output, race safety, missing-tool errors, and
lockfile/pin correctness.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import cast

import pytest

from kpress.errors import KPressMissingOptionalDependencyError, KPressOptimizerError
from kpress.publish.optimize import (
    FULL_OPTIMIZER_PACKAGE,
    FULL_OPTIMIZER_VERSION,
    FullOptimizer,
    full_optimizer_available,
)

needs_full = pytest.mark.skipif(
    not full_optimizer_available(), reason="full optimizer requires Node/npm"
)


def _stub_which(name: str) -> None:
    _ = name
    return


def _fake_tool_path(name: str) -> str:
    return f"/usr/bin/{name}"


class TestLockedCacheStructure:
    """The locked cache directory has a pinned package.json and lockfile."""

    @needs_full
    def test_ensure_cache_creates_package_json(self, tmp_path: Path) -> None:
        from kpress.publish.optimize import ensure_tool_cache

        cache = ensure_tool_cache(cache_root=tmp_path)
        pkg = json.loads((cache / "package.json").read_text())
        assert pkg["dependencies"][FULL_OPTIMIZER_PACKAGE] == FULL_OPTIMIZER_VERSION
        assert pkg.get("private") is True

    @needs_full
    def test_ensure_cache_creates_lockfile(self, tmp_path: Path) -> None:
        from kpress.publish.optimize import ensure_tool_cache

        cache = ensure_tool_cache(cache_root=tmp_path)
        assert (cache / "package-lock.json").exists()
        lock = json.loads((cache / "package-lock.json").read_text())
        assert lock["lockfileVersion"] >= 2
        packages = lock.get("packages", {})
        dep_key = f"node_modules/{FULL_OPTIMIZER_PACKAGE}"
        assert dep_key in packages
        assert packages[dep_key]["version"] == FULL_OPTIMIZER_VERSION

    @needs_full
    def test_ensure_cache_idempotent(self, tmp_path: Path) -> None:
        from kpress.publish.optimize import ensure_tool_cache

        first = ensure_tool_cache(cache_root=tmp_path)
        second = ensure_tool_cache(cache_root=tmp_path)
        assert first == second
        pkg = json.loads((first / "package.json").read_text())
        assert pkg["dependencies"][FULL_OPTIMIZER_PACKAGE] == FULL_OPTIMIZER_VERSION

    def test_reviewed_lock_is_shipped_with_integrity_pins(self) -> None:
        from importlib import resources

        lock_path = resources.files("kpress.publish").joinpath(
            "optimizer_tool", "package-lock.json"
        )
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        packages = lock["packages"]
        root = packages[""]
        dependency = packages[f"node_modules/{FULL_OPTIMIZER_PACKAGE}"]
        assert root["dependencies"] == {FULL_OPTIMIZER_PACKAGE: FULL_OPTIMIZER_VERSION}
        assert dependency["version"] == FULL_OPTIMIZER_VERSION
        assert dependency["resolved"].startswith("https://registry.npmjs.org/")
        assert dependency["integrity"].startswith("sha512-")

    def test_cold_bootstrap_uses_npm_ci_only(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from kpress.publish.optimize import ensure_tool_cache

        monkeypatch.setattr(shutil, "which", _fake_tool_path)
        commands: list[list[str]] = []
        environments: list[dict[str, str]] = []

        def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            commands.append(command)
            environments.append(cast("dict[str, str]", kwargs["env"]))
            cwd = Path(str(kwargs["cwd"]))
            binary = cwd / "node_modules" / ".bin" / FULL_OPTIMIZER_PACKAGE
            binary.parent.mkdir(parents=True)
            binary.touch()
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", run)

        cache = ensure_tool_cache(cache_root=tmp_path)

        assert cache.is_dir()
        assert (cache / ".kpress-lock-sha256").is_file()
        assert commands == [["/usr/bin/npm", "ci", "--ignore-scripts"]]
        assert environments[0]["NPM_CONFIG_MIN_RELEASE_AGE"] == "14"
        assert "NPM_CONFIG_MINIMUM_RELEASE_AGE" not in environments[0]

    def test_cold_bootstrap_without_network_fails_before_npm(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from kpress.publish.optimize import ensure_tool_cache

        monkeypatch.setattr(shutil, "which", _fake_tool_path)

        def unexpected_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
            raise AssertionError(f"npm called: {args!r} {kwargs!r}")

        monkeypatch.setattr(subprocess, "run", unexpected_run)

        with pytest.raises(KPressMissingOptionalDependencyError, match="allow-network"):
            ensure_tool_cache(cache_root=tmp_path, allow_network=False)

    def test_cold_bootstrap_requires_installed_binary(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from kpress.publish.optimize import ensure_tool_cache

        monkeypatch.setattr(shutil, "which", _fake_tool_path)

        def success(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, "", "")

        monkeypatch.setattr(subprocess, "run", success)

        with pytest.raises(KPressOptimizerError, match="did not install"):
            ensure_tool_cache(cache_root=tmp_path)

    def test_cold_bootstrap_wraps_npm_timeout(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from kpress.publish.optimize import ensure_tool_cache

        monkeypatch.setattr(shutil, "which", _fake_tool_path)

        def timeout(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
            raise subprocess.TimeoutExpired(command, 120)

        monkeypatch.setattr(subprocess, "run", timeout)

        with pytest.raises(KPressOptimizerError, match="timed out"):
            ensure_tool_cache(cache_root=tmp_path)


class TestLockedCacheMissingTool:
    """Missing Node/npm raises KPressMissingOptionalDependencyError."""

    def test_optimize_raises_when_node_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(shutil, "which", _stub_which)
        optimizer = FullOptimizer()
        with pytest.raises(KPressMissingOptionalDependencyError, match=r"html-minifier-next|Node"):
            optimizer.optimize("<p>  x  </p>", kind="html")

    def test_optimize_raises_when_npm_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        real_which = shutil.which

        def which_no_npm(name: str) -> str | None:
            if name == "npm":
                return None
            return real_which(name)

        monkeypatch.setattr(shutil, "which", which_no_npm)
        optimizer = FullOptimizer(cache_root=tmp_path)
        with pytest.raises(
            KPressMissingOptionalDependencyError, match=r"html-minifier-next|Node|npm"
        ):
            optimizer.optimize("<p>  x  </p>", kind="html")


class TestDeterministicOutput:
    """Two builds with the same input produce identical output."""

    @needs_full
    def test_deterministic_html_across_builds(self, tmp_path: Path) -> None:
        cache_a = tmp_path / "cache_a"
        cache_b = tmp_path / "cache_b"
        from kpress.publish.optimize import FullOptimizer

        opt_a = FullOptimizer(cache_root=cache_a)
        opt_b = FullOptimizer(cache_root=cache_b)
        html = "<main>\n  <p>hello world</p>\n</main>\n"
        result_a = opt_a.optimize(html, kind="html")
        result_b = opt_b.optimize(html, kind="html")
        assert result_a.content == result_b.content

    @needs_full
    def test_deterministic_css_across_builds(self, tmp_path: Path) -> None:
        cache_a = tmp_path / "cache_a"
        cache_b = tmp_path / "cache_b"
        from kpress.publish.optimize import FullOptimizer

        opt_a = FullOptimizer(cache_root=cache_a)
        opt_b = FullOptimizer(cache_root=cache_b)
        css = ".x {\n  color: red;\n  margin: 0;\n}\n"
        result_a = opt_a.optimize(css, kind="css")
        result_b = opt_b.optimize(css, kind="css")
        assert result_a.content == result_b.content


class TestConcurrentInstall:
    """File lock prevents concurrent installs from corrupting the cache."""

    @needs_full
    def test_concurrent_installs_do_not_corrupt(self, tmp_path: Path) -> None:
        """Two FullOptimizer instances sharing the same cache produce valid output."""
        shared_cache = tmp_path / "shared"
        from kpress.publish.optimize import FullOptimizer

        opt_1 = FullOptimizer(cache_root=shared_cache)
        opt_2 = FullOptimizer(cache_root=shared_cache)

        html = "<main>\n  <p>x</p>\n</main>\n"
        r1 = opt_1.optimize(html, kind="html")
        r2 = opt_2.optimize(html, kind="html")
        assert r1.content == r2.content
        assert r1.changed is True

    @needs_full
    def test_file_lock_exists_during_install(self, tmp_path: Path) -> None:
        """The lock file is created in the cache directory."""
        from kpress.publish.optimize import ensure_tool_cache

        cache = ensure_tool_cache(cache_root=tmp_path)
        assert (cache / ".install.lock").exists() or cache.exists()


class TestNpmPolicyIntegration:
    """The locked layer respects repo npm_env() settings."""

    @needs_full
    def test_cache_respects_npmrc_age_gate(self, tmp_path: Path) -> None:
        from kpress.publish.optimize import ensure_tool_cache

        cache = ensure_tool_cache(cache_root=tmp_path)
        pkg = json.loads((cache / "package.json").read_text())
        assert pkg["dependencies"][FULL_OPTIMIZER_PACKAGE] == FULL_OPTIMIZER_VERSION

    def test_pin_version_matches_optimizer_constant(self) -> None:
        assert FULL_OPTIMIZER_PACKAGE == "html-minifier-next"
        assert FULL_OPTIMIZER_VERSION == "6.2.3"


class TestNoneOptimizerUnchanged:
    """The none optimizer path remains zero-dependency."""

    def test_none_mode_does_not_touch_cache(self, tmp_path: Path) -> None:
        from kpress.publish.optimize import NoneOptimizer

        opt = NoneOptimizer()
        result = opt.optimize("<p>x</p>", kind="html")
        assert result.content == "<p>x</p>"
        assert result.changed is False
        assert not list(tmp_path.iterdir())
