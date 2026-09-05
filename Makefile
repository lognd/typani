.PHONY: install develop clean build release mypy check

# T-0020 (per T-3400 idiom): this Makefile intentionally does NOT ship
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
# Every target below is a one-line wrapper around a platform-agnostic
# script under scripts/ -- no shell logic, no rm/find, no stamp files,
# no .env sourcing. This keeps `make <target>` and
# `uv run python scripts/<target>.py` identical, so Windows (which has
# no make) runs the exact same scripts directly. Pass extra flags via
# ARGS, e.g. `make release ARGS="--bump patch --tag --push"`.

install:
	uv run python scripts/install.py $(ARGS)

develop:
	uv run python scripts/develop.py $(ARGS)

clean:
	uv run python scripts/clean.py $(ARGS)

build:
	uv run python scripts/build.py $(ARGS)

release:
	uv run python scripts/release.py $(ARGS)

mypy:
	uv run python scripts/typecheck_oracle.py $(ARGS)
check:
	uv run python scripts/check.py $(ARGS)
