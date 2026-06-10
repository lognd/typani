# Unreachable

`Unreachable` is a `Unit` subclass that raises `TypeError` the moment it is
instantiated. It is a compile-time sentinel meant to be used only in type
annotations -- if code ever tries to create one at runtime, you have a bug.

The error message includes the source file, line number, and function name of the
call site.

## Usage

```python
from typani.unreachable import Unreachable
from typing import assert_never

def handle(value: int | str) -> str:
    if isinstance(value, int):
        return str(value)
    elif isinstance(value, str):
        return value
    else:
        # This branch is statically unreachable; mypy/pyright will verify it.
        assert_never(value)
        raise Unreachable()  # never actually called
```

You can also use it as a return type annotation for functions that must never
return normally:

```python
def panic(msg: str) -> Unreachable:
    raise RuntimeError(msg)
```

## API

| Name | Kind | Description |
|------|------|-------------|
| `Unreachable` | `@final` class | Raises `TypeError` on instantiation with a location-aware message. |
