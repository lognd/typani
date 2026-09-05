# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `@propagate` is now lexically scoped (T-0028): only an `UnwrapError`
  raised by code lexically inside the decorated function -- its own body,
  or a nested `def`/`lambda`/comprehension in it -- is caught. An
  `UnwrapError` raised by a separate, undecorated helper now escapes
  loudly instead of being silently attributed to the wrong caller.
- `@propagate(on_error=fn)`: an optional hook called as `fn(func,
  container)` immediately before the container is returned; every catch
  is logged at `DEBUG` via the `"typani.propagate"` logger (T-0028).
- `Result.wrap_err(err)`: replace an `Err`'s payload with a fixed *err*
  value, preserving the original error as a new trailing note
  (`"caused by {inner!r}"`) instead of discarding it; `Ok` is a no-op
  (T-0028).
- `unwrap(*, err=None, note=None)` on both `Result` and `Option`: keyword
  sugar for the mapped-error propagation idiom --
  `r.unwrap(err=E, note=N) == r.wrap_err(E).note(N).unwrap()` on `Result`;
  on `Option`, `err` makes a `Nothing` propagate as `Err(err)`. The bare
  call (no keywords) is unchanged and costs nothing extra (T-0028).
- Error-return trace: `Err.trace` (`tuple[str, ...]`, innermost first),
  populated by `@propagate` calling `.traced(f"{func.__qualname__}:
  {lineno}")` on every hop through a propagation chain; renders after
  notes as `"; via a <- b"`. Lists propagation sites, not stack frames,
  and costs nothing on the `Ok` happy path. Not part of `==`/`hash`;
  preserved by `note`/`wrap_err`/`map_err`/`unwrap(err=...)`/pickling/
  `deepcopy` (T-0028).
- `python -m typani.lint`: `TYP004` now also flags the mapped-error
  propagation shape (`if X.is_err: return Err(<mapped>)`), suggesting
  `X.unwrap(err=NewErr)`; `TYP006` flags a `Result.catch`/`catching`
  exception boundary with no named exception types; `TYP007` flags a
  bare/`Exception`/`BaseException` `except` clause inside a
  `Result`/`Option`-returning function (T-0028).

### Changed

- `@propagate`'s returned container is equal to (`==`) the original
  `UnwrapError.container`, but -- because every catch now calls
  `.traced(...)` -- no longer guaranteed to be the identical (`is`)
  object; compare by value (T-0028).

## [0.1.0] - unreleased

### Added

- `Ok`/`Err`/`Some`/`Nothing` become real classes (`Result`/`Option` are
  their abstract bases), with `__match_args__` for `match`/`case`,
  value-based `__eq__`/`__hash__`, `__iter__`, and pickle/copy support
  (T-0009).
- `unwrap()`/`unwrap_err()` plus `@propagate`: Rust-`?`/Zig-`try`-style
  early return, raising `UnwrapError` on the wrong variant and letting
  `@propagate` catch it and return the original container (T-0009).
- Error notes: `Err.note(msg)` attaches free-text context to an error
  without touching its payload; `.notes` reads them back, oldest first
  (T-0009).
- `Result.catch(fn, *exceptions, on_error=...)` and its decorator form
  `@catching(...)`: a single home for the exception-to-`Result` boundary
  (T-0009).
- Completed the `Result`/`Option` combinator surface: `is_ok_and`,
  `is_err_and`, `unwrap_or`, `unwrap_or_else`, `expect`, `expect_err`,
  `inspect`, `inspect_err`, `fold`, `to_option`, `swap_ok`, `swap_err`,
  `Option.filter`, `Option.ok_or`, `Option.ok_or_else`,
  `Option.from_optional` (T-0009).
- `typani-core`: an optional PyO3/maturin native accelerator
  (`pip install "typani[native]"`) reimplementing `Result`/`Option` in
  Rust, selected automatically at import time with an automatic
  pure-Python fallback (`TYPANI_PURE`, exact-version-match rule) and a
  parity test suite proving both backends behave identically (T-0010).
- `python -m typani.lint`: a stdlib-`ast`-only misuse checker for
  `Result`/`Option` usage (TYP001-TYP005: property-called-as-method,
  truthy payload access, discarded result, propagation boilerplate,
  `assert`-guarded `danger_*` under `-O`), with `# typani: ignore` line
  suppression and a `# typani: skip-file` marker (T-0011).
- `py.typed` marker, uv-based tooling (ruff, ty, pytest-xdist,
  `dependency-groups`), GitHub Actions CI across both backends, and a
  manual-dispatch release workflow building the wheel matrix with
  maturin-action (T-0008).
- Professional README (sixty-second tour, feature table, performance and
  lint sections), a `design/typani.strata` model of typani's own module
  graph, and module docs for every public symbol added or changed in
  0.1.0 (T-0013).

### Changed

- `danger_ok`/`danger_err`/`danger_some` now raise `UnwrapError` (an
  `AssertionError` subclass) instead of a bare `AssertionError`; existing
  `pytest.raises(AssertionError)` expectations still pass (T-0009).
- `bool(result)`/`bool(option)` now raise `TypeError` instead of silently
  returning a truthiness value -- `if result:` was a common bug, never a
  valid query (T-0009).
- `Ok(1) == Ok(1)` and `Some(1) == Some(1)` are now `True` (value
  equality by variant and payload, not identity) (T-0009).
- Re-included `singleton.py` in the frob dependency graph and resolved
  the outstanding `ty` diagnostics across `src`/`tests`/`examples`
  (T-0012).

### Removed

- `Result(ok=..., err=...)` and `Option(...)` direct construction:
  `Result`/`Option` are now abstract bases; calling them raises
  `TypeError` naming `Ok`/`Err`/`Some`/`Nothing` instead (T-0009).

### Performance

- Pure-Python 0.1.0's class-based `Ok`/`Err`/`Some`/`Nothing` are
  roughly 3.7x faster than 0.0.4's tagged-tuple representation on the
  construction/accessor hot path (`Ok(1)`: 540ns -> 148ns;
  `is_err`+`danger_ok`: 877ns -> 160ns; see `docs/native.md`'s
  benchmark table) (T-0009).
- The native `typani-core` backend wins clearly on accessors (`unwrap()`:
  ~94ns pure vs. ~30ns native) and `note()` (~846ns vs. ~460ns); plain
  construction and `map`/`and_then` chains are roughly at parity with
  pure-Python, since CPython's allocation and the PyO3 call-boundary
  marshaling cost dominate both paths there (T-0010).

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
