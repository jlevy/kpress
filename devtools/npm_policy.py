"""Verify KPress package-resolution and release policy."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NPM_MIN_RELEASE_AGE_DAYS = "14"
NODE_VERSION = "24.18.0"
NODE_RANGE = ">=24.18.0 <25"
NPM_RANGE = ">=11.10.0 <12"
CHECKOUT_SHA = "9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0"
SETUP_UV_SHA = "fac544c07dec837d0ccb6301d7b5580bf5edae39"
SETUP_NODE_SHA = "48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e"
UV_VERSION = "0.11.26"
UV_LINUX_CHECKSUM = "6426a73c3837e6e2483ee344cbc00f36394d179afcba6183cb77437e67db4af0"
BUILD_PINS = ["hatchling==1.30.1", "uv-dynamic-versioning==0.14.0"]
RUNTIME_TOOL_FLOORS = {"strif>=3.1.0"}
PYTHON_TOOL_FLOORS = {
    "basedpyright>=1.39.9",
    "codespell>=2.4.2",
    "pytest>=9.1.1",
    "pytest-timeout>=2.4.0",
    "ruff>=0.15.20",
}
NPM_TOOL_PINS = {
    "@biomejs/biome": "2.5.2",
    "happy-dom": "20.10.6",
    "lefthook": "2.1.9",
    "typescript": "6.0.3",
    "vitest": "4.1.9",
}
FLOWMARK_VERSION = "0.3.2"
FLOWMARK_EXCEPTION = "2026-07-16T00:00:00Z"
REPREN_VERSION = "3.1.0"
TBD_VERSION = "0.4.0"


def verify_documented_uv_commands(source: str, text: str) -> None:
    """Reject repository commands that bypass the checked-in uv policy."""
    if re.search(r"\buv(?:\s+--config-file\s+uv\.toml)?\s+run(?! --frozen)(?=\s)", text):
        raise RuntimeError(f"{source} documents a non-frozen uv run command")
    sync_arguments = re.findall(r"\buv\s+--config-file\s+uv\.toml\s+sync([^\n]*)", text)
    if any("--locked" not in arguments for arguments in sync_arguments):
        raise RuntimeError(f"{source} documents a non-locked uv sync command")
    if re.search(r"\buv\s+(?:build|lock|run|sync)\b", text):
        raise RuntimeError(f"{source} documents a repository command without --config-file uv.toml")


def verify_repo_package_policy(root: Path = ROOT) -> None:
    """Raise when package or tool configuration bypasses repository policy."""
    npmrc = (root / ".npmrc").read_text(encoding="utf-8")
    required_npmrc = {
        "engine-strict=true",
        "ignore-scripts=true",
        f"min-release-age={NPM_MIN_RELEASE_AGE_DAYS}",
        "package-lock=true",
        "save-exact=true",
    }
    missing = sorted(line for line in required_npmrc if line not in npmrc.splitlines())
    if missing:
        raise RuntimeError(f".npmrc is missing required settings: {missing}")

    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    if not RUNTIME_TOOL_FLOORS.issubset(pyproject["project"].get("dependencies", [])):
        raise RuntimeError("runtime dependencies must preserve the reviewed first-party floors")
    if pyproject["dependency-groups"].get("build") != BUILD_PINS:
        raise RuntimeError("the build dependency group must contain the exact backend pins")
    if pyproject["build-system"].get("requires") != BUILD_PINS:
        raise RuntimeError("the isolated build system must contain the exact backend pins")
    if not PYTHON_TOOL_FLOORS.issubset(pyproject["dependency-groups"].get("dev", [])):
        raise RuntimeError("the development group must preserve the reviewed Python tool floors")
    uv_toml = tomllib.loads((root / "uv.toml").read_text(encoding="utf-8"))
    if uv_toml != {"required-version": ">=0.11.21", "exclude-newer": "14 days"}:
        raise RuntimeError("uv.toml must contain only the reviewed uv policy")

    answers = (root / ".copier-answers.yml").read_text(encoding="utf-8")
    required_answers = (
        "_commit: v0.4.0",
        "package_license: AGPL-3.0-or-later",
        "publish_to_pypi: true",
    )
    if any(value not in answers for value in required_answers):
        raise RuntimeError("Copier answers must record the reviewed v0.4.0 template choices")

    package_data = json.loads((root / "package.json").read_text(encoding="utf-8"))
    if package_data.get("private") is not True:
        raise RuntimeError("the npm development-tool package must remain private")
    if package_data.get("engines") != {"node": NODE_RANGE, "npm": NPM_RANGE}:
        raise RuntimeError("package.json must require the reviewed Node and npm ranges")
    for relative in (".node-version", ".nvmrc"):
        path = root / relative
        if not path.is_file() or path.read_text(encoding="utf-8").strip() != NODE_VERSION:
            raise RuntimeError(f"{relative} must pin Node {NODE_VERSION}")
    if package_data.get("devDependencies") != NPM_TOOL_PINS:
        raise RuntimeError("package.json must contain only the reviewed exact npm tool pins")
    biome_data = json.loads((root / "biome.json").read_text(encoding="utf-8"))
    expected_biome_schema = (
        f"https://biomejs.dev/schemas/{NPM_TOOL_PINS['@biomejs/biome']}/schema.json"
    )
    if biome_data.get("$schema") != expected_biome_schema:
        raise RuntimeError("biome.json schema must match the exact Biome tool pin")

    lock_data = json.loads((root / "package-lock.json").read_text(encoding="utf-8"))
    lock_packages = lock_data.get("packages", {})
    if lock_packages.get("", {}).get("devDependencies") != NPM_TOOL_PINS:
        raise RuntimeError("package-lock.json root pins do not match package.json")
    if lock_packages.get("", {}).get("engines") != package_data["engines"]:
        raise RuntimeError("package-lock.json root engines do not match package.json")
    for package, version in NPM_TOOL_PINS.items():
        locked = lock_packages.get(f"node_modules/{package}", {})
        if locked.get("version") != version:
            raise RuntimeError(f"package-lock.json must contain exact {package}@{version}")
    for package_path, locked in lock_packages.items():
        if not package_path:
            continue
        resolved = str(locked.get("resolved", ""))
        integrity = str(locked.get("integrity", ""))
        if not resolved.startswith("https://registry.npmjs.org/"):
            raise RuntimeError(f"{package_path} must resolve from the npm registry")
        if not integrity.startswith("sha512-"):
            raise RuntimeError(f"{package_path} must have a sha512 lockfile integrity hash")

    tooling_paths = [
        root / "Makefile",
        root / "devtools" / "biome.py",
        root / "devtools" / "js_dom_tests.py",
        root / "devtools" / "tsc_check.py",
    ]
    tooling_text = "\n".join(path.read_text(encoding="utf-8") for path in tooling_paths)
    if "flowmark-rs@$(FLOWMARK_VERSION)" not in tooling_text:
        raise RuntimeError(f"Flowmark tooling must preserve its {FLOWMARK_VERSION} pin")
    if f"--exclude-newer-package 'flowmark-rs={FLOWMARK_EXCEPTION}'" not in tooling_text:
        raise RuntimeError("Flowmark must use only its reviewed first-party age exception")
    agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")
    if f"flowmark-rs=={FLOWMARK_VERSION}" not in agents_text:
        raise RuntimeError("AGENTS.md must document the exact Flowmark tool pin")
    makefile_text = (root / "Makefile").read_text(encoding="utf-8")
    if "$(FLOWMARK) --auto --inplace --nobackup ." not in makefile_text:
        raise RuntimeError("Flowmark formatting must update in place without backup artifacts")
    if "UV := uv --config-file $(CURDIR)/uv.toml" not in makefile_text:
        raise RuntimeError("Make targets must select the repository uv configuration")
    if "UVX := uvx --config-file $(CURDIR)/uv.toml" not in makefile_text:
        raise RuntimeError("Make targets must select the repository uvx configuration")
    if "UV_RUN := $(UV) run --frozen" not in makefile_text:
        raise RuntimeError("Make targets must use a frozen uv runner")
    if "$(UV) sync --all-extras --all-groups --locked" not in makefile_text:
        raise RuntimeError("the local install must validate every locked dependency group")
    ambient_npm_policy = (
        "NPM_CONFIG_BEFORE",
        "NPM_CONFIG_FROZEN_LOCKFILE",
        "NPM_CONFIG_MINIMUM_RELEASE_AGE",
    )
    missing_npm_unexports = [
        variable for variable in ambient_npm_policy if f"unexport {variable}" not in makefile_text
    ]
    if missing_npm_unexports:
        raise RuntimeError(
            f"Make targets must ignore conflicting ambient npm policy: {missing_npm_unexports}"
        )
    if re.search(r"^\tuvx?\s", makefile_text, re.MULTILINE):
        raise RuntimeError("Make recipes must not invoke bare uv or uvx")
    if (
        "default: install\n\t$(MAKE) SKIP_INSTALL=1 format\n"
        "\t$(MAKE) SKIP_INSTALL=1 lint\n\t$(MAKE) SKIP_INSTALL=1 test" not in makefile_text
    ):
        raise RuntimeError("the mutating default workflow must run format, lint, and test serially")
    if "format lint: | install" not in makefile_text or (
        "lint-check test audit build: | install" not in makefile_text
    ):
        raise RuntimeError("parallel quality gates must wait for the install target")
    lefthook_text = (root / "lefthook.yml").read_text(encoding="utf-8")
    if re.search(r"^\s*run:\s+uv\s+(?!--config-file uv\.toml\s)", lefthook_text, re.MULTILINE):
        raise RuntimeError("hooks must select the repository uv configuration")
    if re.search(
        r"^\s*run:.*\buv --config-file uv\.toml run(?! --frozen)(?=\s)",
        lefthook_text,
        re.MULTILINE,
    ):
        raise RuntimeError("hooks must use frozen uv runners")
    command_doc_paths = [
        root / "CONTRIBUTING.md",
        root / "docs/development.md",
        root / "docs/kpress-e2e-testing.runbook.md",
        root / "docs/kpress-validation.runbook.md",
        root / "tests/golden/README.md",
    ]
    for path in command_doc_paths:
        verify_documented_uv_commands(str(path.relative_to(root)), path.read_text(encoding="utf-8"))
    required_audit_commands = (
        "npm audit --audit-level=moderate",
        "$(UV) --preview-features audit-command audit --frozen",
    )
    if any(command not in tooling_text for command in required_audit_commands):
        raise RuntimeError("the audit gate must inspect the locked npm and Python graphs")
    if "npx --yes" in tooling_text or '"--package"' in tooling_text:
        raise RuntimeError("npm tools must never fetch packages during repository gates")

    skill_pins = {
        ".agents/skills/tbd/SKILL.md": f"get-tbd@{TBD_VERSION}",
        ".claude/skills/tbd/SKILL.md": f"get-tbd@{TBD_VERSION}",
        ".agents/skills/repren/SKILL.md": f"repren@{REPREN_VERSION}",
        ".claude/skills/repren/SKILL.md": f"repren@{REPREN_VERSION}",
    }
    for relative, required_pin in skill_pins.items():
        text = (root / relative).read_text(encoding="utf-8")
        if required_pin not in text or "@latest" in text:
            raise RuntimeError(f"{relative} must preserve the exact {required_pin} runner")

    workflow_paths = sorted((root / ".github" / "workflows").glob("*.yml"))
    workflow_text = "\n".join(path.read_text(encoding="utf-8") for path in workflow_paths)
    if re.search(r"\buv\s+(?:build|lock|publish|run|sync)\b", workflow_text):
        raise RuntimeError("workflows must select the repository uv configuration")
    if re.search(r"\buv --config-file uv\.toml run(?! --frozen)(?=\s)", workflow_text):
        raise RuntimeError("workflows must use frozen uv runners")
    workflow_sync_arguments = re.findall(r"\buv --config-file uv\.toml sync([^\n]*)", workflow_text)
    if any("--locked" not in arguments for arguments in workflow_sync_arguments):
        raise RuntimeError("workflows must validate the committed uv lock")
    action_uses = re.findall(r"^\s*uses:\s+[^@\s]+@([^\s#]+)", workflow_text, re.MULTILINE)
    mutable_actions = [ref for ref in action_uses if re.fullmatch(r"[0-9a-f]{40}", ref) is None]
    if mutable_actions:
        raise RuntimeError(f"GitHub Actions must use full commit SHAs: {mutable_actions}")
    required_workflow_pins = (
        f"actions/checkout@{CHECKOUT_SHA}",
        f"astral-sh/setup-uv@{SETUP_UV_SHA}",
        f"actions/setup-node@{SETUP_NODE_SHA}",
        f'version: "{UV_VERSION}"',
        f'checksum: "{UV_LINUX_CHECKSUM}"',
    )
    missing_workflow_pins = [
        value for value in required_workflow_pins if value not in workflow_text
    ]
    if missing_workflow_pins:
        raise RuntimeError(f"workflows are missing reviewed pins: {missing_workflow_pins}")
    node_versions = set(
        re.findall(r'^\s*node-version:\s*["\']?([^\s"\']+)', workflow_text, re.MULTILINE)
    )
    if node_versions != {NODE_VERSION}:
        raise RuntimeError(f"workflows must use only Node {NODE_VERSION}, got {node_versions}")
    checkout_count = workflow_text.count(f"actions/checkout@{CHECKOUT_SHA}")
    if workflow_text.count("persist-credentials: false") != checkout_count:
        raise RuntimeError("every checkout must disable persisted credentials")
    if workflow_text.count("fetch-depth: 0") != checkout_count:
        raise RuntimeError("every checkout must fetch tags for dynamic versioning")

    publish_workflow = (root / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    if "enable-cache: false" not in publish_workflow:
        raise RuntimeError("publishing must explicitly disable the uv cache")
    if "enable-cache: true" in publish_workflow or re.search(
        r'^\s*cache:\s*["\']?npm', publish_workflow, re.MULTILINE
    ):
        raise RuntimeError("publishing must not restore mutable dependency caches")
    required_publish_controls = (
        "types: [published]",
        "environment: pypi",
        "ref: ${{ github.event.release.tag_name }}",
        "run: make verify",
        "^v[0-9]+\\.[0-9]+\\.[0-9]+$",
        "kpress.__version__",
        "uv --config-file uv.toml publish --trusted-publishing always",
    )
    missing_publish_controls = [
        value for value in required_publish_controls if value not in publish_workflow
    ]
    if missing_publish_controls:
        raise RuntimeError(f"publish workflow is missing controls: {missing_publish_controls}")


def main() -> int:
    verify_repo_package_policy()
    print("Package policy checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
