from __future__ import annotations

import pytest

from devtools.check_distribution import ROOT, check_text_member
from devtools.npm_policy import (
    NODE_VERSION,
    verify_documented_uv_commands,
    verify_repo_package_policy,
)


def test_repository_package_policy_is_self_consistent() -> None:
    verify_repo_package_policy()


def test_repository_node_version_files_match_the_toolchain() -> None:
    for relative in (".node-version", ".nvmrc"):
        assert (ROOT / relative).read_text(encoding="utf-8").strip() == NODE_VERSION


def test_documented_repository_commands_require_locked_and_frozen_uv() -> None:
    verify_documented_uv_commands(
        "example.md",
        "uv --config-file uv.toml sync --all-groups --locked\n"
        "uv --config-file uv.toml run --frozen pytest\n",
    )

    with pytest.raises(RuntimeError, match="non-locked uv sync"):
        verify_documented_uv_commands("example.md", "uv --config-file uv.toml sync --all-groups\n")
    with pytest.raises(RuntimeError, match="non-frozen uv run"):
        verify_documented_uv_commands("example.md", "uv --config-file uv.toml run pytest\n")


def test_distribution_hygiene_rejects_private_paths() -> None:
    private_path = "/" + "Users/example/private/source.py"

    with pytest.raises(RuntimeError, match="artifact hygiene failed"):
        check_text_member("kpress/example.txt", private_path.encode())


def test_distribution_hygiene_requires_readme_footer() -> None:
    with pytest.raises(RuntimeError, match="documentation footer is missing"):
        check_text_member("kpress-0.0.0/README.md", b"# KPress\n")
