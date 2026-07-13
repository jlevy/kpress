# KPress Static Publish Runbook

KPress owns the build through a correct output directory: discovery, routes, rendering,
KPress-owned assets, sitemap/robots/redirects, optimization, precompression, and the
build manifest. The consuming project owns deployment, credentials, cache headers, and
rollout policy. KPress intentionally has no deploy command.

## Build workflow

```bash
kpress init
kpress build
kpress doctor --profile optimize --allow-network
kpress build --asset-mode hashed --optimizer full --precompress gzip
kpress doctor --config kpress.yml
kpress clean
```

A representative config is:

```yaml
site:
  base_url: https://example.com
  header_html_file: _includes/header.html
  footer_html: '<p>Published with KPress</p>'
  head_extra_html: '<link rel="icon" href="/favicon.svg">'

sources:
  - path: content
    include: ["**/*.md"]
    exclude: ["public/**", ".kpress/**"]
    static: ["favicon.svg", "img/**/*.png"]

publish:
  output_dir: public
  asset_mode: hashed

optimizer:
  mode: none
  precompress: []
```

`site.base_url` is required to emit `sitemap.xml` and advertise it from `robots.txt`.
Without it, KPress still builds a usable local site and omits the sitemap.

## Asset modes

| Mode | Use |
| --- | --- |
| `hosted` | An embedding application serves package assets at its own URL prefix. |
| `linked` | Local review with stable, readable package-asset names. |
| `hashed` | Production multi-file hosting with content-hashed KPress assets. |

These modes shape KPress-owned assets only.
Document-relative files and external URLs remain the consuming project’s responsibility.
`hashed` is not an offline-verification or external-asset-fetching guarantee.
`inline` is rejected for site builds until the reader modules and fonts can form a
genuinely self-contained file.

The optional `full` optimizer needs Node with npm.
Bootstrap its reviewed, locked toolchain once with
`kpress doctor --profile optimize --allow-network`; builds never fetch implicitly.
Brotli needs `kpress[optimize]`. Selecting a missing toolchain is a hard error; KPress
never silently downgrades the build.

## Wrap KPress in a site pipeline

Generate site-owned Markdown before calling KPress, then deploy the complete output
directory with the site’s tooling:

```makefile
KPRESS := uv run kpress

build:
	python scripts/generate_pages.py
	$(KPRESS) build

clean:
	$(KPRESS) clean
```

For Python-only orchestration, construct `KPressConfig` and pass a
`BuildExtensions.pipeline`. Built-in stage names are `none` and `full`; custom stages
use their own unprefixed names.

## Verify the result

- Serve the complete output directory over HTTP and crawl every route and asset.
- Inspect `_kpress/kpress-manifest.json`. Its `pipeline` records configured stages; each
  file’s `applied_pipeline` records the stages that changed that file.
- Confirm content-local assets were copied through `sources[].static` or another
  site-owned step.
- Run `kpress doctor --config kpress.yml` in CI before a build that requests optional
  capabilities.
- Exercise the tagged wheel outside the source checkout; the clean-room package test
  does this for KPress itself.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
