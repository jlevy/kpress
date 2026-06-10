from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
from pathlib import Path

import kpress
import kpress.format as kpress_format
import kpress.publish as kpress_publish
from kpress.contract import (
    ASSET_MANIFEST_REQUIRED_KEYS,
    ASSET_MANIFEST_SCHEMA_VERSION,
    BUILD_MANIFEST_REQUIRED_KEYS,
    BUILD_MANIFEST_SCHEMA_VERSION,
    PUBLIC_CSS_CLASSES,
    PUBLIC_CSS_VARIABLES,
    PUBLIC_DATA_ATTRIBUTES,
    PUBLIC_FORMAT_API,
    PUBLIC_PACKAGE_API,
    PUBLIC_PUBLISH_API,
    PUBLIC_TEMPLATE_VARIABLES,
)
from kpress.format.assets import package_asset_manifest
from kpress.publish.manifest import BuildReport

_KPRESS_ROOT = Path(__file__).resolve().parents[1]


def test_public_python_api_names_are_current_contract() -> None:
    assert tuple(kpress.__all__) == PUBLIC_PACKAGE_API
    assert tuple(kpress_format.__all__) == PUBLIC_FORMAT_API
    assert tuple(kpress_publish.__all__) == PUBLIC_PUBLISH_API


def test_format_import_keeps_publisher_pdf_and_optimizer_out_of_core() -> None:
    code = """
import importlib
import json
import sys

importlib.import_module("kpress.format")
forbidden = (
    "kpress.publish",
    "kpress.publish.optimize",
    "kpress.format.pdf",
    "subprocess",
)
print(json.dumps({name: name in sys.modules for name in forbidden}, sort_keys=True))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == {
        "kpress.format.pdf": False,
        "kpress.publish": False,
        "kpress.publish.optimize": False,
        "subprocess": False,
    }


def test_root_runtime_import_keeps_publisher_pdf_and_optimizer_lazy() -> None:
    code = """
import importlib
import json
import sys

importlib.import_module("kpress")
forbidden = (
    "kpress.publish",
    "kpress.publish.optimize",
    "kpress.format.pdf",
    "subprocess",
)
print(json.dumps({name: name in sys.modules for name in forbidden}, sort_keys=True))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == {
        "kpress.format.pdf": False,
        "kpress.publish": False,
        "kpress.publish.optimize": False,
        "subprocess": False,
    }


def test_css_class_and_variable_contract_is_present_in_assets_and_markup() -> None:
    css_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((_KPRESS_ROOT / "src/kpress/format/static/css").glob("*.css"))
    )
    template_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((_KPRESS_ROOT / "src/kpress/format/templates").rglob("*.jinja"))
    )
    render_source = (_KPRESS_ROOT / "src/kpress/format/render.py").read_text(encoding="utf-8")
    covered_classes = set(re.findall(r"\.([a-zA-Z][\w-]*)", css_text))
    covered_classes.update(re.findall(r"kpress[-a-zA-Z0-9]*", template_text))
    covered_classes.update(re.findall(r"kpress[-a-zA-Z0-9]*", render_source))

    assert set(PUBLIC_CSS_CLASSES) <= covered_classes

    declared_variables = set(re.findall(r"(--kpress-[a-z0-9-]+)\s*:", css_text))
    assert set(PUBLIC_CSS_VARIABLES) <= declared_variables


def test_public_data_attributes_are_emitted_on_rendered_tables() -> None:
    tree = kpress_format.parse_markdown(
        "| Ticker | Amount |\n| --- | ---: |\n| ACME | 12.5 |",
        title="Contract",
    )
    for attribute in PUBLIC_DATA_ATTRIBUTES:
        assert attribute in tree.html


def test_template_variable_contract_matches_packaged_templates() -> None:
    root = _KPRESS_ROOT / "src/kpress/format/templates"
    for rel_path, variables in PUBLIC_TEMPLATE_VARIABLES.items():
        text = (root / rel_path).read_text(encoding="utf-8")
        for variable in variables:
            assert re.search(r"{{\s*" + re.escape(variable) + r"\b", text)


def test_manifest_schema_versions_are_explicit() -> None:
    asset_manifest = package_asset_manifest().as_dict()
    assert tuple(asset_manifest.keys()) == ASSET_MANIFEST_REQUIRED_KEYS
    assert asset_manifest["schema_version"] == ASSET_MANIFEST_SCHEMA_VERSION

    build_manifest = BuildReport(output_dir=Path("public")).as_dict()
    assert tuple(build_manifest.keys()) == BUILD_MANIFEST_REQUIRED_KEYS
    assert build_manifest["schema_version"] == BUILD_MANIFEST_SCHEMA_VERSION


def test_format_pdf_is_available_only_from_pdf_module() -> None:
    assert not hasattr(kpress_format, "render_pdf")

    pdf_module = importlib.import_module("kpress.format.pdf")
    assert hasattr(pdf_module, "render_pdf")


def test_kpress_does_not_import_any_host_package() -> None:
    """KPress stays host-agnostic so MetaBrowser is a faithful test harness."""

    code = """
import importlib
import json
import sys

importlib.import_module("kpress")
importlib.import_module("kpress.runtime")
importlib.import_module("kpress.format")
importlib.import_module("kpress.publish")
leaked = sorted(
    m for m in sys.modules if m == "metabrowser" or m.startswith("metabrowser.")
)
print(json.dumps(leaked))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == []


def test_render_view_returns_jsonable_contract_payload_with_opaque_host() -> None:
    from kpress import runtime

    runtime.clear_render_cache()
    payload = runtime.render_view(
        runtime.KPressRenderRequest(
            source_text="# Title\n\nBody\n",
            source_path="docs/x.md",
            kind="markdown",
            view="rendered",
            ext=".md",
            mtime_hash="a",
            size=14,
            host="some-arbitrary-host-name-kpress-never-special-cases",
        )
    )

    # Round-trips through JSON unchanged: the host boundary is JSON-ready.
    assert json.loads(json.dumps(payload)) == payload
    assert set(payload) == {
        "type",
        "html",
        "profile",
        "printable",
        "assets",
        "diagnostics",
    }
    assert set(payload["assets"]) == {"css", "js"}
