"""Real-PDF regression for the faces a printed page needs.

The static print instances are declared inside ``@media print``, so they start loading
only once print layout asks for them. An export that switches to print media and prints
immediately draws the page before they arrive, and prints the sans in the fallback the
stack names -- the variable face, which is the Type3 condition this whole feature
exists to remove. Two cases carry the risk:

- text in the document, when the faces are still in flight at print time;
- text in an ``@page`` margin box -- KPress's footer -- which sits outside the document
  tree, so its face never enters ``document.fonts.ready`` and its first request would
  land inside ``page.pdf()``, after the page it belongs to is drawn.

Both are measured through the public ``render_pdf`` on the faces the PDF embeds.
Chromium embeds a subset of a face only for glyphs it actually drew with it, so the
presence of the static instance is the assertion that the sans text survived the export
as a font; ``/Type3`` anywhere in the file is the assertion that nothing fell back.

The quote face is here for the other half of the same rule. It replaced a ``local()``
borrowing of the reader's Georgia, which a PDF could never embed, so what a printed page
does with a quotation mark is exactly the thing that used to be wrong.
"""

from __future__ import annotations

import re
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast

import pytest

from devtools.instance_sans import FAMILY, REGULAR_WEIGHT
from devtools.subset_mono import SOURCES as MONO_STYLES
from devtools.subset_mono import MonoStyle
from devtools.subset_quotes import POSTSCRIPT_NAME as QUOTE_FACE
from kpress.format.model import MonoWeight
from kpress.format.pdf import PdfOptions, render_pdf
from kpress.workflow.format import format_document


def _mono_style(name: str) -> MonoStyle:
    """The one `SOURCES` entry with this `mono_weights` name."""
    return next(style for style in MONO_STYLES if style.name == name)


#: The static instance every default KPress page needs in print: the footer margin box
#: names the sans stack at the shared regular weight.
FOOTER_FACE = f"{FAMILY.replace(' ', '')}-{REGULAR_WEIGHT}"

#: The mono face code resolves to, by the PostScript name the subset keeps from
#: upstream (devtools/subset_mono.py renames nothing). Selected by name rather than by
#: position: `SOURCES` is a declaration-ordered tuple and nothing stops a style being
#: inserted ahead of regular, which would silently repoint this constant.
MONO_FACE = f"PlanetaireMonoText-{_mono_style('regular').upstream}"

#: Every face a KPress page is allowed to print with: the two reader faces, the static
#: print sans, the quote subset, and the mono styles the document declared. A denylist
#: of the two the developing machine happens to own passes on a runner that falls back
#: to DejaVu or Liberation instead, so the guard is a subset test against what KPress
#: ships -- anything else in the font list came from the machine.
OWNED_FACE_PREFIXES = (
    "PTSerif",
    f"{FAMILY.replace(' ', '')}",
    QUOTE_FACE,
    "PlanetaireMonoText",
)

#: How long the delaying server holds a static instance back. Long enough that an export
#: which does not wait prints before the face arrives (measured: it prints immediately),
#: short enough to stay well inside the suite's per-test timeout.
_FONT_DELAY_SECONDS = 0.7

_INSTANCE_FILE = re.compile(r"/kpress-print-sans-latin-\d{3}-(?:normal|italic)\.woff2$")
_BASE_FONT = re.compile(rb"/BaseFont\s*/(?:[A-Z]{6}\+)?([A-Za-z0-9\-]+)")
_OBJECT = re.compile(rb"\d+ 0 obj(.*?)endobj", re.DOTALL)
_TYPE0 = re.compile(rb"/Subtype\s*/Type0\b")


def assert_only_owned_faces(fonts: set[str]) -> None:
    """Every face in the PDF is one KPress ships.

    The inverse of a denylist: naming the faces we own catches a fallback to whatever
    mono the exporting machine happens to have, on any platform, rather than only the
    two a macOS developer would see.
    """
    borrowed = [name for name in fonts if not name.startswith(OWNED_FACE_PREFIXES)]
    assert not borrowed, f"faces not shipped by KPress reached the PDF: {sorted(borrowed)}"


def _embedded_fonts(pdf: Path) -> set[str]:
    """Every font the PDF embeds or references, without its subset prefix."""
    return {name.decode() for name in _BASE_FONT.findall(pdf.read_bytes())}


def _type0_fonts(pdf: Path) -> set[str]:
    """The composite fonts the PDF embeds: a real font program, not drawn outlines.

    ``/Type0`` is what an embedded woff2 becomes on the way into a PDF, so the
    distinction this makes is the same one ``/Type3`` makes above -- a font a viewer
    can smooth, select and search, against a page of paths that only looks like text.
    """
    names: set[str] = set()
    for body in _OBJECT.findall(pdf.read_bytes()):
        if not _TYPE0.search(body):
            continue
        found = _BASE_FONT.search(body)
        if found is not None:
            names.add(found.group(1).decode())
    return names


def _formatted_page(tmp_path: Path, markdown: str) -> Path:
    """One document through the local format workflow, as ``kpress export`` renders it."""
    (tmp_path / "src").mkdir(parents=True)
    source = tmp_path / "src" / "doc.md"
    source.write_text(markdown, encoding="utf-8")
    result = format_document(source, output_dir=tmp_path / "out", work_root=tmp_path / ".kpress")
    return next(path for path in result.outputs if path.suffix == ".html")


class _SlowFontHandler(SimpleHTTPRequestHandler):
    """Serve the formatted page's assets, holding the static instances back."""

    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)

    def end_headers(self) -> None:
        # The document is a file:// page, so its font requests carry a null origin.
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_GET(self) -> None:
        if _INSTANCE_FILE.search(self.path):
            time.sleep(_FONT_DELAY_SECONDS)
        super().do_GET()


def _require_chromium() -> None:
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as playwright:
        if not Path(playwright.chromium.executable_path).is_file():
            pytest.skip("No Playwright Chromium available")


def test_page_footer_face_embeds_in_the_exported_pdf(tmp_path: Path) -> None:
    """The footer is the only sans on a serif-only page, so its face proves it printed."""
    _require_chromium()
    html = _formatted_page(
        tmp_path,
        "# Serif only\n\nA paragraph of ordinary prose, all of it in the serif face.\n\n"
        "### One sans heading\n\nAnd a second paragraph after it.\n",
    )
    output = tmp_path / "doc.pdf"

    render_pdf(html, PdfOptions(output=output))

    fonts = _embedded_fonts(output)
    assert FOOTER_FACE in fonts, fonts
    # Nothing on the page reached the PDF as outline paths, which is the whole point of
    # the static set, and the variable face was never drawn from.
    assert b"/Type3" not in output.read_bytes(), fonts
    assert not [name for name in fonts if name.startswith("SourceSans3")], fonts


def test_slow_print_faces_still_embed_in_the_exported_pdf(tmp_path: Path) -> None:
    """Text in the document survives an export that starts before the faces arrive."""
    _require_chromium()
    html = _formatted_page(
        tmp_path,
        "# Print sans smoke\n\n"
        "A paragraph of prose with a note attached to it.[^a]\n\n"
        "[^a]: The footnote body is set in the sans face at the small size.\n",
    )
    handler = partial(_SlowFontHandler, directory=str(html.parent))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        # Same document, assets over the delaying server: a <base> retargets every
        # relative URL the formatted page carries.
        delayed = html.with_name("delayed.html")
        delayed.write_text(
            html.read_text(encoding="utf-8").replace(
                "<head>", f'<head><base href="http://127.0.0.1:{server.server_address[1]}/">', 1
            ),
            encoding="utf-8",
        )
        output = tmp_path / "delayed.pdf"
        render_pdf(delayed, PdfOptions(output=output))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    fonts = _embedded_fonts(output)
    # The footnote and the footer both resolve to the 400 instance; the prose face is
    # there to show the page itself rendered rather than exporting blank.
    assert FOOTER_FACE in fonts, fonts
    assert any(name.startswith("PTSerif") for name in fonts), fonts


def test_code_embeds_the_shipped_mono_face_in_the_exported_pdf(tmp_path: Path) -> None:
    """Printed code comes from the shipped face, not from the exporting machine's mono.

    This is the last role that used to fall through to whatever the renderer had
    installed: the squares explainer PDF that started this work carried 56 KB of the
    build machine's Menlo. Both shapes a reader meets code in are on the page, and the
    face has to arrive as a composite font rather than as outlines.
    """
    _require_chromium()
    html = _formatted_page(
        tmp_path,
        "# Code in print\n\n"
        "A paragraph that mentions `render_page(document, options)` inline.\n\n"
        "```python\n"
        "def measure(face: str) -> int:\n"
        "    return len(face)  # 0123456789\n"
        "```\n",
    )
    output = tmp_path / "code.pdf"

    render_pdf(html, PdfOptions(output=output))

    assert MONO_FACE in _type0_fonts(output), _embedded_fonts(output)
    fonts = _embedded_fonts(output)
    # The prose beside the code printed too, and nothing anywhere fell back to paths.
    assert any(name.startswith("PTSerif") for name in fonts), fonts
    assert b"/Type3" not in output.read_bytes(), fonts
    # Nothing borrowed the exporting machine's own anything.
    assert_only_owned_faces(fonts)


def test_quotation_marks_embed_in_the_exported_pdf(tmp_path: Path) -> None:
    """A printed quotation mark comes from the shipped face, not from the machine."""
    _require_chromium()
    html = _formatted_page(
        tmp_path,
        "# Quotation marks\n\n"
        "She said \u201cthe marks are shipped,\u201d and that\u2019s "
        "\u2018the whole rule\u2019.\n",
    )
    output = tmp_path / "quotes.pdf"

    render_pdf(html, PdfOptions(output=output))

    fonts = _embedded_fonts(output)
    assert QUOTE_FACE in fonts, fonts
    # The letters beside the marks are still the reading face, so the page did print.
    assert any(name.startswith("PTSerif") for name in fonts), fonts


#: Code that reaches all four styles the packaged stylesheets ask for: prose-weight
#: tokens, keywords at 700, a `c1` comment in italic, and a `cp` preprocessor token,
#: which `syntax.css` sets italic AND 700. Python alone never emits `cp`, so a Python
#: fixture leaves bold-italic unreached and the set that omits it looks clean.
_FOUR_STYLE_CODE = (
    "# Every style\n\n"
    "A paragraph that mentions `render_page(document, options)` inline.\n\n"
    "```python\n"
    "def measure(face: str) -> int:\n"
    "    return len(face)  # 0123456789\n"
    "```\n\n"
    "```c\n"
    "#include <stdio.h>\n"
    "int main(void) { return 0; }\n"
    "```\n"
)


def _page_with_mono_weights(tmp_path: Path, weights: tuple[str, ...]) -> Path:
    """One standalone page exported with an explicit `mono_weights` set.

    Through `export_document` rather than `build_site`, for two reasons: it emits the
    relative asset tree a `file://` render can actually resolve, and it is the path
    that carries the mono setting on `KPressExportRequest` -- so this doubles as the
    check that a single-document export can choose its own mono face at all.
    """
    from kpress.models import KPressExportRequest
    from kpress.publish.build import export_document

    source = tmp_path / "doc.md"
    source.write_text(_FOUR_STYLE_CODE, encoding="utf-8")
    destination = tmp_path / "out" / "doc.html"
    export_document(
        KPressExportRequest(
            path=str(source),
            kind="markdown",
            view="document",
            destination=str(destination),
            mono_weights=cast("tuple[MonoWeight, ...]", weights),
        )
    )
    return destination


@pytest.mark.parametrize(
    "weights",
    [
        pytest.param(tuple(style.name for style in MONO_STYLES[:4]), id="default"),
        pytest.param(tuple(style.name for style in MONO_STYLES), id="all-seven"),
    ],
)
def test_no_shipped_mono_set_prints_type3(tmp_path: Path, weights: tuple[str, ...]) -> None:
    """Every set a host may legally declare prints as embedded fonts, never as outlines.

    `/Type3` is a page of drawn paths wearing text's clothes: unsearchable, unselectable
    and unsmoothed. It is what a browser produces when it has to invent a weight, and
    removing it is the whole reason this face is vendored. `_validated_mono_weights`
    refuses the sets that would cause it, so this is the other half of that guarantee --
    the sets it *admits* are measured here rather than argued about.
    """
    _require_chromium()
    html = _page_with_mono_weights(tmp_path, weights)
    output = tmp_path / "code.pdf"

    render_pdf(html, PdfOptions(output=output))

    fonts = _embedded_fonts(output)
    assert b"/Type3" not in output.read_bytes(), fonts
    assert MONO_FACE in _type0_fonts(output), fonts
    # Both italic styles are reachable from this fixture, so both must be real faces.
    assert f"PlanetaireMonoText-{_mono_style('italic').upstream}" in _type0_fonts(output), fonts
    assert f"PlanetaireMonoText-{_mono_style('bold-italic').upstream}" in _type0_fonts(output), (
        fonts
    )
    assert_only_owned_faces(fonts)
