# typani

A small collection of utility types for Python 3.10+, extracted from real projects. Inspired by Rust and Zig.

```
pip install typani
```

Pydantic integration (`SingletonModel`) requires pydantic>=2.0 as an optional dependency:

```
pip install typani[pydantic]
```

---

## Types

### `Result[T, E]`

An explicit success-or-failure container. Replaces bare exceptions for expected failure paths.

```python
from typani import Ok, Err, Result

def parse(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"not a number: {s!r}")

result = parse("42")
if result.is_ok:
    print(result.ok)  # 42

# Operator shortcuts
doubled = parse("5") | (lambda x: x * 2)      # map
chained = parse("5") >> (lambda x: parse("3")) # and_then
```

| Method | Description |
|---|---|
| `is_ok` / `is_err` | Check which variant |
| `ok` / `err` | Unwrap to `T` or `None` |
| `danger_ok` / `danger_err` | Assert-unwrap (crashes on wrong variant) |
| `map(f)` / `\|` | Transform the success value |
| `map_err(f)` | Transform the error value |
| `and_then(f)` / `>>` | Chain a fallible computation |
| `or_else(f)` | Recover from an error |
| `inspect(f)` | Side-effect on success, return self |
| `swap_ok(t)` / `swap_err(t)` | Re-type the absent side |

---

### `Option[T]`

An explicit present-or-absent container. A composable alternative to `T | None`.

```python
from typani import Some, Nothing, Option

def find(items: list[str], key: str) -> Option[str]:
    return Some(key) if key in items else Nothing()

opt = find(["a", "b"], "a")
if opt.is_some:
    print(opt.some)  # "a"

upper = opt | str.upper          # map
length = opt >> (lambda s: Some(len(s)))  # and_then
```

| Method | Description |
|---|---|
| `is_some` / `is_nothing` | Check which variant |
| `some` | Unwrap to `T` or `None` |
| `danger_some` | Assert-unwrap |
| `map(f)` / `\|` | Transform the value if present |
| `and_then(f)` / `>>` | Chain an optional computation |
| `or_else(f)` | Supply a fallback |
| `unwrap_or(default)` | Unwrap with a default |
| `inspect(f)` | Side-effect if present, return self |

---

### `ErrorSet`

An enum where each member's value is a human-readable description string. Inspired by Zig error sets.

Better than `StrEnum`: members are never accidentally equal to raw strings, and it works on Python 3.10+.

```python
from typani import ErrorSet, merge

class NetworkError(ErrorSet):
    Timeout    = "connection timed out"
    Refused    = "connection refused"

class ParseError(ErrorSet):
    InvalidJson = "invalid JSON payload"
    MissingKey  = "required key not present"

# Merge into a single set (like Zig's error set union)
AppError = merge(NetworkError, ParseError, name="AppError")

def fetch(url: str) -> Result[str, AppError]:
    ...

err = NetworkError.Timeout
print(err.description)  # "connection timed out"
print(str(err))         # "NetworkError.Timeout: connection timed out"

# Merge with | operator at the class level
Combined = NetworkError | ParseError
```

---

### `Sum[A, B, ...]`

A tagged-union base class for exhaustive dispatch. Replaces `isinstance` chains.

```python
from typani import Sum

class Shape(Sum[Circle, Square, Triangle]):
    pass

def area(shape: Shape) -> float:
    return shape.match({
        Circle:   lambda c: 3.14159 * c.r ** 2,
        Square:   lambda s: s.side ** 2,
        Triangle: lambda t: 0.5 * t.base * t.height,
    })
```

`match` raises `TypeError` if any variant is missing from the dict.  Use `check` to validate the dict without calling anything.

---

### `dispatch`

Lightweight dict-based dispatch without the `Sum` base class requirement.

```python
from typani import dispatch

result = dispatch(value, {
    int:   lambda n: f"integer: {n}",
    str:   lambda s: f"string: {s}",
    float: lambda f: f"float: {f}",
})
```

Pass `default=...` to allow unmatched types instead of raising `TypeError`.

---

### `Singleton` / `SingletonMeta`

A base class (or metaclass) that ensures at most one instance is ever created.

```python
from typani import Singleton

class AppConfig(Singleton):
    def __init__(self) -> None:
        self.debug = False

cfg1 = AppConfig()
cfg2 = AppConfig()
assert cfg1 is cfg2  # True
```

---

### `@singleton`

A decorator that adds singleton semantics to any class, including Pydantic `BaseModel` subclasses. Solves the metaclass conflict that prevents `class Cfg(BaseModel, Singleton)`.

```python
from pydantic import BaseModel
from typani import singleton

@singleton
class AppConfig(BaseModel):
    debug: bool = False
    host: str = "localhost"
    port: int = 8080

cfg1 = AppConfig(debug=True, host="prod.example.com", port=9000)
cfg2 = AppConfig()
assert cfg1 is cfg2     # True
assert cfg2.debug       # True -- first call's values are kept
```

Use `@singleton(strict=True)` to raise `RuntimeError` on any second instantiation attempt instead of silently returning the cached instance.

---

### `SingletonModel`

A `pydantic.BaseModel` subclass with singleton semantics built in. Requires `pydantic>=2.0`.

```python
from typani import SingletonModel
from pydantic import Field

class AppConfig(SingletonModel):
    debug: bool = False
    host: str = "localhost"
    port: int = Field(default=8080, ge=1, le=65535)

cfg1 = AppConfig(debug=True)
cfg2 = AppConfig()
assert cfg1 is cfg2  # True
```

---

### `StrictSingleton` / `StrictSingletonMeta`

Like `Singleton`, but raises `RuntimeError` on any second instantiation. Retrieval is via `.instance()`.

```python
from typani import StrictSingleton

class Database(StrictSingleton):
    def __init__(self, url: str) -> None:
        self.url = url

db = Database("postgres://localhost/mydb")
Database("sqlite://")        # RuntimeError -- already instantiated
Database.instance()          # returns the original db
```

---

### `Unit`

A zero-size type with no attributes. Useful as a sentinel or as the success type of a `Result` that carries no value.

```python
from typani import Unit, Ok, Result

def save(data: bytes) -> Result[Unit, str]:
    ...
    return Ok(Unit())
```

All subclasses are forced to `__slots__ = ()`.

---

### `Unreachable`

Raises `AssertionError` when instantiated. Use as the argument to `typing.assert_never` to get exhaustiveness checking from your type checker.

```python
from typing import assert_never
from typani import Unreachable

def handle(x: int | str) -> str:
    if isinstance(x, int):
        return str(x)
    elif isinstance(x, str):
        return x
    else:
        raise Unreachable(x)
```

---

## Requirements

- Python 3.10+
- pydantic>=2.0 (optional, for `SingletonModel`)

## License

MIT
