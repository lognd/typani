# Native core (T-0010)

`typani-core` is a PyO3/maturin extension (`crates/typani-core`) that
reimplements `Result`/`Ok`/`Err`/`Option`/`Some`/`Nothing` in Rust for
lower per-call overhead. It is an accelerator, never a required
dependency: every public behavior -- methods, dunders, error types, error
*messages*, pickling -- is identical between the native and pure-Python
implementations, and typani runs correctly with only the pure-Python
package installed.

<!-- frob:doc docs/native.md#native-core -->
<!-- frob:ticket T-0010 -->

## Install

```bash
pip install "typani[native]"
# or
uv add "typani[native]"
```

Without the `native` extra, typani installs and runs exactly as before;
nothing else changes.

## Backend selection

`typani._impl.native_active()` (re-exported as `typani.native_active()`)
decides once per process, at import time:

1. `TYPANI_PURE` set to a truthy value (`"1"`/`"true"`/`"yes"`,
   case-insensitive) forces the pure-Python backend unconditionally.
2. Otherwise, typani tries `import typani_core`. If that raises
   `ImportError` (the `native` extra was never installed), it falls back
   to pure-Python.
3. If importable, `typani_core.__version__` must exactly equal typani's
   own `__version__` (`typani._version.__version__`). `typani-core` is
   pinned `==` (not `>=`/`~=`) to typani's version in `pyproject.toml`'s
   `native` extra precisely because it is ABI-coupled: a mismatched
   native extension is worse than none. A mismatch logs a `WARNING`
   naming both versions and falls back to pure-Python.

Check which backend is active:

```python
import typani

typani.backend_name()   # "native" or "pure"
typani.native_active()  # bool
```

The choice is also logged once at `DEBUG` via the stdlib `logging`
module (`typani._impl` logger) -- never printed.

## The parity guarantee

Every method, property, dunder, and error path on `Ok`/`Err`/`Some`/
`Nothing` behaves identically under both backends: same return values,
same exception types, same exception *messages*, same `repr`/`str`,
same `__hash__`/`__eq__` semantics, same pickling (`Err`'s notes
round-trip through the shared `typani.result._rebuild_err`, defined once
in pure Python and called by both backends' `Err.__reduce__`). This is
enforced by `tests/test_backend.py::test_native_pure_parity`, which runs
`tests/parity/run_case.py` (a fixed table of ~50 expressions in
`tests/parity/cases.py`) as two subprocesses -- one with `TYPANI_PURE=1`,
one without -- and diffs the JSON reports. The whole test suite
(`tests/`) additionally runs unchanged under both backends in CI.

## Build locally

```bash
make develop
# equivalent to:
uv run maturin develop --uv -m crates/typani-core/Cargo.toml
```

This builds `crates/typani-core` in place and installs it into the
project's `.venv` in editable mode. Rebuild after any change under
`crates/typani-core/src/`.

## Benchmarks

`bench/bench_result.py` runs fixed `timeit` micro-benchmarks and prints a
table; run it under both backends to compare:

```bash
uv run python bench/bench_result.py            # active backend
TYPANI_PURE=1 uv run python bench/bench_result.py
```

Pure-Python numbers, historical for context (0.0.4, before the 0.1.0
rewrite that dropped the tagged-tuple representation for real classes):

| operation              | pure 0.0.4 |
| ----------------------- | ---------: |
| `Ok(1)`                 |    540 ns |
| `is_err` + `danger_ok`  |    877 ns |
| `map` + `and_then`      |   6669 ns |
| `Some(1)`                |    309 ns |
| `Nothing()`              |    465 ns |

Pure-Python 0.1.0 (current, class-based) vs. native 0.1.0, measured on
this machine (`bench/bench_result.py`, 200k iterations per operation;
absolute numbers vary by machine, the native/pure *ratio* is the useful
signal):

| operation               | pure 0.1.0 | native 0.1.0 |
| ------------------------ | ---------: | -----------: |
| `Ok(1)`                  |     148 ns |       212 ns |
| `Some(1)`                 |     148 ns |       181 ns |
| `Nothing()`               |     185 ns |       124 ns |
| `unwrap()`                |      94 ns |        30 ns |
| `is_err` + `danger_ok`   |     160 ns |       159 ns |
| `map` + `and_then`       |     768 ns |       774 ns |
| `Err(e).note("x")`       |     846 ns |       460 ns |
| pickle round trip        |    4033 ns |      4673 ns |

Native wins clearly on `unwrap()` (a single Rust field read, no
Python-level attribute lookup) and `note()` (no dict/`__slots__`
indirection). Plain construction (`Ok(1)`, `Some(1)`) and `map`/
`and_then` chains are roughly at parity or slightly behind pure-Python on
this run -- the PyO3 call boundary (argument marshaling into and out of
Rust) has its own fixed cost that a single-field allocation does not
amortize away, and the pickle path pays for `getattr(cls, "_rebuild_err")`
lookups through the module import that the pure-Python reduce closes over
directly. `crates/typani-core/src/result.rs`'s "tightest possible code
path" comments track where each operation stands relative to that intent;
frob:todo T-0010 marks further constant-folding of the module lookups as
follow-up work, not a blocker for this ticket.
