"""Shared end-to-end helpers for the KPress examples.

The examples don't stop at compiling: these helpers take a built site directory
all the way to a *navigable* local server and an *uploadable* archive, so each
example's ``build.py`` can go source -> built site -> browse / ship in one run.
"""

from __future__ import annotations

import functools
import shutil
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def package_zip(site_dir: Path, archive: Path | None = None) -> Path:
    """Zip a built site into an uploadable archive and return its path.

    The resulting ``.zip`` is exactly what you would drag into a static host
    (object storage, Netlify drop, GitHub Pages artifact, ...).
    """

    site_dir = Path(site_dir)
    base = archive.with_suffix("") if archive else site_dir.parent / f"{site_dir.name}-site"
    shutil.make_archive(str(base), "zip", root_dir=str(site_dir))
    return base.with_name(base.name + ".zip")


def serve(site_dir: Path, port: int = 8000) -> None:
    """Serve a built site locally so it can be navigated in a browser.

    Pages link with site-absolute URLs and directory routes resolve to their
    ``index.html``, so the served site behaves like it would on a static host.
    Blocks until interrupted.
    """

    site_dir = Path(site_dir)
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(site_dir))
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    bound_port = httpd.server_address[1]
    print(f"Serving {site_dir} at http://127.0.0.1:{bound_port}/  (Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()
