# KPress Notices

KPress’s own license is AGPL-3.0-or-later, declared in `LICENSE`. This file records the
third-party components KPress vendors or bundles, each under its own license,
independent of KPress’s license.

## Vendored and Bundled Components

- **Lucide Icons** v1.17.0
  ([ISC and Feather MIT license](src/kpress/licenses/lucide.txt),
  [lucide.dev](https://lucide.dev)). Glyph geometry vendored as an SVG sprite in
  `src/kpress/format/static/icons/icons.svg`.
- **KaTeX** v0.16.45 ([MIT License](src/kpress/licenses/katex.txt),
  [katex.org](https://katex.org)). JS bundles, stylesheet, and woff2 math fonts vendored
  under `src/kpress/format/static/katex/`.
- **PT Serif** ([SIL Open Font License 1.1](src/kpress/licenses/pt-serif.txt),
  ParaType). woff2 subsets vendored under `src/kpress/format/static/fonts/`.
- **Source Sans 3** ([SIL Open Font License 1.1](src/kpress/licenses/source-sans-3.txt),
  Adobe, [adobe-fonts/source-sans](https://github.com/adobe-fonts/source-sans)).
  Variable woff2 subsets vendored under `src/kpress/format/static/fonts/`.

## Optional Publishing Tooling Cached Separately

- **html-minifier-next** (MIT) is installed from the shipped lock into a managed npm
  cache only when an operator runs the explicit optimizer bootstrap through
  `kpress doctor --profile optimize --allow-network`. The optional `full` optimizer
  consumes that warm cache without fetching; the tool is never bundled in the wheel.

## Runtime Dependencies

Python dependencies and optional extras are declared in `pyproject.toml`. They are
installed under their own licenses and are not redistributed by this package.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
