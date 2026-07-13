from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pytest import CaptureFixture

from kpress.cli import build_parser, main
from kpress.errors import KPressMissingOptionalDependencyError


def test_cli_format_asset_mode_lever(tmp_path: Path) -> None:
    src = tmp_path / "doc.md"
    src.write_text("# Title\n\nBody\n", encoding="utf-8")

    linked_dir = tmp_path / "linked"
    hashed_dir = tmp_path / "hashed"
    work = str(tmp_path / ".kpress")

    assert main(["--work-root", work, "format", str(src), "--output-dir", str(linked_dir)]) == 0
    assert (
        main(
            [
                "--work-root",
                work,
                "format",
                str(src),
                "--output-dir",
                str(hashed_dir),
                "--asset-mode",
                "hashed",
            ]
        )
        == 0
    )

    linked_html = (linked_dir / "doc.html").read_text(encoding="utf-8")
    hashed_html = (hashed_dir / "doc.html").read_text(encoding="utf-8")

    # The lever changes asset shaping: linked references stable asset names,
    # hashed references content-hashed names (plus the JS import map).
    assert '<link rel="stylesheet"' in linked_html
    assert '<script type="importmap">' in hashed_html

    # An unknown asset mode is rejected by the choices constraint, and
    # `inline` is deliberately not offered until it is self-contained.
    for rejected in ("bogus", "inline"):
        with pytest.raises(SystemExit):
            _ = main(["--work-root", work, "format", str(src), "--asset-mode", rejected])


@pytest.mark.parametrize(
    "args",
    [
        ["format", "doc.md", "--show"],
        ["render", "doc.md", "--show"],
        ["paste", "--plaintext"],
        ["paste", "--show"],
        ["files", "--all"],
        ["export", "doc.md", "--docx", "doc.docx"],
    ],
)
def test_cli_rejects_retired_no_op_flags(args: list[str]) -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(args)


def test_cli_init_and_build(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    config = tmp_path / "kpress.yml"
    assert main(["--work-root", str(tmp_path / ".kpress"), "init", "--config", str(config)]) == 0
    (tmp_path / "index.md").write_text("# Home\n", encoding="utf-8")

    code = main(
        [
            "--work-root",
            str(tmp_path / ".kpress"),
            "build",
            "--config",
            str(config),
            "--output-dir",
            str(tmp_path / "public"),
        ]
    )

    assert code == 0
    assert (tmp_path / "public" / "index.html").exists()


def test_cli_clean_removes_build_output_and_work_root(
    tmp_path: Path, capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "kpress.yml"
    work = tmp_path / ".kpress"
    output = tmp_path / "public"
    assert main(["--work-root", str(work), "init", "--config", str(config)]) == 0
    (tmp_path / "index.md").write_text("# Home\n", encoding="utf-8")
    assert main(["--work-root", str(work), "build", "--config", str(config)]) == 0
    assert output.is_dir() and work.is_dir()
    _ = capsys.readouterr()

    assert main(["--work-root", str(work), "clean", "--config", str(config)]) == 0
    assert not output.exists()
    assert not work.exists()
    out = capsys.readouterr().out
    assert "public" in out and ".kpress" in out


def test_cli_clean_refuses_output_dir_without_manifest(
    tmp_path: Path, capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "kpress.yml"
    assert main(["--work-root", str(tmp_path / ".kpress"), "init", "--config", str(config)]) == 0
    output = tmp_path / "public"
    output.mkdir()
    precious = output / "notes.txt"
    precious.write_text("not a kpress build\n", encoding="utf-8")
    _ = capsys.readouterr()

    code = main(["--work-root", str(tmp_path / ".kpress"), "clean", "--config", str(config)])

    assert code == 2
    assert precious.exists()
    assert "Refusing to remove" in capsys.readouterr().out


def test_cli_missing_clipboard_extra_reports_diagnostic(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    code = main(["--work-root", str(tmp_path / ".kpress"), "paste", "--title", "Note"])

    captured = capsys.readouterr()
    assert code == 2
    assert "Missing optional clipboard extra" in captured.out


def test_cli_optimize_writes_output(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    source = tmp_path / "page.html"
    output = tmp_path / "out.html"
    source.write_text("<main>\n  <p>x</p>\n</main>", encoding="utf-8")

    code = main(["optimize", str(source), "--output", str(output), "--backend", "none"])

    captured = capsys.readouterr()
    assert code == 0
    assert '"backend": "none"' in captured.out
    # none mode publishes content unchanged.
    assert output.read_text(encoding="utf-8") == "<main>\n  <p>x</p>\n</main>"


def test_cli_build_missing_extra_returns_json_diagnostic(
    tmp_path: Path, capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing_extra(*_args: Any, **_kwargs: Any) -> None:
        raise KPressMissingOptionalDependencyError("Brotli requires kpress[optimize].")

    monkeypatch.setattr("kpress.cli.build_site", missing_extra)

    code = main(["build", "--config", str(tmp_path / "kpress.yml")])

    captured = capsys.readouterr()
    assert code == 2
    assert "KPressMissingOptionalDependencyError" in captured.out
    assert "kpress[optimize]" in captured.out


def test_cli_optimize_missing_extra_returns_json_diagnostic(
    tmp_path: Path, capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "page.html"
    source.write_text("<p>x</p>", encoding="utf-8")

    def missing_extra(*_args: Any, **_kwargs: Any) -> None:
        raise KPressMissingOptionalDependencyError(
            "The full optimizer requires Node.js; or use kpress[optimize] for br."
        )

    monkeypatch.setattr("kpress.cli.optimize_text", missing_extra)

    code = main(["optimize", str(source), "--backend", "full"])

    captured = capsys.readouterr()
    assert code == 2
    assert "KPressMissingOptionalDependencyError" in captured.out
    assert "kpress[optimize]" in captured.out


def test_cli_render_writes_single_html_file(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    src = tmp_path / "note.md"
    src.write_text("# Heading\n\nBody.\n", encoding="utf-8")
    out = tmp_path / "out" / "note.html"
    work = str(tmp_path / ".kpress")

    code = main(["--work-root", work, "render", str(src), "--output", str(out)])

    captured = capsys.readouterr()
    assert code == 0
    assert '"command": "render"' in captured.out
    assert out.is_file()
    html = out.read_text(encoding="utf-8")
    assert "<h1" in html and "Heading" in html


def test_cli_render_parses_frontmatter(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    src = tmp_path / "note.md"
    src.write_text(
        "---\ntitle: Custom Title\nog_title: Social Title\n---\n\n# Body Heading\n\nText.\n",
        encoding="utf-8",
    )
    out = tmp_path / "out" / "note.html"
    work = str(tmp_path / ".kpress")

    code = main(["--work-root", work, "render", str(src), "--output", str(out)])

    assert code == 0
    html = out.read_text(encoding="utf-8")
    body = html.split("<body", 1)[1]
    # Frontmatter drives the title; raw YAML never leaks into the body as text.
    # (Parsed keys do surface in the collapsible Metadata <dl>, which is intended.)
    assert "<title>Custom Title</title>" in html
    assert "title: Custom Title" not in body
    assert "og_title: Social Title" not in body
    assert "<dd>Social Title</dd>" in body
    assert "Body Heading" in body


def test_cli_render_emits_math_assets_and_collects_images(tmp_path: Path) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "fig.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 4"></svg>\n', encoding="utf-8"
    )
    src = tmp_path / "doc.md"
    src.write_text(
        "# Math\n\nInline $a^2$ and a figure.\n\n![Fig](assets/fig.svg)\n", encoding="utf-8"
    )
    out = tmp_path / "out" / "doc.html"

    code = main(
        ["--work-root", str(tmp_path / ".kpress"), "render", str(src), "--output", str(out)]
    )

    assert code == 0
    # A math document materializes the KaTeX bundle beside the HTML...
    assert (out.parent / "_kpress" / "assets" / "katex" / "katex.min.css").is_file()
    # ...and referenced document media is copied so figures resolve offline.
    assert (out.parent / "assets" / "fig.svg").is_file()


def test_cli_convert_writes_markdown(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    src = tmp_path / "page.md"
    src.write_text("# Hello\n\nWorld.\n", encoding="utf-8")
    work = str(tmp_path / ".kpress")

    code = main(["--work-root", work, "convert", str(src), "--output", str(tmp_path / "page.md")])

    captured = capsys.readouterr()
    assert code == 0
    assert '"command": "convert"' in captured.out


def test_cli_files_lists_work_root_contents(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    work = tmp_path / ".kpress"
    work.mkdir()
    (work / "marker.txt").write_text("seen\n", encoding="utf-8")

    code = main(["--work-root", str(work), "files"])

    captured = capsys.readouterr()
    assert code == 0
    assert '"command": "files"' in captured.out
    assert "marker.txt" in captured.out


def test_cli_export_writes_html(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    src = tmp_path / "doc.md"
    src.write_text("# Heading\n\nBody.\n", encoding="utf-8")
    html_out = tmp_path / "doc.html"
    work = str(tmp_path / ".kpress")

    code = main(["--work-root", work, "export", str(src), "--html", str(html_out)])

    captured = capsys.readouterr()
    assert code == 0
    assert '"command": "export"' in captured.out
    assert html_out.is_file()
    assert "<h1" in html_out.read_text(encoding="utf-8")


def test_cli_clean_resolves_output_dir_relative_to_config(
    tmp_path: Path, capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """`clean` must resolve publish.output_dir against the config file's
    directory exactly like `build_site` does, not against the caller's cwd
    (PR #175 review finding 1a).
    """

    site = tmp_path / "site"
    site.mkdir()
    config = site / "kpress.yml"
    work = site / ".kpress"
    (site / "index.md").write_text("# Home\n", encoding="utf-8")
    assert main(["--work-root", str(work), "init", "--config", str(config)]) == 0
    assert main(["--work-root", str(work), "build", "--config", str(config)]) == 0
    output = site / "public"
    assert output.is_dir()
    _ = capsys.readouterr()

    # Run from an unrelated cwd: the config-relative output dir must still be
    # found and removed (previously this exited 0 having removed nothing).
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert main(["--work-root", str(work), "clean", "--config", str(config)]) == 0
    assert not output.exists()


def test_cli_clean_refuses_unmarked_work_root(
    tmp_path: Path, capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """`clean --work-root <dir>` must never delete a directory KPress does not
    own: only the default `.kpress` name or the work-root marker qualify
    (PR #175 review finding 1b).
    """

    monkeypatch.chdir(tmp_path)
    victim = tmp_path / "important-data"
    victim.mkdir()
    (victim / "keep.txt").write_text("precious\n", encoding="utf-8")

    code = main(["--work-root", str(victim), "clean", "--config", str(tmp_path / "kpress.yml")])

    assert code == 2
    assert victim.is_dir() and (victim / "keep.txt").exists()
    assert "Refusing to remove work root" in capsys.readouterr().out


def test_cli_clean_removes_marked_custom_work_root(
    tmp_path: Path, capsys: CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from kpress.workflow.workspace import prepare_work_root

    monkeypatch.chdir(tmp_path)
    custom = tmp_path / "my-work"
    prepare_work_root(custom)

    code = main(["--work-root", str(custom), "clean", "--config", str(tmp_path / "kpress.yml")])

    assert code == 0
    assert not custom.exists()
    _ = capsys.readouterr()
