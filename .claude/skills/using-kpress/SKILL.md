---
name: using-kpress
description: Integrate kpress into a host site or publishing pipeline using its typed Python API, CSS-variable and data-attribute design seams, extension hooks, templates, and runtime behaviors. Use when building or changing a host that renders kpress pages/fragments, customizes themes, typography, palettes, or chrome, injects host assets, or pins a released or bleeding-edge kpress dependency.
---
# Using kpress

Use kpress as a neutral Markdown-to-HTML library and static publisher.
Keep site semantics, content preprocessing, navigation, and deployment in the host.

## Choose a consumption mode

- **Released dependency:** Install an exact tagged version from PyPI for reproducible
  external projects.
- **Bleeding-edge dogfood:** Pin an exact git commit from upstream or a maintained fork
  when a host is developing new kpress capabilities ahead of the next release.

Test both modes when maintaining kpress.
A source pin must remain reproducible; never depend on an unpinned branch name in
production.

## Configure through the typed API

Build sites with `KPressConfig`, `FormatConfig`, `PublishConfig`, and `build_site` from
`kpress.publish`. Use YAML only when the application is deliberately exposing a
file-based configuration surface.

Keep host concepts outside kpress configuration.
Use the documented extension seams for ordered build-pipeline stages, tree transforms,
page transforms, chrome slots, admitted custom tags/attributes, and widget
configuration.

## Customize through public seams

- Override documented `--kpress-*` custom properties; do not copy internal CSS.
- Drive theme, palette, and font state through documented `data-kpress-*` attributes.
- Import only JavaScript exports pinned by the public contract.
- Treat unlisted Python names, CSS tokens, selectors, and JavaScript exports as private.

kpress stamps resolved theme/palette state on both `<html>` and the `.kpress` article.
Runtime host controls should update the root attribute and only mirror the article
attribute when the documented cascade does not propagate that setting.
A stale article attribute can shadow root state.

## Keep markup in templates

Do not assemble HTML, CSS, or JavaScript in Python string literals.
Put generated markup in template or asset files and keep Python responsible for
orchestration and data.

When using Jinja directly, configure autoescaping and strict undefined values.
Mark trusted pre-rendered markup explicitly; escape ordinary data by default.

## Typography

Prefer the pinned host font hooks when replacing the default families.
Override related weight tokens when the replacement face does not support the same
variable-font axis.

Use root-absolute URLs for webfonts injected into pages at different route depths, and
ensure the host copies those files into the published tree.
Verify actual computed families in a browser; a declared `@font-face` does not prove
that the page uses it.

## Validate integrations

For a released dependency, test installation and the documented quickstart in a clean
project outside the source checkout.
For a source pin, run the same host suite against the exact commit.

For visual or runtime changes, check light, dark, and custom palettes; narrow and wide
layouts; print; browser console/network failures; and the host’s injected behaviors.
Run kpress’s public-contract tests whenever a host begins consuming a new seam.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
