# Makefile for easy development workflows.
# See docs/development.md for docs.
#
#   make install        # one-time: uv sync + npm ci (pinned JS toolchain)
#   make hooks-install  # install git hooks (lefthook)
#   make                # default: install + format + lint + test
#   make format         # auto-format Markdown with flowmark-rs (pinned)
#   make lint           # quality gate, auto-fixing what can be fixed
#   make lint-check     # CI-mode gate: read-only, fails on any drift
#   make test           # run tests
#   make build          # build sdist + wheel
#
# Note GitHub Actions call uv / npx directly, not this Makefile.

SHELL := /bin/bash

.DEFAULT_GOAL := default

.PHONY: default install hooks-install format lint lint-check test upgrade build clean

# Pinned for security/stability — bump deliberately, honoring the 14-day rule.
#
# Supply-chain exception (see SUPPLY-CHAIN-SECURITY.md): flowmark-rs is a
# first-party package (github.com/jlevy/flowmark-rs) by this repo's author,
# exempt from the cool-off. The --exclude-newer-package override is surgical
# and per-invocation — it never relaxes any global cool-off — and scoped to
# this one package so an ambient UV_EXCLUDE_NEWER cannot block it.
#   flowmark-rs@0.3.1 published 2026-05-30; cutoff 2026-06-02 admits it.
FLOWMARK_VERSION := 0.3.1
FLOWMARK := uvx --exclude-newer-package 'flowmark-rs=2026-06-02' flowmark-rs@$(FLOWMARK_VERSION)

default: install format lint test

install:
	uv sync --all-extras
	npm ci --silent

hooks-install: install
	npx --no-install lefthook install

# Auto-format all Markdown with flowmark-rs (semantic line breaks, smart
# quotes, safe cleanups). Pass `.` as the sole target so flowmark traverses
# the repo and honors .flowmarkignore + .gitignore. Flowmark-rs only reads
# .flowmarkignore relative to its target arg, so passing subdirs or globs
# bypasses it.
#
# INVARIANT: lefthook's `format-markdown` pre-commit hook delegates to this
# target. There must be exactly one flowmark invocation across the repo —
# do not add per-directory variants or pass staged files to flowmark.
format:
	$(FLOWMARK) --auto .

lint:
	uv run python devtools/lint.py

# Check-only lint, matching CI (does not modify files).
lint-check:
	uv run python devtools/lint.py --check

test:
	uv run pytest

upgrade:
	uv sync --upgrade --all-extras --dev

build:
	uv build

clean:
	-rm -rf dist/
	-rm -rf *.egg-info/
	-rm -rf .pytest_cache/
	-rm -rf .ruff_cache/
	-rm -rf .mypy_cache/
	-rm -rf .venv/
	-rm -rf node_modules/
	-find . -type d -name "__pycache__" -exec rm -rf {} +
