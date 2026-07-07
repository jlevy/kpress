# KPress

KPress renders Markdown into polished, readable HTML documents and publishes them as
static sites. It is a Python library and CLI, not a framework: it owns document
rendering, typography, and the static build pipeline, and stays out of site semantics
and deployment so publishing pipelines and embedding hosts can wrap it.

What you get out of the box:

- High-quality document typography: vendored PT Serif and Source Sans 3, a documented
  CSS token system, light/dark/system themes with a no-flash bootstrap, print CSS.
- Reader features as progressive enhancement: table of contents, footnote and link
  tooltips, code copy, tabs, video popovers, responsive tables, KaTeX math with a MathML
  no-JS fallback. All JS is native ESM, source-first, zero-build.
- A full static build: route planning, sitemap/robots/redirects, content-hashed or fully
  offline (sealed) assets, optional minification and precompression, and a deterministic
  build manifest.
- A dynamic host API for embedding applications, and sanitization trust modes for raw
  HTML.

## Quickstart

```bash
uv add kpress          # library
uvx kpress --help      # CLI

mkdir mysite && cd mysite
uvx kpress init        # writes a starter kpress.yml
echo "# Hello" > index.md
uvx kpress build       # renders to public/
```

KPress is also usable as a library: `kpress.format.render_page(...)` renders one
document, and `kpress.publish.build_site("kpress.yml")` is the programmatic
`kpress build`. The two runnable examples in [examples/](examples/README.md) show both
consumption styles end to end: KPress as the whole static-site generator, and KPress as
an inner rendering library wrapped by your own site shell.

## Documentation

Architecture and contracts:

- [kpress-design.md](docs/kpress-design.md): architecture, package boundary, and the
  public contract (HTML/CSS contracts, asset model, optimizer, host integration).
- [docs/kpress-design.md](docs/kpress-design.md) (Feature Catalog): the durable catalog
  of reader features and the behavior each guarantees.
- [kpress-icons.md](docs/kpress-icons.md): the icon sprite contract.

Using and validating KPress:

- [examples/](examples/README.md): runnable static-site and wrapper examples.
- [docs/kpress-static-publish.runbook.md](docs/kpress-static-publish.runbook.md): how to
  build and ship a static site, and where KPress’s responsibility ends.
- [docs/kpress-validation.runbook.md](docs/kpress-validation.runbook.md): end-to-end
  validation gates.
- [docs/kpress-e2e-testing.runbook.md](docs/kpress-e2e-testing.runbook.md): manual
  browser acceptance checks.

Project status and process:

- [TODO.md](TODO.md): implementation status ledger.
- [docs/kpress-completion-plan.md](docs/kpress-completion-plan.md): map of remaining
  work to verified completion.
- [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/development.md](docs/development.md): dev
  setup and the quality gate.
- [SECURITY.md](SECURITY.md), [SUPPLY-CHAIN-SECURITY.md](SUPPLY-CHAIN-SECURITY.md),
  [NOTICE.md](NOTICE.md): security policy, dependency policy, and third-party notices.

## Compatibility policy

KPress is a young package and evolves by **hard cuts**: API and contract changes land
directly, with no deprecation shims and no backward-compatibility layers.
A change is acceptable when an out-of-date caller fails loudly with a clear error
message, never silently.
The supported surface is pinned in `kpress.contract` (`PUBLIC_*` names) and enforced by
tests; changing a public name means updating the contract, docs, tests, and goldens in
the same patch, and release/PR notes are the migration guide.

## Development

```bash
uv sync --all-extras
uv run pytest tests --tb=short -q
uv run python devtools/lint.py --check
```

## License

AGPL-3.0-or-later; see `LICENSE`. Third-party vendored components (Lucide icons, KaTeX,
PT Serif, Source Sans 3) are listed with their licenses in [NOTICE.md](NOTICE.md).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
