# KPress Documentation

KPress is a Python library and command-line interface for rendering Markdown documents
and publishing static sites.
The project [README](../README.md) provides the shortest installation and usage path.
Use this index for implementation, maintenance, and release work.

## Architecture and Public Contracts

- [KPress Design](kpress-design.md): architecture, public contracts, extension seams,
  static publishing, assets, icons, and optimization
- [Interactive Footnote Popovers](interactive-footnote-popovers.plan.md): proposed
  interaction, accessibility, asset, and verification contract for pinnable evidence
  previews
- [History-Aware Section Navigation](done/history-navigation.plan.md): the completed
  plan for native hash history on TOC links and viewport-aware scroll restoration on
  Back/Forward
- [Operations and Host Integration](kpress-operations-and-host-integration.md): local
  runtime probes, browser quality gates, acceptance, accessibility, and dynamic embeds
- [Backlog and Status](../TODO.md): current capability evidence, release gates, and
  tracked follow-up work

## Setup and Maintenance

- [Installation](installation.md): supported platforms and installing uv and Python
- [Development](development.md): repository setup, common commands, dependency policy,
  and documentation workflow
- [Contributing](../CONTRIBUTING.md): required checks for proposed changes
- [Security Policy](../SECURITY.md): supported versions and private vulnerability
  reporting
- [Supply-Chain Security](../SUPPLY-CHAIN-SECURITY.md): required dependency-install and
  upgrade controls

## Publishing and Validation

- [Static Publish Runbook](kpress-static-publish.runbook.md): build configuration, asset
  modes, wrapper integration, and output verification
- [End-to-End Validation](kpress-validation.runbook.md): package gates, contract review,
  CLI and publishing smoke tests, and human acceptance
- [End-to-End Testing](kpress-e2e-testing.runbook.md): real-browser reader checks that
  automated tests cannot fully establish
- [Release Publishing](publishing.md): trusted PyPI release procedure
- [KPress 0.2.3](releases/0.2.3.md): current navigation and rendering maintenance
  release
- [KPress 0.2.2](releases/0.2.2.md): host-export maintenance release
- [KPress 0.2.1](releases/0.2.1.md): rendering and release-floor maintenance release
- [KPress 0.2.0](releases/0.2.0.md): host-rendering and asset-contract release
- [KPress 0.1.0](releases/0.1.0.md): first public alpha

## Examples

The [examples index](../examples/README.md) covers full static generation, host-wrapped
fragments, and typed programmatic builds.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
