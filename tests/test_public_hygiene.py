from __future__ import annotations

from pathlib import Path

from devtools.public_hygiene import find_violations, public_package_paths


def test_public_hygiene_flags_private_path(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("Reference: /Users/example/private/source.py\n", encoding="utf-8")

    findings = find_violations([doc])

    assert [(finding.rule, finding.line) for finding in findings] == [("private-path", 1)]


def test_public_hygiene_flags_secret_like_token(tmp_path: Path) -> None:
    doc = tmp_path / "SECURITY.md"
    doc.write_text("Do not commit sk-" + ("a" * 24) + "\n", encoding="utf-8")

    findings = find_violations([doc])

    assert [(finding.rule, finding.line) for finding in findings] == [("secret-token", 1)]


def test_public_package_paths_exclude_tests(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Public docs\n", encoding="utf-8")
    fixture = tmp_path / "tests" / "fixtures" / "history.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text('{"path": "/Users/example/private/source.py"}\n', encoding="utf-8")

    findings = find_violations(public_package_paths(tmp_path))

    assert findings == []
