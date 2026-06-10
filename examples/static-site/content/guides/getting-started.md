---
title: Getting Started
---
# Getting started

[Home](/) · **[Getting started](/guides/getting-started.html)** ·
[Markdown features](/guides/markdown-features.html) · [API reference](/reference/api/)

Building this site is one function call.
From this directory:

```python
from pathlib import Path

from kpress.publish import build_site

report = build_site(Path("kpress.yml"))
print(report.routes)
```

Or from the command line:

```bash
kpress build kpress.yml
```

Either way the output lands in `public/`, ready to serve with any static host:

```bash
python -m http.server -d public
```

## How URLs Are Derived

| Source file | URL |
| --- | --- |
| `content/index.md` | `/` |
| `content/guides/getting-started.md` | `/guides/getting-started.html` |
| `content/reference/api.md` | `/reference/api/` (overridden) |

The directory layout under `content/` is the routing table.
Drop a Markdown file in, get a page out.
