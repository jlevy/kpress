# Makefile for easy development workflows.
# See docs/development.md for docs.
# GitHub Actions use these targets so local and CI gates stay aligned.

.DEFAULT_GOAL := default
# Keep install and quality stages ordered even when callers pass `-j`.
.NOTPARALLEL:

# Safe default for every dependency resolution invoked through this Makefile.
UV_EXCLUDE_NEWER ?= 14 days
export UV_EXCLUDE_NEWER
# Prevent machine-global uv policy from changing the repository lock. Pass the
# checked-in configuration explicitly so every command is self-contained and
# reviewable instead of depending on an inherited UV_CONFIG_FILE setting.
UV := uv --config-file $(CURDIR)/uv.toml
UVX := uvx --config-file $(CURDIR)/uv.toml
UV_RUN := $(UV) run --frozen
# First-party exception reviewed in SUPPLY-CHAIN-SECURITY.md. The cutoff is
# package-scoped and only admits the exact formatter release pinned here.
FLOWMARK_VERSION := 0.3.2
FLOWMARK_EXCEPTION := 2026-07-16T00:00:00Z
FLOWMARK := $(UVX) --exclude-newer-package 'flowmark-rs=$(FLOWMARK_EXCEPTION)' flowmark-rs@$(FLOWMARK_VERSION)

# Some managed agent environments export pnpm-style npm variables that npm 11
# treats as unknown configuration. Repository policy lives in .npmrc, so prevent
# those ambient aliases from adding warnings or changing command behavior.
unexport NPM_CONFIG_FROZEN_LOCKFILE
unexport NPM_CONFIG_MINIMUM_RELEASE_AGE
# A host-level publication cutoff conflicts with the repository's release-age gate in
# npm 11. Repository installs must use the reviewed .npmrc policy instead.
unexport NPM_CONFIG_BEFORE

.PHONY: default install hooks-install biome-fix browser-types format format-markdown lint lint-check test audit lock upgrade build verify clean

default: install format lint test

install:
	# --locked also asserts uv.lock matches pyproject.toml and uv.toml, so a
	# stale or locally contaminated lock fails here instead of shipping.
	$(UV) sync --all-extras --all-groups --locked
	npm ci

hooks-install: install
	npx --no-install lefthook install

biome-fix:
	npx --no-install biome check --write --unsafe --no-errors-on-unmatched $(STAGED_FILES)

browser-types:
	npx --no-install tsc --noEmit -p tsconfig.json

format lint lint-check test audit build: | install

format:
	$(MAKE) format-markdown
	$(UV_RUN) ruff format src tests devtools
	npx --no-install biome format --write src tests biome.json package.json tsconfig.json

format-markdown:
	$(FLOWMARK) --auto --inplace --nobackup .

lint:
	$(UV_RUN) python -m devtools.lint
	$(UV_RUN) python -m devtools.check_supply_chain
	$(UV_RUN) python -m devtools.public_hygiene

# Check-only lint, matching CI (does not modify files).
lint-check:
	$(UV_RUN) python -m devtools.lint --check
	$(UV_RUN) python -m devtools.check_supply_chain
	$(UV_RUN) python -m devtools.public_hygiene
	$(FLOWMARK) --auto --check .

test:
	$(UV_RUN) pytest
	npx --no-install vitest run --config tests/js/vitest.config.mjs

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
