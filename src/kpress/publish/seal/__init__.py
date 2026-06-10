"""Package-asset copy helpers for the KPress static publisher.

The historical asset sealer (HTML/CSS/JS URL rewriter, external fetcher,
offline-tree verifier) is deferred to v2 — see
``packages/kpress/kpress-design.md`` § "Asset sealing: deferred for v1"
and the v1-removal spec at
``docs/project/specs/active/plan-2026-05-21-kpress-remove-sealing-for-v1.md``.

In v1, this subpackage owns only the package-asset graph: KPress's
vendored CSS/JS/fonts and the KaTeX bundle when math is present.
Document-local and external asset URLs are left in the rendered HTML
verbatim and handled by the deploy layer.
"""

from __future__ import annotations

from kpress.publish.seal.copy import copy_katex_assets, copy_package_assets

__all__ = [
    "copy_katex_assets",
    "copy_package_assets",
]
