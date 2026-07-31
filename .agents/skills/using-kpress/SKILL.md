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

Rendered fragments are theme-agnostic: kpress bakes no theme or palette attributes on
the article (standalone pages stamp `<html>` only).
An embedding host stamps `data-kpress-resolved-theme` (and optionally
`data-kpress-palette`) on one chosen scope and updates it on toggle.
Fragment manifests omit `theme.js` and page-default widgets; set
`include_theme_resolver=True` only when kpress should own root theme state, persistence,
and OS-theme tracking.
The explicit `asset_policy="all"` includes the resolver by definition; use `auto` or
`none` for host-owned fragments.
Explicit settings controls remain host-safe: handle their `theme:request`, apply host
state, then emit `theme:change`. An element-level attribute deliberately wins over an
ancestor scope (a stamped element is a coherent theme island); body-portaled tooltips
escape non-`:root` wrapper scopes, so wrapper-scoped hosts stamp `:root` too.

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

Size the document through the one base knob: set `--kpress-host-font-size-base` (any
length, e.g. `17px`) once on `:root` and every kpress font size, bullet, and label
scales proportionally, independent of the browser root font size.
Never scale by overriding ramp tokens; override a public ramp/label/bullet token only
for a deliberate design divergence from its derived ratio (e.g. aligning mono or label
sizes with host chrome).
The `:root` hook also reaches body-appended tooltips; a `.kpress`-scoped override does
not, and a redeclared base also overrides kpress’s print re-rooting.

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
