# Project Instructions for AI Agents

This file provides instructions and context for AI coding agents working on this project.

<!-- BEGIN TBD INTEGRATION format=f04 surface=agents-md -->
## tbd

This repository uses **tbd** for git-native issue tracking (beads), spec-driven
planning, and on-demand engineering guidelines.
As the agent, you operate tbd on the user’s behalf — translate their requests into tbd
actions rather than telling them to run commands.

- Run `tbd prime` to load current project state and the full tbd workflow.
- Run `tbd skill` for the complete reusable tbd skill instructions.
- Run `tbd shortcut --list` and `tbd guidelines --list` for on-demand resources.
- Track all work as beads: `tbd create`, `tbd ready`, `tbd close`, and `tbd sync`.

<!-- END TBD INTEGRATION -->

## Build & Test

_Add your build and test commands here_

```bash
# Example:
# npm install
# npm test
```

## Architecture Overview

_Add a brief overview of your project architecture_

## Conventions & Patterns

_Add your project-specific conventions here_

<!-- BEGIN FLOWMARK INTEGRATION format=f02 surface=agents-md -->
## flowmark

Auto-format Markdown with `flowmark` for clean, semantic git diffs.

- Run `flowmark --auto <files>` on Markdown you create or edit.
- Run `flowmark --docs` for full usage and `flowmark --skill` for the skill.
- If `flowmark` is not on `PATH`, use a pinned `uvx` runner (never `@latest`).
- Fast Rust port (recommended): `uvx --from flowmark-rs==0.3.1 flowmark`.
- Python build (library / newest patch): `uvx --from flowmark==0.7.2 flowmark`.

<!-- END FLOWMARK INTEGRATION -->

<!-- BEGIN PPROSE INTEGRATION format=f01 -->
## Practical Prose (pprose)

Practical Prose: an evaluation toolkit and editorial workflows for practical documents.
Use when the user asks to improve, audit, score, or compare practical documents.

Discover the tool from the CLI itself: `pprose --help` for commands, `pprose about` for
the project narrative, and `pprose skill --list` / `pprose shortcut --list` /
`pprose guidelines --list` / `pprose runbook --list` for on-demand workflows, playbooks,
style guides, and procedures.

Run pprose as `pprose <command>` if on PATH, else `uvx pprose@0.1.0 <command>`
(zero-install via uv).

<!-- END PPROSE INTEGRATION -->
