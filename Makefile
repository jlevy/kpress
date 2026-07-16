# Makefile for easy development workflows.
# See docs/development.md for docs.
#
#   make install        # one-time: install the locked Python and npm environments
#   make hooks-install  # install git hooks (lefthook)
#   make                # default: install + format + lint + test
#   make format         # auto-format Markdown with flowmark-rs (pinned)
#   make lint           # quality gate, auto-fixing what can be fixed
#   make lint-check     # CI-mode gate: read-only, fails on any drift
#   make test           # run tests
#   make build          # build sdist + wheel
#
# GitHub Actions use these targets so local and CI gates stay aligned.

SHELL := /bin/bash

.DEFAULT_GOAL := default

# Safe default for every dependency resolution invoked through this Makefile.
UV_EXCLUDE_NEWER ?= 14 days
export UV_EXCLUDE_NEWER
# Prevent machine-global uv policy from changing the repository lock. Pass the
# checked-in configuration explicitly so every command is self-contained and
# reviewable instead of depending on an inherited UV_CONFIG_FILE setting.
UV := uv --config-file $(CURDIR)/uv.toml
UVX := uvx --config-file $(CURDIR)/uv.toml
UV_RUN := $(UV) run --frozen

# Some managed agent environments export pnpm-style npm variables that npm 11
# treats as unknown configuration. Repository policy lives in .npmrc, so prevent
# those ambient aliases from adding warnings or changing command behavior.
unexport NPM_CONFIG_FROZEN_LOCKFILE
unexport NPM_CONFIG_MINIMUM_RELEASE_AGE
# A host-level publication cutoff conflicts with the repository's release-age gate in
# npm 11. Repository installs must use the reviewed .npmrc policy instead.
unexport NPM_CONFIG_BEFORE

.PHONY: default install hooks-install format lint lint-check test audit lock upgrade build verify clean

# Pinned for security/stability — bump deliberately, honoring the 14-day rule.
#
# Supply-chain exception (see SUPPLY-CHAIN-SECURITY.md): flowmark-rs is a
# first-party package (github.com/jlevy/flowmark-rs) by this repo's author,
# exempt from the cool-off. The --exclude-newer-package override is surgical
# and per-invocation — it never relaxes any global cool-off — and scoped to
# this one package so an ambient UV_EXCLUDE_NEWER cannot block it.
#   flowmark-rs@0.3.2 published 2026-07-15; cutoff 2026-07-16 admits it.
FLOWMARK_VERSION := 0.3.2
FLOWMARK := $(UVX) --exclude-newer-package 'flowmark-rs=2026-07-16T00:00:00Z' flowmark-rs@$(FLOWMARK_VERSION)

default: install
	$(MAKE) SKIP_INSTALL=1 format
	$(MAKE) SKIP_INSTALL=1 lint
	$(MAKE) SKIP_INSTALL=1 test

install:
	# --locked also asserts uv.lock matches pyproject.toml and uv.toml, so a
	# stale or locally contaminated lock fails here instead of shipping.
	$(UV) sync --all-extras --all-groups --locked
	npm ci

hooks-install: install
	npx --no-install lefthook install

# Top-level quality gates cannot start until both environments are installed
# from their locks. The default target invokes its mutating format/lint/test
# stages serially and tells those recursive makes that installation is complete.
ifeq ($(SKIP_INSTALL),)
format lint: | install
lint-check test audit build: | install
endif

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
	$(FLOWMARK) --auto --inplace --nobackup .

lint:
	$(UV_RUN) python devtools/lint.py
	$(UV_RUN) python devtools/npm_policy.py

# Check-only lint, matching CI (does not modify files).
lint-check:
	$(UV_RUN) python devtools/lint.py --check
	$(UV_RUN) python devtools/npm_policy.py
	$(FLOWMARK) --auto --check .

test:
	$(UV_RUN) pytest

audit:
	npm audit --audit-level=moderate
	$(UV) --preview-features audit-command audit --frozen

lock:
	$(UV) lock

upgrade:
	$(UV) lock --upgrade
	$(UV) sync --all-extras --all-groups --frozen

build:
	$(UV) build --clear --no-build-isolation
	$(UV_RUN) python -m devtools.check_distribution

verify: install lint-check test audit build

clean:
	-rm -rf dist/
	-rm -rf *.egg-info/
	-rm -rf .pytest_cache/
	-rm -rf .ruff_cache/
	-rm -rf .mypy_cache/
	-rm -rf .venv/
	-rm -rf node_modules/
	-find . -type d -name "__pycache__" -exec rm -rf {} +
