---
title: API Reference
# Override the derived URL. Without this the page would publish to
# /reference/api.html; instead it publishes to the clean directory URL
# /reference/api/ (served as /reference/api/index.html).
public_path: /reference/api/
---
# API reference

[Home](/) · [Getting started](/guides/getting-started.html) ·
[Markdown features](/guides/markdown-features.html) ·
**[API reference](/reference/api/)**

The two functions this example relies on:

## `build_site(config_path, options=None) -> BuildReport`

Reads a `kpress.yml`, discovers every Markdown source, and writes a complete static site
to the configured `output_dir`. Returns a `BuildReport` whose `routes` maps each public
URL to its output file.

## `BuildOptions`

Per-build overrides that take precedence over `kpress.yml`:

| Field | Purpose |
| --- | --- |
| `output_dir` | Where to write the site (overrides config) |
| `asset_mode` | `hashed`, `linked`, `inline`, or `sealed` |
| `optimizer` | `none`, `safe`, or `full` |
| `precompress` | List of encodings to pre-generate, e.g. `[gzip]` |

See the package README for the full publishing contract.
