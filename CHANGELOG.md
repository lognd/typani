# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - unreleased

<!-- Each bullet below is a placeholder; see the corresponding ticket in
     tickets.md (T-0008..T-0013) for the authoritative done report. -->

- T-0008: modernize tooling -- uv, ruff, ty, py.typed, CI, release workflow,
  changelog, bump script.
- T-0009: Result/Option redesign -- Ok/Err/Some/Nothing classes, unwrap and
  propagate, notes, eq/hash/match/iter/pickle, catch.
- T-0010: typani-core -- PyO3/maturin native Result/Option with pure-Python
  fallback and parity tests.
- T-0011: typani.lint -- stdlib-ast misuse checker TYP001-TYP005.
- T-0012: leaf modules pass -- re-include singleton.py in the frob graph,
  fix ty diagnostics, update examples to 0.1 idioms.
- T-0013: docs and README -- banner, professional README, module docs for
  the 0.1 API, strata model update, CHANGELOG.

## [0.0.4] - 2026-07-17

Adoption of `frob` as the compliance/enforcement layer, plus the design
model and documentation work that followed it.

- Adopted frob enforcement baseline; annotated the public API with frob
  obligations (`frob:doc`, `frob:tests`).
- Bound unit and integration test coverage for TEST001/TEST003; linked
  every module doc with `frob:doc` coverage edges.
- Migrated the ticket ledger to a single-file `tickets.md`.
- Closed T-0003 (frob compliance: zero warnings) and applied the T-0044
  workaround for method-level `COV001` findings.
- Modeled typani's architecture as a strata design model and linked it
  from the docs index.
- Added `pytest-cov` and switched to an editable install.

## [0.0.3] and earlier

- Result, Option, ErrorSet, Sum, dispatch, Unit, Unreachable, and the
  Singleton family, with docs, examples, and tests for each.
- README, `pydantic` optional extra, and PyPI packaging groundwork.

[0.1.0]: https://github.com/lognd/typani/compare/v0.0.4...HEAD
[0.0.4]: https://github.com/lognd/typani/compare/v0.0.3...v0.0.4
