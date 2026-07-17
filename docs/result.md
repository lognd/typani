<!-- frob:describes src/typani/result.py::Result -->
# Result

`Result[T, E]` models a computation that either succeeds with a value of type `T` or
fails with an error of type `E`. It is inspired by Rust's `Result<T, E>`.

Exactly one of `ok` or `err` is set; constructing a `Result` with both or neither
raises `TypeError`.

<!-- frob:describes src/typani/result.py::Ok -->
<!-- frob:describes src/typani/result.py::Err -->
## Constructors

Use the convenience functions instead of `Result(...)` directly:

```python
from typani.result import Ok, Err, Result

ok: Result[int, str] = Ok(42)
err: Result[int, str] = Err("something went wrong")
```

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_ok` | `bool` | `True` when the result holds a success value. |
| `is_err` | `bool` | `True` when the result holds an error. |
| `ok` | `T \| None` | The success value, or `None`. |
| `err` | `E \| None` | The error value, or `None`. |
| `danger_ok` | `T` | The success value; asserts `is_ok` (crashes on `Err`). |
| `danger_err` | `E` | The error value; asserts `is_err` (crashes on `Ok`). |

## Methods

### `map(func) -> Result[V, E]`

Transform the success value; errors pass through unchanged.

```python
Ok(5).map(lambda x: x * 2)   # Ok(10)
Err("e").map(lambda x: x * 2)  # Err('e')
```

### `map_err(func) -> Result[T, F]`

Transform the error value; successes pass through unchanged.

### `and_then(func) -> Result[V, E | F]`

Chain a fallible operation. If `self` is `Ok`, calls `func` and returns its result.
If `self` or the inner result is `Err`, the first error is propagated.

```python
Ok(3).and_then(lambda x: Ok(x + 1))          # Ok(4)
Ok(3).and_then(lambda x: Err("inner"))        # Err('inner')
Err("outer").and_then(lambda x: Ok(x + 1))   # Err('outer')
```

### `or_else(func) -> Result[T, F]`

Recover from an error. If `self` is `Err`, calls `func(err)` and returns its result.
If `self` is `Ok`, returns `self` unchanged.

### `inspect(func) -> Result[T, E]`

Run a side-effectful function on the success value without transforming it. Returns
`self` unchanged regardless.

### `swap_err(err_type) -> Result[T, F]`

Assert-cast the error type. Only valid when `is_ok`; asserts otherwise.

### `swap_ok(ok_type) -> Result[V, E]`

Assert-cast the success type. Only valid when `is_err`; asserts otherwise.
