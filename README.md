# typani

A small collection of utility types for Python 3.10+, extracted from real projects.
Inspired by Rust's `Result`/`Option`, Zig's error sets, and functional pipelines.

```
pip install typani
```

Pydantic integration (`SingletonModel`) is optional:

```
pip install typani[pydantic]
```

---

## `Result[T, E]` -- explicit success or failure

[Full docs](https://github.com/lognd/typani/blob/main/docs/result.md)

Tired of `try/except` chains that silently swallow errors, or functions that return
`None` and leave the caller guessing why?  `Result` makes the failure path a
first-class value.

```python
from typani import Ok, Err, Result

def parse_port(s: str) -> Result[int, str]:
    try:
        port = int(s)
    except ValueError:
        return Err(f"{s!r} is not a number")
    if not (1 <= port <= 65535):
        return Err(f"{port} is out of range 1-65535")
    return Ok(port)
```

The real power is chaining -- build a pipeline without nesting:

```python
from typani import Ok, Err, Result

def read_env(key: str) -> Result[str, str]:
    import os
    val = os.getenv(key)
    return Ok(val) if val is not None else Err(f"missing env var {key!r}")

def parse_int(s: str) -> Result[int, str]:
    return Ok(int(s)) if s.isdigit() else Err(f"not an integer: {s!r}")

port: Result[int, str] = (
    read_env("PORT")         # Result[str, str]
    >> parse_int             # Result[int, str]  -- and_then
    | (lambda p: p * 2)     # Result[int, str]  -- map (hypothetical transform)
)

match port:
    case _ if port.is_ok:
        print(f"port is {port.ok}")
    case _:
        print(f"error: {port.err}")
```

`|` is `map` (transform the success value), `>>` is `and_then` (chain a fallible
step).  Errors short-circuit the chain automatically -- no `if result.is_err: return
result` noise at every step.

---

## `Option[T]` -- explicit presence or absence

[Full docs](https://github.com/lognd/typani/blob/main/docs/option.md)

`T | None` is untracked by the type checker in many real codebases.  `Option[T]` is
a real container: the type checker forces you to handle the absent case.

```python
from typani import Some, Nothing, Option

def find_user(users: dict[int, str], uid: int) -> Option[str]:
    return Some(users[uid]) if uid in users else Nothing()
```

Chain transformations without checking at every step:

```python
users = {1: "alice", 2: "bob"}

display = (
    find_user(users, 1)          # Some("alice")
    | str.upper                  # Some("ALICE")
    | (lambda s: f"User: {s}")   # Some("User: ALICE")
)
print(display.unwrap_or("unknown"))  # "User: ALICE"

missing = (
    find_user(users, 99)         # Nothing
    | str.upper                  # Nothing (map skips Nothing)
)
print(missing.unwrap_or("unknown"))  # "unknown"
```

`Nothing` short-circuits the whole chain just like `Err` does in `Result`.

---

## `ErrorSet` -- Zig-inspired typed error enums

[Full docs](https://github.com/lognd/typani/blob/main/docs/error_set.md)

Define errors with human-readable descriptions attached, combine them with `|`, and
use them as `Result` error types -- all without accidentally comparing them to raw
strings.  `A | B` and `B | A` return the exact same cached class object.

```python
from typani import ErrorSet, Ok, Err, Result

class NetworkError(ErrorSet):
    Timeout   = "connection timed out after the deadline"
    Refused   = "remote host refused the connection"
    DnsFailure = "could not resolve hostname"

class ParseError(ErrorSet):
    InvalidJson = "payload is not valid JSON"
    MissingKey  = "required key not present in payload"

# Merge into a single "global" error set -- like Zig's || operator
AppError = NetworkError | ParseError

def fetch_config(url: str) -> Result[dict, AppError]:
    ...

err = NetworkError.Timeout
print(err.description)  # "connection timed out after the deadline"
print(str(err))         # "NetworkError.Timeout: connection timed out after the deadline"
print(repr(err))        # "NetworkError.Timeout"
```

Why not `StrEnum`?  `StrEnum` makes members equal to their string value
(`NetworkError.Timeout == "Timeout"` is `True`), which blurs the line between domain
errors and raw strings and makes exhaustiveness checking unreliable.  `ErrorSet`
keeps description strings internal and never exposes them as the member's identity.
It also works on Python 3.10+ -- `StrEnum` requires 3.11.

---

## `Sum[A, B, ...]` -- exhaustive tagged unions

[Full docs](https://github.com/lognd/typani/blob/main/docs/sum.md)

Replace `isinstance` chains with a single `match` call that the type checker can
verify is exhaustive:

```python
from dataclasses import dataclass
from typani import Sum

@dataclass
class Circle:
    radius: float

@dataclass
class Square:
    side: float

@dataclass
class Triangle:
    base: float
    height: float

Shape = Sum[Circle, Triangle, Square]

def area(shape: Shape) -> float:
    return Shape.match(shape, {
        Circle:   lambda c: 3.14159 * c.radius ** 2,
        Triangle: lambda t: 0.5 * t.base * t.height,
        Square:   lambda s: s.side ** 2,
    })
```

`match` raises `TypeError` if any variant is missing from the dict -- you cannot
forget a case.  Compare to the equivalent `isinstance` version, which silently falls
through to `None` if you add a new variant and forget to update every dispatch site.

---

## `dispatch` -- dict-based isinstance dispatch

[Full docs](https://github.com/lognd/typani/blob/main/docs/dispatch.md)

For when you want the `Sum` dispatch style but can't or don't want to change the
class hierarchy:

```python
from typani import dispatch

def describe(value: int | str | list) -> str:
    return dispatch(value, {
        int:  lambda n: f"the integer {n}",
        str:  lambda s: f"the string {s!r}",
        list: lambda l: f"a list of {len(l)} items",
    })
```

First matching type wins (subclasses before base classes).  Pass `default=...` to
handle unknown types instead of raising `TypeError`.

---

## `@singleton` -- singleton semantics for any class

[Full docs](https://github.com/lognd/typani/blob/main/docs/singleton.md)

The decorator works on regular classes, classes with existing bases, and Pydantic
`BaseModel` subclasses.  No metaclass conflicts.

```python
from pydantic import BaseModel
from typani import singleton

@singleton
class AppConfig(BaseModel):
    debug: bool = False
    host: str = "localhost"
    port: int = 8080

# First call -- constructs and caches
cfg = AppConfig(debug=True, host="prod.example.com", port=9000)

# Every subsequent call -- returns the same object, ignores new args
same = AppConfig(debug=False)
assert cfg is same    # True
assert same.debug     # True -- first call's values are kept
```

`class AppConfig(BaseModel, Singleton)` would raise a `TypeError` at import time
because Python resolves metaclass conflicts before any Python code can run.
`@singleton` sidesteps this by creating the merged metaclass *after* the class
exists, then producing a thin subclass using it.

Use `strict=True` to raise instead of silently returning the cached instance:

```python
@singleton(strict=True)
class Database:
    def __init__(self, url: str) -> None:
        self.url = url

db = Database("postgres://localhost/mydb")
Database("sqlite://")   # RuntimeError: Database is a strict singleton...
```

Also available as base classes when you don't need Pydantic:

```python
from typani import Singleton, StrictSingleton

class AppConfig(Singleton): ...         # silent return on re-instantiation
class Database(StrictSingleton): ...    # RuntimeError on re-instantiation
Database.instance()                     # retrieves the one created instance
```

---

## `SingletonModel` -- Pydantic BaseModel + singleton

[Full docs](https://github.com/lognd/typani/blob/main/docs/singleton.md)

For the `class Cfg(SingletonModel): ...` style without the decorator:

```python
from typani import SingletonModel
from pydantic import Field

class AppConfig(SingletonModel):
    debug: bool = False
    host: str = "localhost"
    port: int = Field(default=8080, ge=1, le=65535)

cfg = AppConfig(debug=True, host="prod.example.com", port=9000)
assert AppConfig() is cfg  # True
```

Requires `pip install typani[pydantic]`.

---

## `Unit` -- zero-size marker type

[Full docs](https://github.com/lognd/typani/blob/main/docs/unit.md)

The Python equivalent of Rust's `()`.  Use it as the success value of a `Result`
that has no data to return, or as a lightweight sentinel.

```python
from typani import Unit, Ok, Result

def write_file(path: str, data: bytes) -> Result[Unit, str]:
    try:
        with open(path, "wb") as f:
            f.write(data)
        return Ok(Unit())
    except OSError as e:
        return Err(str(e))
```

`Unit` forces `__slots__ = ()` on every subclass -- instances carry no attributes and
cannot accidentally grow state.

---

## `Unreachable` -- exhaustiveness sentinel

[Full docs](https://github.com/lognd/typani/blob/main/docs/unreachable.md)

Works with `typing.assert_never` to get static exhaustiveness checking.  Raises
`AssertionError` with a location-aware message if it is ever actually reached at
runtime.

```python
from typing import assert_never
from typani import Unreachable

def handle(value: int | str) -> str:
    if isinstance(value, int):
        return str(value)
    elif isinstance(value, str):
        return value
    else:
        assert_never(value)   # mypy/pyright error if value can be anything else
        Unreachable()         # TypeError the moment this line is reached
```

---

## Requirements

- Python 3.10+
- pydantic>=2.0 (optional, for `SingletonModel`)

## License

MIT
