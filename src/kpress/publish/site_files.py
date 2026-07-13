"""Static site support files: sitemap, robots, and redirects."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from xml.sax.saxutils import escape

from kpress.output import write_text_atomic


def _absolute(base_url: str, route: str) -> str:
    if not base_url:
        return route
    return base_url.rstrip("/") + "/" + route.lstrip("/")


def _redirect_line(rule: Mapping[str, object]) -> str | None:
    source = str(rule.get("from", "")).strip()
    target = str(rule.get("to", "")).strip()
    if not source or not target:
        return None
    status = rule.get("status", 301)
    return f"{source} {target} {status}"


def write_site_files(
    output_dir: Path,
    routes: Mapping[str, str],
    *,
    base_url: str = "",
    lastmods: Mapping[str, str] | None = None,
    redirects: Sequence[Mapping[str, object]] | None = None,
) -> list[Path]:
    """Write sitemap, robots, and optional redirects files."""

    written: list[Path] = []
    lastmods = lastmods or {}

    if base_url:
        entries: list[str] = []
        for route in sorted(routes):
            loc = escape(_absolute(base_url, route))
            lastmod = lastmods.get(route)
            if lastmod:
                entries.append(f"<url><loc>{loc}</loc><lastmod>{escape(lastmod)}</lastmod></url>")
            else:
                entries.append(f"<url><loc>{loc}</loc></url>")
        sitemap = output_dir / "sitemap.xml"
        write_text_atomic(
            sitemap,
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"{''.join(entries)}</urlset>\n",
        )
        written.append(sitemap)

    robots = output_dir / "robots.txt"
    robots_text = "User-agent: *\nAllow: /\n"
    if base_url:
        robots_text += f"Sitemap: {_absolute(base_url, '/sitemap.xml')}\n"
    write_text_atomic(robots, robots_text)
    written.append(robots)

    if redirects:
        lines = [line for rule in redirects if (line := _redirect_line(rule)) is not None]
        if lines:
            redirects_file = output_dir / "_redirects"
            write_text_atomic(redirects_file, "\n".join(lines) + "\n")
            written.append(redirects_file)

    return written
