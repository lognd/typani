<!-- frob:describes src/typani/result.py::Result -->
# Result

`Result[T, E]` models a computation that either succeeds with a value of type `T` or
fails with an error of type `E`. It is inspired by Rust's `Result<T, E>`.

`Result` is an abstract base; only its two subclasses construct:

<!-- frob:describes src/typani/result.py::Ok -->
<!-- frob:describes src/typani/result.py::Err -->
## Constructors

```python
from typani import Ok, Err, Result

ok: Result[int, str] = Ok(42)
err: Result[int, str] = Err("something went wrong")
```

`Result(...)` (calling the base class directly) raises `TypeError`. `Ok` and `Err`
are real classes -- not factory functions -- so both structural pattern matching and
`isinstance` narrowing work:

```python
match result:
    case Ok(value):
        ...
    case Err(error):
        ...

if isinstance(result, Ok):
    reveal_type(result.value)  # int
```

`Ok(1) == Ok(1)` compares by payload (value semantics), and both variants are
picklable, hashable, and safe across `copy.copy`/`copy.deepcopy`.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_ok` | `bool` | `True` when the result holds a success value. |
| `is_err` | `bool` | `True` when the result holds an error. |
| `ok` | `T \| None` | The success value, or `None`. |
| `err` | `E \| None` | The error value, or `None`. |
| `danger_ok` | `T` | The success value; raises `UnwrapError` on `Err`. |
| `danger_err` | `E` | The error value; raises `UnwrapError` on `Ok`. |
| `notes` | `tuple[str, ...]` | Notes attached via `.note()`, oldest first; always `()` on `Ok`. |

`danger_ok`/`danger_err` are properties, not methods -- `r.danger_ok()` is a bug
(calling `int`/`str`/etc. as a function). `python -m typani.lint` flags this
(`TYP001`).

## Methods

### `is_ok_and(pred) -> bool` / `is_err_and(pred) -> bool`

`True` when the variant matches and *pred* holds for the payload.

### `unwrap() -> T`

Return the success value; raise `UnwrapError(self)` on `Err`. See
[Propagation](#propagation) for the intended way to handle the raised error.

### `unwrap_err() -> E`

Return the error value; raise `UnwrapError(self)` on `Ok`.

### `unwrap_or(default) -> T | U`

Return the success value, or *default* on `Err`.

### `unwrap_or_else(fn) -> T | U`

Return the success value, or `fn(error)` on `Err`.

### `expect(msg) -> T` / `expect_err(msg) -> E`

Like `unwrap()`/`unwrap_err()`, but the raised `UnwrapError`'s message is prefixed
with *msg*.

### `map(fn) -> Result[V, E]`

Transform the success value; errors pass through unchanged.

```python
Ok(5).map(lambda x: x * 2)     # Ok(10)
Err("e").map(lambda x: x * 2)  # Err('e')
```

### `map_err(fn) -> Result[T, F]`

Transform the error value, preserving any attached notes; successes pass through
unchanged.

### `and_then(fn) -> Result[V, E | F]`

Chain a fallible operation. If `self` is `Ok`, calls `fn` and returns its result.
If `self` or the inner result is `Err`, the first error is propagated.

```python
Ok(3).and_then(lambda x: Ok(x + 1))          # Ok(4)
Ok(3).and_then(lambda x: Err("inner"))       # Err('inner')
Err("outer").and_then(lambda x: Ok(x + 1))   # Err('outer')
```

### `or_else(fn) -> Result[T, F]`

Recover from an error. If `self` is `Err`, calls `fn(err)` and returns its result.
If `self` is `Ok`, returns `self` unchanged.

### `inspect(fn) -> Result[T, E]`

Run a side-effectful function on the success value without transforming it.
Returns `self` unchanged regardless.

### `inspect_err(fn) -> Result[T, E]`

Run a side-effectful function on the error value without transforming it.
Returns `self` unchanged regardless.

### `fold(on_ok, on_err) -> U`

Collapse a `Result` into a single value: `on_ok(value)` on `Ok`, `on_err(error)` on
`Err`.

### `to_option() -> Option[T]`

Convert to `Option`: `Ok(v) -> Some(v)`, `Err -> Nothing()`. The error is discarded.

### `swap_err(err_type) -> Result[T, F]`

Assert-cast the error type. Only valid when `is_ok`; raises `UnwrapError` otherwise.

### `swap_ok(ok_type) -> Result[V, E]`

Assert-cast the success type. Only valid when `is_err`; raises `UnwrapError`
otherwise.

## Notes

### `note(msg) -> Result[T, E]`

An `Err` can carry free-text context describing where it happened, without
touching the error payload itself (so `is`/`==` comparisons against `ErrorSet`
members keep working):

```python
r = read_config(path).note(f"while loading {path}")
r.notes  # ("while loading config.toml",)
```

- `Err.note(msg) -> Err` returns a **new** `Err` with the note appended to an
  immutable tuple; `Ok.note(msg)` is a no-op returning `self`.
- `.notes -> tuple[str, ...]` is oldest-first.
- `str(err)`/`repr(err)` render notes after the payload:
  `Err(TicketError.NotFound; note: while loading x.md)`.
- `map_err` preserves notes. `@propagate` returns the same `Err` object, so notes
  survive every hop through a call chain.

## Propagation

`unwrap()` plus `@propagate` gives Rust `?` / Zig `try`-style early return without
hand-written `if r.is_err: return Err(r.danger_err)` boilerplate:

```python
from typani import propagate, Result, Ok, Err

@propagate
def close(root: Path, ticket_id: str) -> Result[Ticket, TicketError]:
    queue = load_queue(root).unwrap()          # Err returns from close()
    ticket = queue.get(ticket_id).ok_or(TicketError.NotFound).unwrap()
    return Ok(ticket)
```

`unwrap()` on `Err` raises `UnwrapError`, which carries the original `Result` in
`.container`. `@propagate` catches `UnwrapError` and returns `exc.container`
unchanged (identity preserved, notes included). Outside a `@propagate` function, an
unwrap on the wrong variant is a programmer bug and the exception escapes loudly,
exactly like an un-propagated Rust panic.

`@propagate` also works on `async def` functions, on plain methods, and on the
inner function of a `@classmethod`.

### `UnwrapError`

`UnwrapError(AssertionError)` is raised by every unwrap/expect/danger_* access on
the wrong variant. It subclasses `AssertionError` for compatibility with existing
`pytest.raises(AssertionError)` expectations, but is always raised explicitly --
never via a bare `assert` -- so it is never stripped by `python -O`. Attributes:

| Attribute | Description |
|-----------|--------------|
| `container` | The `Result`/`Option` that was unwrapped. |

`str(exc)` defaults to e.g. `"unwrap() on Err(TicketError.NotFound)"`; passing a
`message` to `expect`/`expect_err` prefixes it: `f"{message}: {default}"`.

## `catch`

### `catch(fn, *exceptions, on_error) -> Result[T, E]`

```python
Result.catch(fn, *exceptions, on_error) -> Result[T, E]
```

Runs `fn()`; returns `Ok(value)`, or -- for one of *exceptions* (default:
`(Exception,)`, never `BaseException`) -- `Err(on_error(exc))`. This is the single
home for the exception-to-`Result` boundary instead of hand-written `try/except` at
every call site.

```python
r = Result.catch(lambda: json.loads(text), json.JSONDecodeError, on_error=ParseError.InvalidJson)
```

### `catching`

Decorator form of `catch`, wrapping a whole function (sync or async):

```python
@catching(OSError, on_error=lambda e: IoError.Failed)
def read_file(path: Path) -> str:
    return path.read_text()
```
