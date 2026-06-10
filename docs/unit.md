# Unit

`Unit` is a zero-slot base class. Any subclass of `Unit` is guaranteed to carry no
instance attributes (the metaclass forces `__slots__ = ()` on every class in the
hierarchy). It is the Python equivalent of Rust's `()` type or Haskell's `Unit` -- a
type with exactly one value, useful only for its presence.

## Usage

```python
from typani.unit import Unit

class MyMarker(Unit): ...

m = MyMarker()
```

Setting attributes on a `Unit` instance raises `AttributeError` because slots are empty
and there is no `__dict__`.

## Why it exists

Several types in `typani` (e.g. `Unreachable`, `Result`'s internal sentinels) need
lightweight marker values that carry no state. Inheriting from `Unit` enforces that
constraint automatically -- no way for a subclass to accidentally add fields.

## API

| Name | Kind | Description |
|------|------|-------------|
| `UnitMeta` | metaclass | Forces `__slots__ = ()` on every class it creates. |
| `Unit` | class | Base class; uses `UnitMeta`. Inherit from this directly. |
