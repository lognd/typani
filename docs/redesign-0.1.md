# typani 0.1 redesign

Design record for the 0.1 line. Written from a usage audit of frob
(209 of 649 source files import typani) and its bug history (1612
changelog entries, 2018 fix commits). Every item below traces to a
measured finding; the numbers are from 2026-09-05.

## 1. What the audit found

### 1.1 Usage profile (frob, `src/**/*.py`)

| Symbol / idiom | Occurrences |
|----------------|-------------|
| `Err(...)` | 2256 |
| `Ok(...)` | 1416 |
| `.is_err` | 1826 |
| `.danger_ok` | 1812 |
| `.danger_err` | 1283 |
| `.is_ok` | 186 |
| `ErrorSet` subclasses | 165 |
| `Option` / `Some` / `Nothing` | 30 / 23 / 59 |
| `.map(` | 7 |
| `.and_then(` / `>>` / `map_err` / `inspect` / `swap_*` | 0 |
| `Result(ok=...)` direct construction | 0 |
| `Singleton*`, `Sum`, `dispatch`, `merge` | 0 |

The dominant idiom, 651 exact instances plus variants, is three lines
of boilerplate per fallible call:

```python
loaded = load_queue(root)
if loaded.is_err:
    return Err(loaded.danger_err)
queue = loaded.danger_ok
```

The combinator API is unused because Python lambdas cannot contain
statements and the chain reads worse than the early return. The
library therefore optimizes the wrong path today: `map`/`and_then`
allocate three `Result` objects and the hot path (`Ok`, `is_err`,
`danger_ok`) pays for sentinel double-checks and keyword-only
`__init__` dispatch.

### 1.2 Where the bugs come from

Themes across frob's bug tickets, with counts of changelog titles:

| Theme | Titles | typani-relevant root cause |
|-------|--------|----------------------------|
| "silently" dropped / ignored / discarded | 63 | a computed value or `Result` that nothing inspects; a default taken with no diagnostic |
| exception escaping a `Result` boundary (uncaught / crash / instead of returning Err) | 30+ | `try/except` written by hand at every edge (685 `except` sites in src); one missed edge is a crash (T-3015, T-3264, T-0134, T-0142, T-0152, T-1423) |
| lost context ("which file? which id?") | 45 | `ErrorSet` members are singletons and carry no detail; 26 `Result[..., str]` and 7 tuple-error results exist only to smuggle context |
| property called as a method (`danger_ok()`) | recorded 3x in the user's own refs | a footgun that repeats across sessions; the refs literally say "NEVER call as r.danger_ok()" |
| `assert` used for the unwrap invariant | latent | under `python -O` `danger_ok` on an `Err` returns the private sentinel silently |
| no `py.typed` marker | latent | downstream mypy treats every typani type as `Any`; the whole `Result` discipline is unchecked in consumers |

### 1.3 What other languages have that we lack

- Rust `?` / Zig `try`: early-return propagation. This is the 651-line
  boilerplate above.
- Rust `match` with `Ok(v)` / `Err(e)` arms. Python 3.10 has structural
  pattern matching, but `Ok` and `Err` are factory functions today, so
  `case Ok(v)` is impossible.
- Rust `#[must_use]`: a discarded `Result` is a warning. Python has no
  attribute for this; a lint is the only tool.
- Rust `anyhow::Context` / Zig error return traces: attach context as
  the error travels up. Nothing here today.
- Rust value semantics: `Ok(1) == Ok(1)`. Today identity only, which
  makes tests awkward.
- Kotlin/Swift `if let` narrowing: `isinstance(r, Ok)` narrowing is
  impossible while `Ok` is a function.

## 2. Decisions

### 2.1 `Ok` and `Err` become classes; `Result` is their base

```python
class Result(Generic[T_co, E_co]): ...      # abstract; not constructible
class Ok(Result[T_co, E_co]): ...           # __match_args__ = ("value",)
class Err(Result[T_co, E_co]): ...          # __match_args__ = ("error",)
```

- `Ok(1)` and `Err(e)` still construct exactly as before.
- `isinstance(r, Ok)` narrows in ty/mypy; `match r: case Ok(v): ...`
  works.
- `Result(ok=..., err=...)` is removed (zero external uses); calling
  `Result(...)` raises `TypeError` naming `Ok`/`Err`.
- Covariant type variables so `Ok[int, Never]` is assignable to
  `Result[int, MyError]` and the return-type context infers `E`.
- `__eq__`/`__hash__` by variant and payload. `__iter__` yields the
  value for `Ok` and nothing for `Err`. `__bool__` raises `TypeError`
  (`if result:` is always a bug). `__repr__` unchanged.
- Picklable and copyable (frob crosses `ProcessPoolExecutor`
  boundaries with these in 14 files).

The same shape for `Option`: `Some(Option)` with `__match_args__ =
("value",)` and `Nothing` as a class whose call returns one cached
instance (`Nothing()` keeps working; `case Nothing():` works; zero
allocations).

### 2.2 Propagation: `unwrap()` plus `@propagate`

```python
from typani import propagate, Result, Ok, Err

@propagate
def close(root: Path, ticket_id: str) -> Result[Ticket, TicketError]:
    queue = load_queue(root).unwrap()          # Err returns from close()
    ticket = queue.get(ticket_id).ok_or(TicketError.NotFound).unwrap()
    return Ok(ticket)
```

- `unwrap()` on `Err` raises `UnwrapError`, which carries the original
  `Result`. `@propagate` catches it and returns that `Result` object
  unchanged (notes included, see 2.3). Outside a `@propagate` function
  the exception escapes: an un-propagated unwrap on an error is a
  programmer bug and crashes loudly, exactly like Rust.
- `UnwrapError` subclasses `AssertionError` so existing
  `pytest.raises(AssertionError)` expectations keep passing, and it is
  raised unconditionally (never via `assert`, so `-O` cannot strip it).
- `danger_ok` / `danger_err` / `danger_some` stay as properties and now
  raise `UnwrapError` too. They are the "I checked already" accessor;
  `unwrap()` is the "propagate or crash" accessor.
- `Option.unwrap()` raises the same `UnwrapError` carrying the `Nothing`.

### 2.3 Error notes (context that travels with the error)

```python
r = read_config(path).note(f"while loading {path}")
```

- `Err.note(msg) -> Err` returns a new `Err` with the note appended to
  an immutable tuple; `Ok.note(msg)` returns `self`.
- `.notes -> tuple[str, ...]`, oldest first.
- `str(err)` and `repr(err)` render notes after the payload:
  `Err(TicketError.NotFound; note: while loading x.md)`.
- The error payload itself is untouched, so `is` comparisons against
  `ErrorSet` members keep working. This is the whole reason it is on
  the `Result` and not on the error.
- `map_err` preserves notes. `@propagate` returns the same object, so
  notes survive every hop.

### 2.4 Completing the API

Result: `is_ok`, `is_err`, `is_ok_and(pred)`, `is_err_and(pred)`, `ok`,
`err`, `danger_ok`, `danger_err`, `unwrap`, `unwrap_err`, `unwrap_or`,
`unwrap_or_else`, `expect(msg)`, `expect_err(msg)`, `map`, `map_err`,
`and_then`, `or_else`, `inspect`, `inspect_err`, `fold(on_ok, on_err)`,
`to_option()`, `note`, `notes`, `swap_ok`, `swap_err` (kept, assert-cast
semantics via `UnwrapError`), `__or__` (map), `__rshift__` (and_then).

Option: `is_some`, `is_nothing`, `some`, `danger_some`, `unwrap`,
`unwrap_or`, `unwrap_or_else`, `expect`, `map`, `and_then`, `or_else`,
`inspect`, `filter(pred)`, `ok_or(err)`, `ok_or_else(fn)`,
`Option.from_optional(x)`, `__or__`, `__rshift__`.

Classmethod `Result.catch(fn, *exceptions, on_error=...)`: runs `fn()`;
returns `Ok(value)` or, for a listed exception, `Err(on_error(exc))`.
This is the single home for the exception-to-Result boundary that
frob hand-writes 685 times. Decorator form `@catching(OSError,
on_error=lambda e: IoError.Failed)` wraps a whole function.

### 2.5 Native core with pure-Python fallback

- New distribution `typani-core` (maturin, PyO3, `abi3-py310`) in
  `crates/typani-core/`, module `typani_core`, implementing `Result`,
  `Ok`, `Err`, `Option`, `Some`, `Nothing` as frozen `#[pyclass]`es.
- `typani` stays a pure-Python wheel with no build dependency. On
  import, `typani._impl` uses `typani_core` when it is importable AND
  `typani_core.__version__ == typani.__version__`; otherwise the
  pure-Python classes. `TYPANI_PURE=1` forces the fallback. The choice
  is logged once at debug level and exposed as `typani.native_active()`.
- The pure-Python module is the checker-visible definition (mypy strict
  and ty run against it); the native classes are behaviorally identical
  and the parity test suite runs the full test matrix under both
  backends.
- `typani[native]` extra pins `typani-core==<same version>` (frob's
  version-coupling doctrine: an ABI-coupled extension is never loosely
  pinned).
- `ErrorSet`, `Sum`, `dispatch`, `Unit`, `Unreachable`, `Singleton` stay
  pure Python: none is on a hot path.

### 2.6 Misuse lint: `python -m typani.lint`

A stdlib-`ast` checker with no dependencies, runnable in CI and as a
frob `[policy]` rule. Rules:

| Rule | Detects |
|------|---------|
| TYP001 | `x.danger_ok()`, `x.is_ok()`, `x.some()` -- a property called as a method |
| TYP002 | `if r.ok:` / `if r.err:` / `if r.some:` -- truthiness of an `Optional` payload |
| TYP003 | an expression statement that is a bare `Ok(...)`/`Err(...)`/`Some(...)` or a call to a function in the same module annotated `-> Result[...]` / `-> Option[...]` (discarded result) |
| TYP004 | `if x.is_err: return Err(x.danger_err)` -- the propagation boilerplate; suggests `unwrap()` under `@propagate` (informational) |
| TYP005 | `assert r.is_ok` immediately followed by `r.danger_ok` -- an invariant that `-O` strips (informational) |

### 2.7 Tooling modernization (from the frob scaffold)

uv with `[dependency-groups]`, ruff for lint and format (drops black and
isort), ty as the type checker (mypy kept only as an oracle for the
3.10 target), pytest with xdist, `py.typed`, `scripts/bump_version.py`,
`CHANGELOG.md`, GitHub Actions CI (lint, typecheck, test on both
backends, cargo test, frob check) and a manual-dispatch release
workflow building the wheel matrix with maturin-action and publishing
via OIDC. Makefile keeps only bootstrap and build/publish targets;
`frob` is the interface for everything else. License stays MIT: typani
is already published under it.

## 3. Compatibility with 0.0.x

Kept: every public name, `Ok`/`Err`/`Some`/`Nothing` call syntax, all
properties, all combinators, `|`/`>>`, `ErrorSet` and `|` merging,
`Sum`, `dispatch`, `Unit`, `Unreachable`, the singleton family.

Changed: `danger_*` raise `UnwrapError` (an `AssertionError`) instead
of a bare `AssertionError`; `Result(...)` and `Option(...)` are no
longer constructible; `Nothing` is a class; `bool(result)` raises;
`Ok(1) == Ok(1)` is now `True`.

frob was checked for each change: zero direct constructions, zero
`Nothing`-without-call, two `AssertionError` expectations (still pass),
one `isinstance(x, Result)` (still passes).
