# KPress

KPress is a Python library and CLI that turns Markdown into polished HTML documents and
static sites. It owns document rendering, typography, reader interactions, and the build
pipeline while leaving site semantics and deployment to the consuming project.

KPress `0.2.3` is an alpha for developers evaluating it in real projects.
The document and publishing paths are usable and tested, but public seams may change by
hard cut before a stable release.

KPress requires Python 3.12 or newer.
KPress `0.2.3` supports macOS and Linux; native Windows support is tracked for a later
alpha (`kpr-isp2`).

## Install and Build a Site

Install the released package into a project:

```bash
uv add kpress==0.2.3
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
KPress copies eligible project-local media without rewriting its authored URLs and does
not fetch or verify external assets or seal a complete asset graph.
Use `linked` for readable local asset names and `hosted` when an embedding application
serves KPress assets itself.
Truly self-contained single-file and verified offline output are not part of `0.2.3`.

## Use KPress as a Library

File-based sites can call the same publisher used by the CLI:

```python
from kpress.publish import build_site

report = build_site("kpress.yml")
print(report.routes)
```

Python hosts can instead construct a typed `KPressConfig`, render a standalone page with
`kpress.format.render_page`, or render an embeddable fragment with
`kpress.format.render_fragment`. Each render returns a typed, complete asset manifest;
hosts can materialize its package closure with
`kpress.format.materialize_package_assets` and emit tags only for its browser entry
points.

The three runnable examples cover the supported integration shapes:

- [`examples/static-site/`](examples/static-site/): KPress owns a complete static site.
- [`examples/wrapped-site/`](examples/wrapped-site/): an outer site shell embeds KPress
  fragments and serves the asset closure.
- [`examples/single-doc/`](examples/single-doc/): a typed, programmatic build with no
  YAML config.

See [`examples/README.md`](examples/README.md) for commands and
[`docs/kpress-static-publish.runbook.md`](docs/kpress-static-publish.runbook.md) for the
publisher boundary.

## What Ships

- Vendored PT Serif and Source Sans 3, design tokens, light/dark/system modes, print
  CSS, and a no-flash theme bootstrap.
- Progressive reader features: table of contents, footnote and link tooltips, code copy,
  tabs, video placeholders, responsive tables, and KaTeX math with MathML.
- Static discovery and routing, sitemap/robots/redirects, content-hashed package assets,
  optional optimization and precompression, and schema-versioned manifests.
- Typed Python APIs, native ESM browser modules, host-owned chrome slots, runtime
  widget/behavior registries, and sanitized or trusted raw-HTML modes.

## Documentation

[`docs/README.md`](docs/README.md) is the documentation index.
It links the architecture and public-contract reference, installation and development
guides, publishing guidance, validation runbooks, and release notes.

## Development and Unreleased Versions

External evaluators should start with the tagged package.
Projects deliberately dogfooding unreleased work may pin an exact upstream commit or a
maintained fork, but should treat that as a separate, faster-moving consumption path and
record the pin.

```bash
make install
make verify
```

Architecture and stability contracts live in
[`docs/kpress-design.md`](docs/kpress-design.md).
Current capability status, release gates, and the prioritized public backlog live in
[`TODO.md`](TODO.md).
See [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md), and
[`SUPPLY-CHAIN-SECURITY.md`](SUPPLY-CHAIN-SECURITY.md) before contributing or reporting
a vulnerability. General defects and integration feedback belong in the
[issue tracker](https://github.com/jlevy/kpress/issues).

## Compatibility Policy

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
