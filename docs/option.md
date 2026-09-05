<!-- frob:describes src/typani/option.py::Option -->
# Option

`Option[T]` models an optional value: either `Some(value)` or `Nothing`. It is the
explicit, composable alternative to Python's bare `T | None`. Where `Optional[T]`
is a type alias, `Option[T]` is a real container with a full transformation API.

`Option` is an abstract base; only its two subclasses construct:

<!-- frob:describes src/typani/option.py::Some -->
<!-- frob:describes src/typani/option.py::Nothing -->
## Constructors

```python
from typani import Some, Nothing, Option

present: Option[int] = Some(42)
absent: Option[int] = Nothing()
```

`Option(...)` (calling the base class directly) raises `TypeError`. `Some` and
`Nothing` are real classes, so both pattern matching and `isinstance` narrowing
work:

```python
match option:
    case Some(value):
        ...
    case Nothing():
        ...
```

`Nothing()` always returns the same cached instance (`Nothing() is Nothing()` is
`True`), so absence is a zero-allocation, singleton value. `Some(1) == Some(1)`
compares by payload, and both variants are picklable, hashable, and safe across
`copy.copy`/`copy.deepcopy`.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_some` | `bool` | `True` when a value is present. |
| `is_nothing` | `bool` | `True` when no value is present. |
| `some` | `T \| None` | The inner value, or `None`. |
| `danger_some` | `T` | The inner value; raises `UnwrapError` on `Nothing`. |

`danger_some` is a property, not a method -- `o.danger_some()` is a bug.
`python -m typani.lint` flags this (`TYP001`).

## Methods

### `unwrap() -> T`

Return the value; raise `UnwrapError(self)` on `Nothing`. Works with `@propagate`
exactly like `Result.unwrap()` -- see [the Result docs](result.md#propagation).

### `unwrap_or(default) -> T`

Return the value if present, otherwise return *default*.

```python
Some(3).unwrap_or(0)    # 3
Nothing().unwrap_or(0)  # 0
```

### `unwrap_or_else(fn) -> T | U`

Return the value if present, otherwise return `fn()`.

### `expect(msg) -> T`

Like `unwrap()`, but the raised `UnwrapError`'s message is prefixed with *msg*.

### `map(fn) -> Option[V]`

Transform the value if present; `Nothing` passes through.

```python
Some(3).map(lambda x: x * 2)    # Some(6)
Nothing().map(lambda x: x * 2)  # Nothing
```

### `and_then(fn) -> Option[V]`

Chain a computation that may itself return `Nothing`.

```python
Some(4).and_then(lambda x: Some(x + 1))  # Some(5)
Some(4).and_then(lambda x: Nothing())    # Nothing
Nothing().and_then(lambda x: Some(x))    # Nothing
```

### `or_else(fn) -> Option[T]`

Provide a fallback when the value is absent.

```python
Nothing().or_else(lambda: Some(0))  # Some(0)
Some(7).or_else(lambda: Some(0))    # Some(7)
```

### `inspect(fn) -> Option[T]`

Run a side-effectful function on the value if present; returns `self` unchanged.

### `filter(pred) -> Option[T]`

Keep the value only when *pred* holds; a present-but-rejected value becomes
`Nothing`.

```python
Some(4).filter(lambda x: x % 2 == 0)  # Some(4)
Some(3).filter(lambda x: x % 2 == 0)  # Nothing
```

### `ok_or(err) -> Result[T, E]`

Convert to `Result`: `Some(v) -> Ok(v)`, `Nothing() -> Err(err)`.

### `ok_or_else(fn) -> Result[T, E]`

Like `ok_or`, computing the error lazily: `Some(v) -> Ok(v)`, `Nothing() -> Err(fn())`.

### `from_optional(x) -> Option[T]`

Wrap a bare `T | None`: `Some(x)` when `x is not None`, else `Nothing()`.

```python
Option.from_optional(config.get("key"))
```

## Relationship to Result

`Option[T]` is equivalent to `Result[T, Unit]` but more ergonomic when there is no
meaningful error to report. Use `Result` when the error type carries information;
use `Option` when you only care whether a value exists. `Result.to_option()` and
`Option.ok_or()`/`Option.ok_or_else()` convert between the two.
