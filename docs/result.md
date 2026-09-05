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
| `trace` | `tuple[str, ...]` | Error-return trace from `.traced()` (T-0028), innermost first; always `()` on `Ok`. |

`danger_ok`/`danger_err` are properties, not methods -- `r.danger_ok()` is a bug
(calling `int`/`str`/etc. as a function). `python -m typani.lint` flags this
(`TYP001`).

## Methods

### `is_ok_and(pred) -> bool` / `is_err_and(pred) -> bool`

`True` when the variant matches and *pred* holds for the payload.

### `unwrap() -> T`

Return the success value; raise `UnwrapError(self)` on `Err`. See
[Propagation](#propagation) for the intended way to handle the raised error.

`unwrap(*, err=None, note=None) -> T` (T-0028): on `Ok`, *err*/*note* are
always ignored. On `Err`, the raised `UnwrapError`'s `.container` -- the
value `@propagate` returns -- is built from them instead of `self`:

```python
r.unwrap(err=E, note=N) == r.wrap_err(E).note(N).unwrap()
```

i.e. *err* alone maps the error via [`wrap_err`](#wrap_errerr---resultt-f)
first; *note* alone appends to the existing `Err`'s notes; both compose. The
bare call (`r.unwrap()`, both keywords omitted) is exactly the pre-T-0028
path with no extra work -- see [Scope](#scope) for the cost guarantee this
preserves.

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

### `wrap_err(err) -> Result[T, F]`

Replace an `Err`'s payload with *err*, a plain value (T-0028) -- unlike
`map_err`, not a function of the old error. The old error is not lost: it is
appended to `.notes` as `f"caused by {inner!r}"`, after any notes already
present, so it stays inspectable even though the error type changed.
`Ok` passes through unchanged.

```python
Ok(1).wrap_err("NEW")               # Ok(1)
Err("bad").wrap_err("NEW")          # Err('NEW'; note: caused by 'bad')
```

Prefer this over `map_err(lambda _: NewErr)` when the new error is a fixed
replacement rather than something computed from the old one -- it is also
what `unwrap(err=...)` (see [`unwrap`](#unwrap---t)) and the mapped-error
idiom below use under the hood.

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

<!-- frob:describes src/typani/_propagate.py::propagate -->
```python
from typani import propagate, Result, Ok, Err

@propagate
def close(root: Path, ticket_id: str) -> Result[Ticket, TicketError]:
    queue = load_queue(root).unwrap()          # Err returns from close()
    ticket = queue.get(ticket_id).ok_or(TicketError.NotFound).unwrap()
    return Ok(ticket)
```

`unwrap()` on `Err` raises `UnwrapError`, which carries the original `Result` in
`.container`. `@propagate` catches `UnwrapError` and returns `exc.container`,
equal to the original and carrying its notes -- but, as of T-0028, not
necessarily the same object: every catch calls `.traced(...)` first (see
"Return trace" below), which returns a new `Err` with one more trace entry.
Compare by `==`, not `is`. Outside a `@propagate` function, an unwrap on the
wrong variant is a programmer bug and the exception escapes loudly, exactly
like an un-propagated Rust panic.

`@propagate` also works on `async def` functions, on plain methods, and on the
inner function of a `@classmethod`.

### Cost

`@propagate` is not free on the happy path, and it would be dishonest to
claim otherwise: wrapping a function adds one extra Python call frame to
every invocation, decorated or not, success or failure. The `try` block
itself costs nothing in CPython when no exception is raised -- the frame is
the entire cost. Measured with `timeit` (best-of-3, 300k calls, a function
that just returns `Ok(1).unwrap()`, this repo's dev machine):

| Backend | Undecorated | `@propagate`-decorated | Delta |
|---------|-------------|-------------------------|-------|
| native  | ~230 ns     | ~340 ns                 | ~+110 ns |
| pure    | ~320 ns     | ~430 ns                 | ~+110 ns |

That extra frame is roughly constant regardless of backend -- it is Python
function-call overhead, not anything `@propagate`'s body does. Weigh it
against what it replaces: the hand-written `if r.is_err: return
Err(r.danger_err)` boilerplate it exists to remove is itself Python-level
code with its own (larger) per-call cost, so `@propagate` is very rarely
the bottleneck in real code. It is worth measuring, not worth avoiding by
default -- see "When to use it" below for where it does and does not pay
for itself. Note this cost is unrelated to the T-0028 scope check and
trace bookkeeping described below, which run only when an `UnwrapError` is
actually caught -- the failure path, never the happy path.

### Failure-path cost

A hop that actually propagates costs about 2.2us on the native backend
(measured with `timeit`, logging disabled), of which about 0.9us is the
floor of raising and catching one Python exception at all; the rest is
the lexical-scope check, the trace hop and the guarded DEBUG log. The
old three-line early return costs about 0.5us per hop. Propagation is
therefore for failures that are exceptional, not for an expected `Err`
inside a tight loop, where `match` is the right tool.

### When to use it

- Decorate a function with **two or more** propagation sites (two or more
  `.unwrap()` calls whose failure should short-circuit the function). A
  single-site function reads at least as clearly with a `match`/`case` or
  an explicit early return, and does not pay the extra-frame cost above
  for no readability win.
- Keep `@propagate` the **innermost** decorator, directly above `def`:
  below `@classmethod`, `@staticmethod`, `@functools.lru_cache`, and
  pydantic validators (`@field_validator`, `@model_validator`). Those
  decorators need to see the function `@propagate` wraps, not the other
  way around -- get the order wrong and `@classmethod`/caching machinery
  ends up operating on the raw function instead of the propagating one.
- Do not sweep `@propagate` across a codebase to make `python -m
  typani.lint`'s TYP004 count hit zero. TYP004 is a **triage worklist** --
  "here is manual propagation boilerplate you could replace" -- not a
  target to drive to zero; some of those sites are single-unwrap
  functions that are fine left as `match`/`case` or an early return per
  the point above.
- Avoid it in a hot pure-Python loop (e.g. `@propagate` on a function
  called millions of times in a tight loop): the extra-frame cost above
  is realistic there, unlike in typical request/command-handler-shaped
  code where it is noise next to I/O.

### Scope

`@propagate` only catches an `UnwrapError` raised by code **lexically inside**
the decorated function -- its own body, plus any nested `def`, `lambda`, or
comprehension written inside that body. It does not catch an `UnwrapError`
raised by a call to a separate, undecorated helper:

```python
def load_queue(root: Path) -> Result[Queue, TicketError]:
    ...

@propagate
def close(root: Path, ticket_id: str) -> Result[Ticket, TicketError]:
    queue = load_queue(root).unwrap()  # OK: unwrap() is lexically inside close()
    return Ok(...)

def _load_or_die(root: Path) -> Queue:
    return load_queue(root).unwrap()  # NOT inside any @propagate function

@propagate
def close_bad(root: Path, ticket_id: str) -> Result[Ticket, TicketError]:
    queue = _load_or_die(root)  # BUG: helper's unwrap() escapes as UnwrapError
    return Ok(...)
```

`close_bad` above lets `UnwrapError` escape loudly instead of silently
returning `_load_or_die`'s container -- doing otherwise would attribute the
wrong provenance to the failure, and the helper's container type may not even
match `close_bad`'s declared error type. Fix it one of two ways: decorate the
helper itself (`@propagate` on `_load_or_die`, then `.unwrap()` its result
inside `close_bad`), or have the helper return its `Result`/`Option` directly
and unwrap it at the call site inside the decorated function.

When the failure needs to be translated into the outer function's error type,
map before unwrapping, all inside the decorated function. Use
`unwrap(err=...)` (a `wrap_err(...)` + `unwrap()` in one call) when the new
error is a fixed replacement, or `map_err(fn).unwrap()` when it is computed
from the old one:

```python
@propagate
def close(root: Path, ticket_id: str) -> Result[Ticket, CloseError]:
    queue = load_queue(root).unwrap(err=CloseError.QueueUnavailable)
    ...

@propagate
def close2(root: Path, ticket_id: str) -> Result[Ticket, CloseError]:
    queue = load_queue(root).map_err(CloseError.from_ticket_error).unwrap()
    ...
```

`@propagate` also accepts an `on_error` hook: `@propagate(on_error=fn)` calls
`fn(func, container)` immediately before the container is returned (any
exception `fn` raises propagates to the caller instead). Every catch --
whether or not `on_error` is given -- is logged at `DEBUG` via the
`"typani.propagate"` logger as `"propagate: %s returned %r"`, so a caught
propagation is visible in logs even when `on_error` is not used; the `%r`
includes any notes attached to the container.

### Return trace

Every hop through a `@propagate` chain leaves a breadcrumb, Zig
error-return-trace style: before returning the caught container,
`@propagate` calls `container.traced(f"{func.__qualname__}:{lineno}")`,
where *lineno* is the line of the `unwrap()` call that raised (resolved from
the same frame the [Scope](#scope) check already inspects). `Err.trace` is
the resulting `tuple[str, ...]`, innermost site first; `Ok.trace` is always
`()`. It renders after any notes: `Err(E; note: n; via close_ticket:42 <-
handle_request:9)`.

This lists **propagation sites, not stack frames** -- one entry per
`@propagate` hop the error passed through, not every call in between, and
nothing at all is recorded on the `Ok` happy path (`traced()` only ever runs
from an already-caught `UnwrapError`, so it costs nothing when nothing
fails). `.trace` is not part of `==`/`hash` and is preserved by `note()`,
`wrap_err()`, `map_err()`, `unwrap(err=...)`, pickling, and `deepcopy`.

```python
@propagate
def inner() -> Result[int, str]:
    return Err("disk full").unwrap()

@propagate
def middle() -> Result[int, str]:
    return Ok(inner().unwrap())

@propagate
def outer() -> Result[int, str]:
    return Ok(middle().unwrap())

outer()  # Err('disk full'; via inner:3 <- middle:8 <- outer:12)
```

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
