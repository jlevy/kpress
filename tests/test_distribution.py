from __future__ import annotations

import pytest

from devtools.check_distribution import check_text_member


def test_distribution_hygiene_rejects_private_paths() -> None:
    private_path = "/" + "Users/example/private/source.py"

    with pytest.raises(RuntimeError, match="artifact hygiene failed"):
        check_text_member("kpress/example.txt", private_path.encode())


def test_distribution_hygiene_requires_readme_footer() -> None:
    with pytest.raises(RuntimeError, match="documentation footer is missing"):
        check_text_member("kpress-0.0.0/README.md", b"# KPress\n")
