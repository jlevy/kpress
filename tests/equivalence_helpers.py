"""Reusable dynamic-vs-hashed equivalence harness for KPress.

Compares dynamic zero-build rendering (render_page) against production hashed
publishing (build_site) and asserts that the document surface is structurally
equivalent.  Accepted differences are limited to:

- URL shape (asset prefix, hashed filenames)
- Minification (collapsed whitespace, removed comments)
- Compression (.gz/.br sidecar files)
- Asset loading mechanism (inline vs linked)
- Explicitly documented optional optimizations

The harness normalizes both surfaces to strip these expected differences and
compares the remaining document structure.
"""

from __future__ import annotations

import html as html_module
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from kpress.format import DocumentInput, RenderOptions, render_page
from kpress.format.model import TocMode
from kpress.publish import BuildOptions, build_site

from .golden_helpers import KPRESS_ROOT

# Fixture document directory.
FIXTURE_DOCUMENTS = KPRESS_ROOT / "tests" / "fixtures" / "documents"


@dataclass(frozen=True)
class EquivalenceFixture:
    """A fixture for dynamic-vs-hashed equivalence comparison."""

    name: str
    source_path: Path
    title: str
    include_toc: TocMode = "auto"
    toc_min_headings: int = 4


@dataclass(frozen=True)
class EquivalenceResult:
    """Result of an equivalence comparison."""

    fixture_name: str
    passed: bool
    dynamic_elements: list[str]
    hashed_elements: list[str]
    differences: list[str] = field(default_factory=list)


def discover_fixtures() -> list[EquivalenceFixture]:
    """Discover all fixture documents and return equivalence fixtures."""

    fixtures: list[EquivalenceFixture] = []
    for path in sorted(FIXTURE_DOCUMENTS.glob("*.md")):
        name = path.stem
        title = name.replace("-", " ").title()
        # Rich and semantic fixtures need TOC enabled with low threshold.
        toc: TocMode = "auto"
        toc_min = 4
        if "rich" in name or "semantic" in name:
            toc = "on"
            toc_min = 2
        fixtures.append(
            EquivalenceFixture(
                name=name,
                source_path=path,
                title=title,
                include_toc=toc,
                toc_min_headings=toc_min,
            )
        )
    return fixtures


_LOCAL_ASSET_RE = re.compile(
    r"""
    (?:!\[.*?\]\((?P<md_url>[^)#?\s]+?)(?:\s|[)]))
    |
    (?:src="(?P<src_url>[^"]+)")
    |
    (?:href="(?P<href_url>[^"]+)")
    """,
    re.VERBOSE,
)

_PLACEHOLDER_CONTENT: dict[str, bytes] = {
    ".jpg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00",
    ".jpeg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00",
    ".png": b"\x89PNG\r\n\x1a\n",
    ".gif": b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
    ".svg": b"<svg></svg>",
    ".webp": b"RIFF\x00\x00\x00\x00WEBP",
    ".css": b"/* placeholder */\n",
    ".js": b"// placeholder\n",
}


def _create_placeholder_assets(source_text: str, docs_dir: Path) -> None:
    """Create placeholder files for local asset references in source text."""

    for match in _LOCAL_ASSET_RE.finditer(source_text):
        url = match.group("md_url") or match.group("src_url") or match.group("href_url")
        if not url:
            continue
        # Skip external URLs, anchors, and absolute paths.
        if url.startswith(("http://", "https://", "//", "#", "/", "mailto:")):
            continue
        # Skip fragment-only references.
        if url.startswith("#"):
            continue
        # Strip any query/fragment.
        clean = url.split("?")[0].split("#")[0]
        if not clean:
            continue
        target = docs_dir / clean
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        suffix = target.suffix.lower()
        content = _PLACEHOLDER_CONTENT.get(suffix, b"placeholder")
        target.write_bytes(content)


def _render_dynamic(fixture: EquivalenceFixture) -> str:
    """Render a fixture through the dynamic render_page path."""

    source_text = fixture.source_path.read_text(encoding="utf-8")
    page = render_page(
        DocumentInput(
            title=fixture.title,
            source_text=source_text,
            body_markdown=source_text,
            source_path=str(fixture.source_path),
        ),
        RenderOptions(
            asset_mode="hosted",
            include_toc=fixture.include_toc,
            toc_min_headings=fixture.toc_min_headings,
        ),
    )
    return page.html


def _render_hashed(fixture: EquivalenceFixture, tmp_path: Path) -> str:
    """Render a fixture through the hashed build_site path with inline assets."""

    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    source_text = fixture.source_path.read_text(encoding="utf-8")

    # Use the original fixture filename so build_site derives the same title.
    source_name = fixture.source_path.name
    (docs / source_name).write_text(source_text, encoding="utf-8")

    # Copy sidecar assets from the fixture directory.
    assets_dir = fixture.source_path.parent / "assets"
    if assets_dir.is_dir():
        out_assets = docs / "assets"
        out_assets.mkdir(exist_ok=True)
        for asset in assets_dir.iterdir():
            if asset.is_file():
                (out_assets / asset.name).write_bytes(asset.read_bytes())

    # Create placeholder files for local asset references in the source that
    # do not exist as real fixture sidecar files (e.g., frame.jpg in semantic
    # components).
    _create_placeholder_assets(source_text, docs)

    config = tmp_path / "kpress.yml"
    config.write_text(
        "sources:\n"
        "  - path: docs\n"
        "\n"
        "publish:\n"
        "  output_dir: public\n"
        "\n"
        "format:\n"
        f"  toc: {fixture.include_toc}\n"
        f"  toc_min_headings: {fixture.toc_min_headings}\n",
        encoding="utf-8",
    )

    # `inline` is config-rejected for end users until self-contained
    # (orig-7ehk); the harness selects it programmatically because the
    # equivalence comparison wants fully-embedded CSS/JS text.
    build_site(config, BuildOptions(asset_mode="inline"))

    # The output filename matches the source stem.
    stem = fixture.source_path.stem
    output_name = f"{stem}.html"
    output = tmp_path / "public" / output_name
    if not output.exists():
        # Fall back to index.html for index-named sources.
        output = tmp_path / "public" / "index.html"
    return output.read_text(encoding="utf-8")


def normalize_document_surface(html: str) -> str:
    """Normalize an HTML document surface to remove expected mode differences.

    Strips:
    - <head> content (asset loading, meta tags differ between modes)
    - Inline <style> and <script> blocks with kpress-asset markers
    - Asset URL prefixes and content hashes in remaining references
    - Whitespace differences (collapse to single spaces)
    - The theme bootstrap script
    - The diagnostics JSON script
    """

    # Remove <head> entirely (contains asset tags, meta, title).
    html = re.sub(r"<head>.*?</head>", "", html, flags=re.DOTALL)

    # Remove inline style blocks (present in inline mode).
    html = re.sub(
        r'<style\s+data-kpress-asset="[^"]*">.*?</style>',
        "",
        html,
        flags=re.DOTALL,
    )

    # Remove inline script blocks with kpress-asset markers.
    html = re.sub(
        r'<script\s+type="module"\s+data-kpress-asset="[^"]*">.*?</script>',
        "",
        html,
        flags=re.DOTALL,
    )

    # Remove the diagnostics and page-model JSON blocks from the *surface*
    # comparison: the page model's `route` legitimately differs between
    # dynamic and published renders. The page model itself is compared
    # structurally (route normalized) via `page_model_differences`.
    html = re.sub(
        r'<script\s+type="application/json"\s+id="kpress-(diagnostics|page-model)">.*?</script>',
        "",
        html,
        flags=re.DOTALL,
    )

    # Remove the theme bootstrap script.
    html = re.sub(r"<script>\s*\(\(\)\s*=>\s*\{.*?\}\)\(\);\s*</script>", "", html, flags=re.DOTALL)

    # Normalize asset URLs: strip prefix variations and hashes.
    html = re.sub(r"/_kpress/assets/", "/assets/", html)
    html = re.sub(r"/kpress-static/", "/assets/", html)
    html = re.sub(r"\.\./fonts/", "/assets/fonts/", html)
    # Strip content hashes from filenames (pattern: name.16hexchars.ext).
    html = re.sub(r"\.[0-9a-f]{16}(\.\w+)", r"\1", html)

    # Normalize hashed asset paths.
    html = re.sub(r"/assets/hashed/[0-9a-f]{16}-", "/assets/hashed/", html)

    # Collapse whitespace.
    html = re.sub(r"\s+", " ", html).strip()

    return html


_PAGE_MODEL_RE = re.compile(
    r'<script\s+type="application/json"\s+id="kpress-page-model">(.*?)</script>',
    re.DOTALL,
)


def extract_page_model(html: str) -> dict[str, object]:
    """Parse the #kpress-page-model JSON block out of a rendered page."""

    match = _PAGE_MODEL_RE.search(html)
    if match is None:
        raise AssertionError("page has no #kpress-page-model block")
    return cast("dict[str, object]", json.loads(match.group(1)))


def page_model_differences(dynamic_html: str, hashed_html: str) -> list[str]:
    """Structurally compare the page models of two rendered pages.

    Only `route` is genuinely mode-variant (a published page has a site
    route; a dynamic render does not), so it is normalized away; every other
    field must match exactly — this is the published-data contract widgets
    compute from, and a parity break here is a real bug even when the
    visible document surface still matches.
    """

    dynamic_model = extract_page_model(dynamic_html)
    hashed_model = extract_page_model(hashed_html)
    dynamic_model["route"] = ""
    hashed_model["route"] = ""
    differences: list[str] = []
    for key in sorted(set(dynamic_model) | set(hashed_model)):
        if dynamic_model.get(key) != hashed_model.get(key):
            differences.append(
                f"page model {key!r}: dynamic={dynamic_model.get(key)!r} "
                f"hashed={hashed_model.get(key)!r}"
            )
    return differences


def extract_document_elements(html: str) -> list[str]:
    """Extract structural document elements from normalized HTML.

    Returns a sorted list of structural markers: headings, paragraphs, lists,
    tables, code blocks, semantic containers, and other content elements.
    """

    elements: list[str] = []

    # Extract headings.
    for match in re.finditer(r"<h([1-6])\s+id=\"([^\"]+)\"[^>]*>(.*?)</h\1>", html):
        level, id_val, text = match.groups()
        clean_text = re.sub(r"<[^>]+>", "", text).strip()
        elements.append(f"h{level}#{id_val}:{clean_text}")

    # Extract article/section markers.
    for match in re.finditer(r'<article\s+class="([^"]*)"', html):
        elements.append(f"article:{match.group(1)}")

    # Extract semantic containers (kpress-specific classes).
    for match in re.finditer(r'<(?:div|section|aside|nav)\s+class="(kpress-[^"]*)"', html):
        elements.append(f"container:{match.group(1)}")

    # Extract list items.
    for match in re.finditer(r"<li[^>]*>(.*?)</li>", html, re.DOTALL):
        text = re.sub(r"<[^>]+>", "", match.group(1)).strip()[:80]
        if text:
            elements.append(f"li:{text}")

    # Extract table cells.
    for match in re.finditer(r"<t[hd][^>]*>(.*?)</t[hd]>", html, re.DOTALL):
        text = re.sub(r"<[^>]+>", "", match.group(1)).strip()[:40]
        if text:
            elements.append(f"td:{text}")

    # Extract code blocks.
    for match in re.finditer(r'<code\s+class="language-(\w+)"', html):
        elements.append(f"code:{match.group(1)}")

    # Extract footnote references.
    for _match in re.finditer(r'class="footnote-ref"', html):
        elements.append("footnote-ref")

    # Extract footnote definitions.
    for match in re.finditer(r'id="fn-([^"]+)"', html):
        elements.append(f"footnote-def:{match.group(1)}")

    return sorted(elements)


def assert_equivalence(
    fixture: EquivalenceFixture,
    tmp_path: Path,
) -> EquivalenceResult:
    """Run the full equivalence comparison for a fixture.

    Returns a result with details; raises AssertionError on structural mismatch.
    """

    dynamic_html = _render_dynamic(fixture)
    hashed_html = _render_hashed(fixture, tmp_path)

    dynamic_normalized = normalize_document_surface(dynamic_html)
    hashed_normalized = normalize_document_surface(hashed_html)

    dynamic_elements = extract_document_elements(dynamic_normalized)
    hashed_elements = extract_document_elements(hashed_normalized)

    differences: list[str] = []

    # Check element-level structural equivalence.
    dynamic_set = set(dynamic_elements)
    hashed_set = set(hashed_elements)
    only_dynamic = sorted(dynamic_set - hashed_set)
    only_hashed = sorted(hashed_set - dynamic_set)

    if only_dynamic:
        differences.append(f"only in dynamic: {only_dynamic}")
    if only_hashed:
        differences.append(f"only in hashed: {only_hashed}")

    # The page model is stripped from the surface comparison above; compare it
    # structurally here so published-data parity breaks fail too.
    differences.extend(page_model_differences(dynamic_html, hashed_html))

    result = EquivalenceResult(
        fixture_name=fixture.name,
        passed=not differences,
        dynamic_elements=dynamic_elements,
        hashed_elements=hashed_elements,
        differences=differences,
    )

    if differences:
        detail = "\n".join(differences)
        msg = f"Equivalence mismatch for {fixture.name}:\n{detail}"
        raise AssertionError(msg)

    return result


def assert_content_equivalence(
    fixture: EquivalenceFixture,
    tmp_path: Path,
) -> EquivalenceResult:
    """Assert normalized text content is equivalent between modes.

    Beyond structural elements, this checks that the visible text content
    (stripped of all tags) matches between dynamic and hashed output.
    """

    dynamic_html = _render_dynamic(fixture)
    hashed_html = _render_hashed(fixture, tmp_path)

    dynamic_normalized = normalize_document_surface(dynamic_html)
    hashed_normalized = normalize_document_surface(hashed_html)

    def extract_visible_text(normalized_html: str) -> str:
        text = re.sub(r"<[^>]+>", " ", normalized_html)
        # Decode HTML entities so &#x0002B; == + and &quot; == ".
        text = html_module.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    dynamic_text = extract_visible_text(dynamic_normalized)
    hashed_text = extract_visible_text(hashed_normalized)

    differences: list[str] = []
    if dynamic_text != hashed_text:
        # Find specific differences.
        dynamic_words = dynamic_text.split()
        hashed_words = hashed_text.split()
        only_dynamic = set(dynamic_words) - set(hashed_words)
        only_hashed = set(hashed_words) - set(dynamic_words)
        if only_dynamic:
            differences.append(f"text only in dynamic: {sorted(only_dynamic)[:10]}")
        if only_hashed:
            differences.append(f"text only in hashed: {sorted(only_hashed)[:10]}")

    dynamic_elements = extract_document_elements(dynamic_normalized)
    hashed_elements = extract_document_elements(hashed_normalized)

    result = EquivalenceResult(
        fixture_name=fixture.name,
        passed=not differences,
        dynamic_elements=dynamic_elements,
        hashed_elements=hashed_elements,
        differences=differences,
    )

    if differences:
        detail = "\n".join(differences)
        msg = f"Content equivalence mismatch for {fixture.name}:\n{detail}"
        raise AssertionError(msg)

    return result


def build_readable_tree(
    sources: dict[str, str],
    tmp_path: Path,
    *,
    toc: TocMode = "auto",
    toc_min_headings: int = 4,
) -> Path:
    """Build a site in readable mode (linked assets, no precompression)."""

    site = tmp_path / "readable-site"
    docs = site / "docs"
    docs.mkdir(parents=True)
    for name, content in sources.items():
        (docs / name).write_text(content, encoding="utf-8")

    config = site / "kpress.yml"
    config.write_text(
        "sources:\n"
        "  - path: docs\n"
        "\n"
        "publish:\n"
        "  output_dir: public\n"
        "  asset_mode: linked\n"
        "\n"
        "format:\n"
        f"  toc: {toc}\n"
        f"  toc_min_headings: {toc_min_headings}\n",
        encoding="utf-8",
    )

    build_site(config)
    return site / "public"


def build_hashed_tree(
    sources: dict[str, str],
    tmp_path: Path,
    *,
    toc: TocMode = "auto",
    toc_min_headings: int = 4,
) -> Path:
    """Build a site in production mode (hashed package assets, gzip precompression).

    Historical name retained for the readable-vs-hashed golden suite; the
    actual asset-sealing pass is deferred to v2 (see
    ``docs/kpress-design.md`` § "Asset sealing: deferred for
    v1"). Today this exercises the readable→production package-asset
    shape: hashed paths plus gzip sidecars.
    """

    site = tmp_path / "hashed-site"
    docs = site / "docs"
    docs.mkdir(parents=True)
    for name, content in sources.items():
        (docs / name).write_text(content, encoding="utf-8")

    config = site / "kpress.yml"
    config.write_text(
        "sources:\n"
        "  - path: docs\n"
        "\n"
        "publish:\n"
        "  output_dir: public\n"
        "  asset_mode: hashed\n"
        "\n"
        "optimizer:\n"
        "  precompress: [gzip]\n"
        "\n"
        "format:\n"
        f"  toc: {toc}\n"
        f"  toc_min_headings: {toc_min_headings}\n",
        encoding="utf-8",
    )

    build_site(config, BuildOptions(asset_mode="hashed", precompress=["gzip"]))
    return site / "public"


def readable_vs_hashed_file_categories(
    readable_files: Sequence[str],
    hashed_files: Sequence[str],
) -> dict[str, list[str]]:
    """Categorize file differences between readable and hashed output trees.

    Returns a dict with keys:
    - shared: files present in both (ignoring hashes)
    - readable_only: files only in readable
    - hashed_only: files only in hashed (hashes, compression, etc.)
    - hashed: hashed files that are hash-renamed versions of readable files
    - compressed: hashed .gz/.br sidecar files
    """

    def normalize_name(name: str) -> str:
        return re.sub(r"\.[0-9a-f]{16}(\.\w+)", r"\1", name)

    readable_set = set(readable_files)
    hashed_set = set(hashed_files)

    readable_normalized = {normalize_name(f): f for f in readable_files}
    hashed_normalized = {normalize_name(f): f for f in hashed_files}

    shared_keys = set(readable_normalized) & set(hashed_normalized)
    shared = sorted(shared_keys)

    readable_only = sorted(f for f in readable_set if normalize_name(f) not in hashed_normalized)
    hashed_only = sorted(f for f in hashed_set if normalize_name(f) not in readable_normalized)

    hashed = sorted(
        f for f in hashed_set if f not in readable_set and normalize_name(f) in readable_normalized
    )
    compressed = sorted(f for f in hashed_set if f.endswith((".gz", ".br")))

    return {
        "shared": shared,
        "readable_only": readable_only,
        "hashed_only": hashed_only,
        "hashed": hashed,
        "compressed": compressed,
    }
