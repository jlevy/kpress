from __future__ import annotations

import json
from pathlib import Path

from devtools.public_hygiene import ROOT, find_violations, public_package_paths


def test_public_hygiene_flags_private_path(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("Reference: /" + "Users/example/private/source.py\n", encoding="utf-8")

    findings = find_violations([doc])

    assert [(finding.rule, finding.line) for finding in findings] == [("private-path", 1)]


def test_public_hygiene_flags_secret_like_token(tmp_path: Path) -> None:
    doc = tmp_path / "SECURITY.md"
    doc.write_text("Do not commit sk-" + ("a" * 24) + "\n", encoding="utf-8")

    findings = find_violations([doc])

    assert [(finding.rule, finding.line) for finding in findings] == [("secret-token", 1)]


def test_public_package_paths_include_tests(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Public docs\n", encoding="utf-8")
    fixture = tmp_path / "tests" / "fixtures" / "history.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text('{"status": "public"}\n', encoding="utf-8")

    findings = find_violations(public_package_paths(tmp_path))

    assert findings == []


def test_public_package_paths_scan_test_fixtures(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Public docs\n", encoding="utf-8")
    fixture = tmp_path / "tests" / "fixtures" / "history.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text('{"path": "/' + 'Users/example/private/source.py"}\n', encoding="utf-8")

    findings = find_violations(public_package_paths(tmp_path))

    assert [(finding.rule, finding.line) for finding in findings] == [("private-path", 1)]


def test_public_package_paths_scan_both_skill_trees(tmp_path: Path) -> None:
    for skill_root in (".agents", ".claude"):
        skill = tmp_path / skill_root / "skills" / "using-kpress" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("Reference: /" + "Users/example/private/source.py\n", encoding="utf-8")

    findings = find_violations(public_package_paths(tmp_path))

    assert [(finding.path.parts[-4], finding.rule) for finding in findings] == [
        (".agents", "private-path"),
        (".claude", "private-path"),
    ]


def test_codex_hook_commands_anchor_to_repository_root() -> None:
    payload = json.loads((ROOT / ".codex" / "hooks.json").read_text())
    commands = [
        hook["command"]
        for groups in payload["hooks"].values()
        for group in groups
        for hook in group["hooks"]
    ]

    assert commands
    assert all("$(git rev-parse --show-toplevel)" in command for command in commands)
    assert all("bash .codex/" not in command for command in commands)


def test_claude_hook_commands_anchor_to_project_root() -> None:
    payload = json.loads((ROOT / ".claude" / "settings.json").read_text())
    commands = [
        hook["command"]
        for groups in payload["hooks"].values()
        for group in groups
        for hook in group["hooks"]
    ]

    assert commands
    assert all('"$CLAUDE_PROJECT_DIR"' in command for command in commands)
    assert all("bash .claude/" not in command for command in commands)


def test_agent_skill_runners_use_exact_versions() -> None:
    expected = {
        ".agents/skills/tbd/SKILL.md": "get-tbd@0.4.0",
        ".claude/skills/tbd/SKILL.md": "get-tbd@0.4.0",
        ".agents/skills/repren/SKILL.md": "repren@3.1.0",
        ".claude/skills/repren/SKILL.md": "repren@3.1.0",
    }

    for relative, pin in expected.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert pin in text
        assert "@latest" not in text
