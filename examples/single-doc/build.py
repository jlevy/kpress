"""Publish ONE Markdown document as a polished static page — the library-call path.

This is the exemplary *programmatic* KPress integration: no ``kpress.yml``, no
YAML strings, no slot files. The host constructs a typed :class:`KPressConfig`
in Python — chrome slots are plain strings, widget selection is a dict — and
calls :func:`build_site` with it. (Production site builders follow the same
pattern.)

The only host-side packaging step is staging: the source document is copied to
``index.md`` (so it publishes at the site root) with a frontmatter title
injected as a JSON-escaped scalar (valid YAML, injection-safe). That staging is
deliberately the host's job — KPress owns the document layer, not the workflow.

    python build.py                 # build ./public
    python build.py --serve         # build, then serve it so you can browse it
    python build.py /tmp/out        # build into /tmp/out
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from kpress.publish import (
    BuildReport,
    FormatConfig,
    KPressConfig,
    PublishConfig,
    SourceConfig,
    build_site,
)

HERE = Path(__file__).resolve().parent
DOC = HERE / "doc.md"
TITLE = "A Single Published Document"

# Reach the shared example runner (serve helper).
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from _runner import serve  # noqa: E402  (path set up above)


def build(output_dir: Path | None = None) -> BuildReport:
    """Publish ``doc.md`` into ``output_dir`` (default ``./public``)."""

    out = (output_dir or HERE / "public").resolve()
    with tempfile.TemporaryDirectory() as tmp:
        # Host packaging: stage the doc as index.md so it lands at the site
        # root, with the title as injection-safe frontmatter.
        content = Path(tmp) / "content"
        content.mkdir()
        (content / "index.md").write_text(
            f"---\ntitle: {json.dumps(TITLE, ensure_ascii=False)}\n---\n\n{DOC.read_text(encoding='utf-8')}",
            encoding="utf-8",
        )
        return build_site(
            KPressConfig(
                # Anchor for the staged content's relative media (no config file).
                base_dir=Path(tmp),
                # Chrome slots are plain strings — no YAML, no *_file dance.
                header_html='<a href="/">&larr; back home</a>',
                head_extra_html="<style>:root { --kpress-host-settings-inset-block: 1rem; }</style>",
                sources=[SourceConfig(path=content)],
                format=FormatConfig(
                    toc="on",
                    show_frontmatter=False,
                    palette="warm",
                    # Widget selection: the settings gear with two choosers.
                    widgets={"settings": {"choosers": ["theme", "reading-font"]}},
                ),
                publish=PublishConfig(output_dir=out),
            )
        )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Publish the single-doc KPress example.")
    parser.add_argument("output_dir", nargs="?", help="Where to write the site (default ./public)")
    parser.add_argument("--serve", action="store_true", help="Serve the built site for browsing")
    parser.add_argument("--port", type=int, default=8000, help="Port for --serve (default 8000)")
    args = parser.parse_args(argv)

    out = Path(args.output_dir).resolve() if args.output_dir else None
    report = build(out)
    print(f"built {len(report.files)} files -> {report.output_dir}")
    if args.serve:
        serve(report.output_dir, args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
