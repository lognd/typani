# Singleton

`typani` provides three ways to make a class a singleton, plus a strict variant
that raises on second instantiation instead of silently returning the cached instance.

## `@singleton` decorator (recommended)

The decorator works on **any** class -- regular Python classes, classes with existing
base classes, and Pydantic `BaseModel` subclasses -- without any metaclass conflicts:

```python
from typani.singleton import singleton

@singleton
class AppConfig:
    def __init__(self, debug: bool = False) -> None:
        self.debug = debug

cfg1 = AppConfig(debug=True)
cfg2 = AppConfig(debug=False)   # returns the same object
assert cfg1 is cfg2             # True
assert cfg1.debug               # True -- first-call values are kept
```

### With Pydantic `BaseModel`

```python
from pydantic import BaseModel, Field
from typani.singleton import singleton

@singleton
class AppConfig(BaseModel):
    debug: bool = False
    host: str = Field(default="localhost")
    port: int = 8080

cfg = AppConfig(debug=True, host="prod.example.com")
AppConfig()                     # returns the same object
assert AppConfig().debug        # True
```

Pydantic field validation, `Field(...)` descriptors, and all other model features
work normally on the first construction. Subsequent calls return the cached instance
without re-running validation.

### Strict mode

Pass `strict=True` to raise `RuntimeError` instead of silently returning the cached
instance on second instantiation:

```python
@singleton(strict=True)
class Database:
    def __init__(self, url: str) -> None:
        self.url = url

db = Database("postgres://...")   # OK
Database("sqlite://...")          # RuntimeError: Database is a strict singleton...
```

## `Singleton` base class

For simple cases with no existing base classes, inheriting from `Singleton` is
the most concise option:

```python
from typani.singleton import Singleton

class AppConfig(Singleton):
    def __init__(self) -> None:
        self.debug = False

assert AppConfig() is AppConfig()
```

`Singleton` uses `SingletonMeta` as its metaclass, which conflicts with Pydantic's
`ModelMetaclass`. Use the `@singleton` decorator when combining with Pydantic or
any other class that has its own metaclass.

## `StrictSingleton` base class

`StrictSingleton` uses `StrictSingletonMeta` and raises `RuntimeError` on any
second instantiation attempt. It also provides a `.instance()` classmethod:

```python
from typani.singleton import StrictSingleton

class Database(StrictSingleton):
    def __init__(self, url: str) -> None:
        self.url = url

db = Database("postgres://...")   # OK
Database.instance()               # returns the existing instance
Database("sqlite://...")          # RuntimeError!
```

`.instance()` raises `LookupError` if the singleton has not been created yet.

## `SingletonModel`

`SingletonModel` is a Pydantic `BaseModel` subclass that provides singleton
semantics via a pre-merged metaclass. It is an alternative to `@singleton` for
Pydantic models and keeps the `class Cfg(SingletonModel): ...` style:

```python
from typani.singleton import SingletonModel

class AppConfig(SingletonModel):
    debug: bool = False
```

Requires `pydantic>=2.0`.

## Why `@singleton` works with Pydantic but `(BaseModel, Singleton)` does not

Python resolves metaclasses at class-creation time and raises `TypeError` if two
bases have incompatible metaclasses (`SingletonMeta` and Pydantic's `ModelMetaclass`
are incompatible). This error fires before any Python code in `typani` can intervene.

`@singleton` sidesteps this by dynamically creating a merged metaclass from
`SingletonMeta` and `type(cls)` *after* the class already exists, then producing a
thin subclass of the original using that merged metaclass.

## API

| Name | Kind | Description |
|------|------|-------------|
| `@singleton` | decorator | Makes any class a singleton. Accepts `strict=True`. |
| `Singleton` | class | Base class; uses `SingletonMeta`. |
| `SingletonMeta` | metaclass | Returns cached instance on every `__call__`. |
| `StrictSingleton` | class | Base class; raises on second instantiation. Has `.instance()`. |
| `StrictSingletonMeta` | metaclass | Raises `RuntimeError` on second `__call__`. |
| `SingletonModel` | class | Pydantic `BaseModel` + singleton. Requires `pydantic>=2.0`. |
