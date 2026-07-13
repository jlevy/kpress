"""Build the KPress static-site example, end to end.

This is the "competent generator" path: ``build_site`` turns the ``content/``
Markdown tree into a complete, self-contained static site. KPress owns the whole
page: layout, theme, assets, and routing.

End to end means source -> built site -> navigable / uploadable:

    python build.py                 # build ./public
    python build.py --serve         # build, then serve it so you can browse it
    python build.py --zip           # build, then package an uploadable .zip
    python build.py /tmp/out        # build into /tmp/out

Or call :func:`build` from your own code / tests.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kpress.publish import BuildExtensions, BuildOptions, BuildReport, build_site
from kpress.publish.optimize import OptimizerResult

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "kpress.yml"

# Reach the shared example runner (serve + package helpers).
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from _runner import package_zip, serve  # noqa: E402  (path set up above)


def build(output_dir: Path | None = None) -> BuildReport:
    """Build the example site and return the publish report.

    ``output_dir`` overrides the ``publish.output_dir`` from ``kpress.yml`` so
    callers (and tests) can build into a scratch directory.
    """

    options = BuildOptions(output_dir=output_dir) if output_dir is not None else None
    return build_site(CONFIG, options, extensions=EXTENSIONS)


class LicenseBannerStage:
    """Demo pipeline stage (extension model, layer E): a host build step run
    BEFORE any built-in compressor — here, stamping a license banner onto each
    published JS asset. Same shape as KPress's own optimizer backends."""

    name = "license-banner"

    def optimize(self, content: str, *, kind: str) -> OptimizerResult:
        if kind != "js" or content.startswith("/*!"):
            return OptimizerResult(content=content, backend=self.name, changed=False)
        banner = "/*! KPress static-site example - demo pipeline stage */\n"
        return OptimizerResult(content=banner + content, backend=self.name, changed=True)


# The ordered pipeline: the demo stage, then the built-in no-op (swap in
# "full" to minify after the banner is applied — order is the point).
EXTENSIONS = BuildExtensions(pipeline=[LicenseBannerStage(), "none"])


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build the KPress static-site example.")
    parser.add_argument("output_dir", nargs="?", help="Where to write the site (default ./public)")
    parser.add_argument("--serve", action="store_true", help="Serve the built site for browsing")
    parser.add_argument(
        "--zip", action="store_true", help="Package the built site as an uploadable .zip"
    )
    parser.add_argument("--port", type=int, default=8000, help="Port for --serve (default 8000)")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    report = build(output_dir)
    destination = output_dir or (HERE / "public")
    print(f"Built {len(report.routes)} pages into {destination}")
    for route, output_path in sorted(report.routes.items()):
        print(f"  {route:<24} -> {output_path}")

    if args.zip:
        archive = package_zip(destination)
        print(f"\nPackaged uploadable archive: {archive}")
    if args.serve:
        serve(destination, port=args.port)
    elif not args.zip:
        print("\nServe it with:  python build.py --serve")
        print(
            "Upload it with: python build.py --zip   (or copy", destination, "to any static host)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
