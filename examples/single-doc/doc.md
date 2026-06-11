# A Single Published Document

This page was published by `examples/single-doc/build.py`: one Markdown file,
one programmatic `KPressConfig`, one `build_site()` call — no YAML file.

## Why this example exists

A Python host calling a Python library should write Python. The typed config
carries everything the YAML form can: chrome slots as plain strings, the
palette, the TOC mode, and widget selection (the settings gear here ships the
theme and reading-font choosers).

## What KPress provides

Typography, theming, the table of contents, tooltips and footnote previews,[^1]
code highlighting, and the asset bundle — all from the one call.

```python
build_site(KPressConfig(...))
```

[^1]: Hover this footnote reference to see the built-in preview behavior.
