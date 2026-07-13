"""Package-asset copy helpers for the KPress static publisher.

Verified external-asset publishing (HTML/CSS/JS URL rewriting, external fetch,
and offline-tree verification) is deferred to v2; see
``docs/kpress-design.md`` § "Asset sealing: deferred for v1" and ``kpr-xsog``.

In v1, this subpackage owns only the package-asset graph: KPress's
vendored CSS/JS/fonts and the KaTeX bundle when math is present.
Document-local and external asset URLs are left in the rendered HTML
verbatim and handled by the deploy layer.
"""

from __future__ import annotations

from kpress.publish.assets.copy import copy_katex_assets, copy_package_assets

__all__ = [
    "copy_katex_assets",
    "copy_package_assets",
]
