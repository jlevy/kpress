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
UV_VERSION = "0.11.25"
UV_LINUX_CHECKSUM = "1db18b5e76fa645a7f3865773139bdec8e2d46adbdbb35e7410b34fa8015ccd2"
BUILD_PINS = ["hatchling==1.30.1", "uv-dynamic-versioning==0.14.0"]
PYTHON_TOOL_FLOORS = {
    "basedpyright>=1.39.9",
    "codespell>=2.4.2",
    "pytest>=9.1.1",
    "pytest-timeout>=2.4.0",
    "ruff>=0.15.20",
}
NPM_TOOL_PINS = {
    "@biomejs/biome": "2.5.1",
    "happy-dom": "20.10.6",
    "lefthook": "2.1.9",
    "typescript": "6.0.3",
    "vitest": "4.1.9",
}
FLOWMARK_VERSION = "0.3.1"
REPREN_VERSION = "3.1.0"
TBD_VERSION = "0.4.0"


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
    if package_data.get("devDependencies") != NPM_TOOL_PINS:
        raise RuntimeError("package.json must contain only the reviewed exact npm tool pins")

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
    if "uv sync --all-extras --all-groups --frozen" not in tooling_text:
        raise RuntimeError("the local install must use every locked dependency group")
    required_audit_commands = (
        "npm audit --audit-level=moderate",
        "uv --preview-features audit-command audit --frozen",
    )
    if any(command not in tooling_text for command in required_audit_commands):
        raise RuntimeError("the audit gate must inspect the locked npm and Python graphs")
    if "UV_CONFIG_FILE ?= $(CURDIR)/uv.toml" not in tooling_text:
        raise RuntimeError("Make targets must isolate uv from machine-global configuration")
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
    required_publish_controls = (
        "types: [published]",
        "environment: pypi",
        "ref: ${{ github.event.release.tag_name }}",
        "run: make verify",
        "^v[0-9]+\\.[0-9]+\\.[0-9]+$",
        "kpress.__version__",
        "uv publish --trusted-publishing always",
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
