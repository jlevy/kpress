# KPress Static Publish (SSG) Runbook

How to build and ship a static site with kpress, and where kpress’s responsibility ends.

## Ownership

kpress owns everything up to a correct output directory: discovery, routes, rendering,
assets, sitemap/robots/redirects, optimization, precompression, and the build manifest.
**Deployment and sync are owned by the site repository’s pipeline**, not by kpress: the
deploy target (Render, Pages, rsync to a host) and its credentials, cache headers, and
rollout policy live in the site repo (Makefile, CI job, `render.yaml`). kpress never
ships a deploy command.

## The workflow

```bash
kpress init                  # once: starter kpress.yml
kpress build                 # render to publish.output_dir (default public/)
kpress build --asset-mode sealed --optimizer full --precompress br
kpress clean                 # remove output dir (manifest-guarded) + .kpress/
kpress doctor --config kpress.yml   # verify required capabilities before CI use
```

Pick the asset mode by hosting model:

| Mode | Use when |
| --- | --- |
| `hosted` | a long-running host serves package assets itself |
| `linked` | local preview; stable, readable asset names |
| `hashed` | production hosting with far-future caching (import map resolves JS) |
| `sealed` | fully offline artifact; no external loads at page load |

`inline` (single-file) is rejected until it is truly self-contained; use `sealed`.

The optimizer (`full`, html-minifier-next) and Brotli precompression need their
toolchains present; selection without a toolchain is a hard error, never a silent
downgrade. `kpress doctor` preflights both.

## Pipelines wrap kpress

Generated content (directory pages from data files, API-derived markdown) is produced by
site-owned scripts *before* `kpress build`; kpress only sees Markdown sources plus
`sources[].static` passthrough files.
The canonical pattern:

```makefile
KPRESS := uvx kpress@0.0.1   # pin the version

build:
	python scripts/generate_pages.py
	$(KPRESS) build

clean:
	$(KPRESS) clean
```

CI should run the same `make build` on every PR so site breakage is caught before
deploy; the deploy step then publishes `public/` with the site’s own tooling.

## Verifying a build

- The build manifest (`_kpress/kpress-manifest.json`) lists every emitted file with
  content hashes; rebuilds purge previously-manifested files first, so the output is a
  pure function of current inputs.
- `tests/test_optimized_build_assets.py` pins that optimized hashed/sealed builds emit
  resolvable asset references (import map included); `tests/test_clean_room_wheel.py`
  pins that all of this works from the installed wheel outside the repo.
- For a manual offline check, build `--asset-mode sealed`, open the output over
  `file://` or a local server with the network disabled, and confirm reader features
  (TOC, tooltips, code copy) work.

<!-- This document follows std-doc-guidelines.md.
Review guidelines before editing.
-->
