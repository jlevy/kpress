from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, cast

import pytest
from pytest import CaptureFixture

from kpress.cli import main


def _no_which(_name: str) -> str | None:
    return None


def _capsys_json(capsys: CaptureFixture[str]) -> dict[str, Any]:
    return cast("dict[str, Any]", json.loads(capsys.readouterr().out))


def test_doctor_default_is_discovery_and_never_fails(capsys: CaptureFixture[str]) -> None:
    code = main(["doctor"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Core render" in out
    assert "Static publish" in out


def test_doctor_json_shape_is_stable(capsys: CaptureFixture[str]) -> None:
    code = main(["doctor", "--json"])
    payload = _capsys_json(capsys)
    assert code == 0
    assert "kpress_version" in payload
    assert "platform" in payload
    caps = payload["capabilities"]
    assert set(caps) == {
        "render",
        "publish",
        "optimizer_full",
        "precompress_brotli",
        "pdf_browser",
    }
    for entry in caps.values():
        assert entry["status"] in {"ok", "unavailable", "skipped", "fail"}


def test_doctor_render_profile_ok(capsys: CaptureFixture[str]) -> None:
    code = main(["doctor", "--profile", "render", "--json"])
    payload = _capsys_json(capsys)
    assert code == 0
    assert payload["capabilities"]["render"]["status"] == "ok"


def test_doctor_optimize_profile_fails_without_node(
    capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shutil, "which", _no_which)
    code = main(["doctor", "--profile", "optimize", "--json"])
    payload = _capsys_json(capsys)
    assert code != 0
    assert payload["capabilities"]["optimizer_full"]["status"] != "ok"


def test_doctor_default_does_not_fail_when_node_missing(
    capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shutil, "which", _no_which)
    code = main(["doctor"])
    capsys.readouterr()
    # Discovery reports unavailable but never fails the process.
    assert code == 0


def test_doctor_config_aggregate_fails_when_required_optimizer_missing(
    tmp_path: Path, capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shutil, "which", _no_which)
    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n  - path: docs\n\noptimizer:\n  mode: full\n",
        encoding="utf-8",
    )
    code = main(["doctor", "--config", str(config), "--json"])
    payload = _capsys_json(capsys)
    assert code != 0
    assert payload["capabilities"]["optimizer_full"]["status"] != "ok"


def test_doctor_config_aggregate_ok_when_nothing_optional_required(
    tmp_path: Path, capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shutil, "which", _no_which)
    config = tmp_path / "kpress.yml"
    config.write_text("sources:\n  - path: docs\n", encoding="utf-8")
    code = main(["doctor", "--config", str(config)])
    capsys.readouterr()
    # optimizer=none, no br, no pdf -> missing Node is not a failure.
    assert code == 0
