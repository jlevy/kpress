"""Site map for the wrapped-site example.

The *outer* builder owns routing and navigation, not KPress. Each page names a
Markdown source, the URL it should publish to, and its label in the sidebar nav.
This is the kind of registry a CMS or static-site framework maintains; KPress is
only asked to render each document's body.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    source: str  # Markdown file under content/
    url: str  # site-absolute clean URL (served as <url>/index.html)
    nav_title: str  # label in the sidebar navigation


# Order here is the order shown in the sidebar.
PAGES: tuple[Page, ...] = (
    Page(source="index.md", url="/", nav_title="Home"),
    Page(source="docs/installation.md", url="/docs/installation/", nav_title="Installation"),
    Page(source="docs/configuration.md", url="/docs/configuration/", nav_title="Configuration"),
    Page(source="blog/announcing.md", url="/blog/announcing/", nav_title="Announcement"),
)
