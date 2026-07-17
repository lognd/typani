<!-- frob:describes src/typani/option.py::Option -->
# Option

`Option[T]` models an optional value: either `Some(value)` or `Nothing`. It is the
explicit, composable alternative to Python's bare `T | None`. Where `Optional[T]` is
a type alias, `Option[T]` is a real container with a transformation API.

<!-- frob:describes src/typani/option.py::Some -->
<!-- frob:describes src/typani/option.py::Nothing -->
## Constructors

```python
from typani.option import Some, Nothing, Option

present: Option[int] = Some(42)
absent: Option[int] = Nothing()
```

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_some` | `bool` | `True` when a value is present. |
| `is_nothing` | `bool` | `True` when no value is present. |
| `some` | `T \| None` | The inner value, or `None`. |
| `danger_some` | `T` | The inner value; asserts `is_some` (crashes on `Nothing`). |

## Methods

### `map(func) -> Option[V]`

Transform the value if present; `Nothing` passes through.

```python
Some(3).map(lambda x: x * 2)   # Some(6)
Nothing().map(lambda x: x * 2) # Nothing
```

### `and_then(func) -> Option[V]`

Chain a computation that may itself return `Nothing`.

```python
Some(4).and_then(lambda x: Some(x + 1))  # Some(5)
Some(4).and_then(lambda x: Nothing())    # Nothing
Nothing().and_then(lambda x: Some(x))   # Nothing
```

### `or_else(func) -> Option[T]`

Provide a fallback when the value is absent.

```python
Nothing().or_else(lambda: Some(0))  # Some(0)
Some(7).or_else(lambda: Some(0))    # Some(7)
```

### `inspect(func) -> Option[T]`

Run a side-effectful function on the value if present; returns `self` unchanged.

### `unwrap_or(default) -> T`

Return the value if present, otherwise return `default`.

```python
Some(3).unwrap_or(0)   # 3
Nothing().unwrap_or(0) # 0
```

## Relationship to Result

`Option[T]` is equivalent to `Result[T, Unit]` but more ergonomic when there is no
meaningful error to report. Use `Result` when the error type carries information; use
`Option` when you only care whether a value exists.
