from __future__ import annotations

import pytest

from devtools.check_distribution import check_text_member
from devtools.npm_policy import verify_repo_package_policy


def test_repository_package_policy_is_self_consistent() -> None:
    verify_repo_package_policy()


def test_distribution_hygiene_rejects_private_paths() -> None:
    private_path = "/" + "Users/example/private/source.py"

    with pytest.raises(RuntimeError, match="artifact hygiene failed"):
        check_text_member("kpress/example.txt", private_path.encode())
