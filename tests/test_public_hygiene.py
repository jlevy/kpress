from __future__ import annotations

import json
from pathlib import Path

from devtools.public_hygiene import (
    COMMON_DOC_FOOTER,
    KPRESS_CSS_ROOT,
    ROOT,
    find_documentation_findings,
    find_sizing_findings,
    find_theme_vocabulary_findings,
    find_violations,
    public_package_paths,
)


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


def test_project_markdown_requires_common_document_footer() -> None:
    project_doc = ROOT / "docs" / "example.md"

    assert find_documentation_findings(project_doc, "# Example\n") == [
        "docs/example.md: missing common-doc-guidelines footer"
    ]
    assert find_documentation_findings(project_doc, COMMON_DOC_FOOTER) == []
    assert find_documentation_findings(ROOT / "src" / "example.py", "") == []


def test_generated_and_rendering_documents_are_footer_exempt() -> None:
    generated = ROOT / ".agents" / "skills" / "tbd" / "SKILL.md"
    rendering_fixture = ROOT / "tests" / "fixtures" / "documents" / "minimal.md"
    rendering_example = ROOT / "examples" / "static-site" / "content" / "index.md"

    assert find_documentation_findings(generated, "") == []
    assert find_documentation_findings(rendering_fixture, "") == []
    assert find_documentation_findings(rendering_example, "") == []


def test_sizing_findings_flag_rem_font_sizes_and_size_tokens(tmp_path: Path) -> None:
    css = tmp_path / "sample.css"
    text = (
        ".a { font-size: 1.2rem; }\n"
        ".b { font-size: clamp(\n    1.75rem,\n    4.5vw,\n    2.3rem\n  ); }\n"
        ":root { --kpress-font-size-mono: 0.82rem; --kpress-bullet-size: 0.9rem; }\n"
        ".c { font-size: var(--kpress-font-size-h2, 1.32rem); }\n"
        ":root { --kpress-caps-label-size: 0.9rem; }\n"
    )

    findings = find_sizing_findings(css, text)

    assert [(finding.rule, finding.line) for finding in findings] == [
        ("rem-font-size", 1),
        ("rem-font-size", 2),
        ("rem-font-size", 7),
        ("rem-font-size", 7),
        # A rem fallback literal inside var() is still a rem reference.
        ("rem-font-size", 8),
        ("rem-font-size", 9),
    ]


def test_sizing_findings_allow_base_derivations_and_the_base_default(tmp_path: Path) -> None:
    css = tmp_path / "sample.css"
    text = (
        ":root { --kpress-font-size-base: var(--kpress-host-font-size-base, 1rem); }\n"
        ".a { font-size: calc(var(--kpress-font-size-base) * 1.7); }\n"
        ".b { font-size: var(--kpress-font-size-mono); }\n"
        ".c { font-size: 0.85em; }\n"
        ".d { font-size: 110%; }\n"
        ".e { margin: 1rem; max-width: 48rem; }\n"
    )

    assert find_sizing_findings(css, text) == []


def test_theme_vocabulary_findings_flag_mode_attribute_selectors(tmp_path: Path) -> None:
    css = tmp_path / "sample.css"
    text = (
        '.kpress[data-kpress-theme="dark"] { color: black; }\n'
        ':where([data-kpress-resolved-theme="dark"]) .kpress { color: white; }\n'
        "[data-kpress-theme-choice] { cursor: pointer; }\n"
        "/* prose mention of data-kpress-theme is fine */\n"
    )

    findings = find_theme_vocabulary_findings(css, text)

    assert [(finding.rule, finding.line) for finding in findings] == [("mode-keyed-css", 1)]


def test_shipped_css_keys_only_on_the_resolved_theme() -> None:
    findings = [
        finding
        for path in sorted(KPRESS_CSS_ROOT.glob("*.css"))
        for finding in find_theme_vocabulary_findings(path, path.read_text(encoding="utf-8"))
    ]

    assert findings == []


def test_shipped_css_derives_every_font_size_from_the_base() -> None:
    findings = [
        finding
        for path in sorted(KPRESS_CSS_ROOT.glob("*.css"))
        for finding in find_sizing_findings(path, path.read_text(encoding="utf-8"))
    ]

    assert findings == []


# The agent hook and skill files under .claude/, .codex/ and .agents/ are
# GENERATED by `tbd setup --auto` and owned by tbd, which is first-party. We
# take what its generator produces rather than hand-patching it, because a hand
# patch is silently undone by the next refresh. These tests therefore assert
# that the hooks are wired at all, not what shape tbd writes them in -- they
# previously pinned the anchored path form and the get-tbd runner version, which
# made every tbd upgrade fail here and left the repo four minors behind.
def test_agent_hooks_are_wired_for_both_agents() -> None:
    known_scripts = ("tbd-session.sh", "tbd-closing-reminder.sh", "ensure-gh-cli.sh")

    for relative in (".codex/hooks.json", ".claude/settings.json"):
        payload = json.loads((ROOT / relative).read_text())
        commands = [
            hook["command"]
            for groups in payload["hooks"].values()
            for group in groups
            for hook in group["hooks"]
        ]
        assert commands, f"{relative} declares no hook commands"
        for command in commands:
            assert any(script in command for script in known_scripts), (
                f"{relative} runs an unrecognised hook command: {command!r}"
            )
            script = command.split()[-1] if command.endswith(".sh") else command.split()[1]
            path = ROOT / script.replace('"$CLAUDE_PROJECT_DIR"/', "").lstrip("/")
            assert path.exists(), f"{relative} points at a missing script: {script}"


def test_third_party_skill_runners_use_exact_versions() -> None:
    """Exact pins are the rule for runners we do not publish.

    tbd is excluded deliberately, and it is the only exclusion: its skill file is
    generated, and the `@latest` in it is tbd's own documented install line
    rather than a runner this repository executes in a build, test, or
    publishing path. See SUPPLY-CHAIN-SECURITY.md, "The Default".
    """

    expected = {
        ".agents/skills/repren/SKILL.md": "repren@3.1.0",
        ".claude/skills/repren/SKILL.md": "repren@3.1.0",
    }

    for relative, pin in expected.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert pin in text
        assert "@latest" not in text
