# Stamp file: uv sync runs only when pyproject.toml or uv.lock changes.
STAMP := .venv/.install-stamp

.PHONY: install develop clean build upload mypy

# T-0008 (per T-3400 idiom): this Makefile intentionally does NOT ship
# format/lint/typecheck/test/coverage/check targets. This is a
# frob-enabled project (see frob.toml) and frob IS the interface for
# those workflows, not a make wrapper around it -- use the commands
# below directly:
#
#   frob format     ruff check --fix + ruff format
#   frob check      the aggregate gate (ruff, ty, frob cycle/dup/arch/...)
#   frob test       select and run tests for the touched set (or --all)
#   frob coverage   refresh coverage.xml / the coverage stamp
#
# Only bootstrap (install, develop), build/publish (build, upload), and
# the mypy oracle stay here: bootstrap cannot be a frob subcommand
# because it installs frob's own prerequisites, build/upload carry
# release-specific logic frob has no equivalent for, and mypy is kept
# only as a 3.10-semantics oracle alongside frob's own ty-based check
# (see pyproject.toml [tool.frob] check_skip_ty, T-0002/T-0012).

# ---------- install (stamp-guarded bootstrap) ----------

$(STAMP): pyproject.toml
	# --all-extras is deliberately NOT used here: the `native` extra pins
	# typani-core==0.1.0, which is not published yet (T-0010). Once it is,
	# CI and local installs that want the native extension should opt in
	# explicitly with `uv sync --all-groups --all-extras`.
	uv sync --all-groups
	@touch $(STAMP)

install: $(STAMP)

develop: $(STAMP)
	@test -f crates/typani-core/Cargo.toml || (echo "no native crate yet (T-0010)"; exit 0)
	@test -f crates/typani-core/Cargo.toml && uv run maturin develop --uv -m crates/typani-core/Cargo.toml || true

# ---------- typecheck oracle ----------

mypy: $(STAMP)
	uv run mypy --config-file mypy-py310.ini

# ---------- build & publish ----------

clean:
	rm -rf dist/ build/ .pytest_cache/ .ruff_cache/ .mypy_cache/ .ty_cache/ .coverage htmlcov/ coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null; true

build: clean
	uv build

upload: build
	@NEW=$$(uv run python scripts/bump_version.py); \
	git add pyproject.toml; \
	git commit -m "chore: bump version to $$NEW"; \
	git push; \
	uv build && uv publish
