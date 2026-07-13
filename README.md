# KPress

KPress is a Python library and CLI that turns Markdown into polished HTML documents and
static sites. It owns document rendering, typography, reader interactions, and the build
pipeline while leaving site semantics and deployment to the consuming project.

Version `0.1.0` is an alpha for developers evaluating KPress in real projects.
The document and publishing paths are usable and tested, but public seams may still
change by hard cut before a stable release.

KPress requires Python 3.12 or newer.

## Install and build a site

Install the released package into a project:

```bash
uv add kpress==0.1.0
```

Create this minimal `kpress.yml`:

```yaml
sources:
  - path: content

publish:
  output_dir: public
  asset_mode: hashed
```

Then add a document and build it:

```bash
mkdir -p content
printf '# Hello\n\nBuilt with KPress.\n' > content/index.md
uv run kpress build
python -m http.server 8080 -d public
```

Open `http://127.0.0.1:8080/`. The build writes `public/index.html`, the packaged reader
assets under `public/_kpress/assets/`, and a deterministic build manifest at
`public/_kpress/kpress-manifest.json`.

`hashed` fingerprints KPress-owned CSS and JavaScript for production caching.
It does not fetch, rewrite, or guarantee document-local and external assets.
Use `linked` for readable local asset names and `hosted` when an embedding application
serves KPress assets itself.
Truly self-contained single-file and verified offline output are not part of `0.1.0`.

## Use KPress as a library

File-based sites can call the same publisher used by the CLI:

```python
from kpress.publish import build_site

report = build_site("kpress.yml")
print(report.routes)
```

Python hosts can instead construct a typed `KPressConfig`, render a standalone page with
`kpress.format.render_page`, or render an embeddable fragment with
`kpress.format.render_fragment`.

The three runnable examples cover the supported integration shapes:

- [`examples/static-site/`](examples/static-site/): KPress owns a complete static site.
- [`examples/wrapped-site/`](examples/wrapped-site/): an outer site shell embeds KPress
  fragments and serves the asset closure.
- [`examples/single-doc/`](examples/single-doc/): a typed, programmatic build with no
  YAML config.

See [`examples/README.md`](examples/README.md) for commands and
[`docs/kpress-static-publish.runbook.md`](docs/kpress-static-publish.runbook.md) for the
publisher boundary.

## What ships

- Vendored PT Serif and Source Sans 3, design tokens, light/dark/system modes, print
  CSS, and a no-flash theme bootstrap.
- Progressive reader features: table of contents, footnote and link tooltips, code copy,
  tabs, video placeholders, responsive tables, and KaTeX math with MathML.
- Static discovery and routing, sitemap/robots/redirects, content-hashed package assets,
  optional optimization and precompression, and schema-versioned manifests.
- Typed Python APIs, native ESM browser modules, host-owned chrome slots, runtime
  widget/behavior registries, and sanitized or trusted raw-HTML modes.

## Development and unreleased versions

External evaluators should start with the tagged package.
Projects deliberately dogfooding unreleased work may pin an exact upstream commit or a
maintained fork, but should treat that as a separate, faster-moving consumption path and
record the pin.

```bash
uv sync --all-extras
make lint-check
uv run pytest
```

Architecture and stability contracts live in
[`docs/kpress-design.md`](docs/kpress-design.md).
See [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md), and
[`SUPPLY-CHAIN-SECURITY.md`](SUPPLY-CHAIN-SECURITY.md) before contributing or reporting
a vulnerability. General defects and integration feedback belong in the
[issue tracker](https://github.com/jlevy/kpress/issues).

## Compatibility policy

KPress evolves by hard cuts during the alpha: there are no deprecation shims.
An out-of-date caller should fail loudly rather than appear to work.
The supported surface is pinned in `kpress.contract`; public-name changes update the
contract, docs, tests, goldens, and release notes together.

## License

AGPL-3.0-or-later; see [`LICENSE`](LICENSE). Vendored components and their licenses are
listed in [`NOTICE.md`](NOTICE.md).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
