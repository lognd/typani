<!-- frob:describes src/typani/sum.py::Sum -->
# Sum

`Sum[A, B, C]` is a tagged-union base class with exhaustive dispatch.  It replaces
chains of `isinstance` checks with a single `match` call that raises `TypeError` if
any declared variant is missing from the handler dict.

## Defining a sum type

Subscript `Sum` with the variant types you want to close over:

```python
from dataclasses import dataclass
from typani.sum import Sum

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
```

`Shape` is now a class whose `_variants` tuple is `(Circle, Triangle, Square)`.

## Exhaustive dispatch with `match`

```python
import math

def area(shape: Shape) -> float:
    return Shape.match(shape, {
        Circle:   lambda c: math.pi * c.radius ** 2,
        Triangle: lambda t: 0.5 * t.base * t.height,
        Square:   lambda s: s.side ** 2,
    })

print(area(Circle(radius=1.0)))   # 3.14159...
print(area(Square(side=4.0)))     # 16.0
```

If you omit a variant, `match` raises immediately with a clear message -- you cannot
forget a case silently:

```python
Shape.match(shape, {
    Circle:   lambda c: "round",
    Triangle: lambda t: "pointy",
    # Square missing!
})
# TypeError: Non-exhaustive match on Shape: missing handlers for Square
```

Compare to the equivalent `isinstance` version:

```python
# Old way -- adding a new variant and forgetting this function gives no error
if isinstance(shape, Circle):
    ...
elif isinstance(shape, Triangle):
    ...
# Square falls through to None silently
```

## Allowing a default

Pass `default=...` to allow unhandled variants without raising:

```python
label = Shape.match(shape, {
    Circle: lambda c: "round",
}, default="other")
```

## Membership check with `check`

```python
Shape.check(Circle(radius=1.0))   # True
Shape.check("hello")              # False
```

## Relationship to `dispatch`

`Sum.match` calls `dispatch` internally.  The difference is that `Sum` declares the
closed set of types upfront and enforces coverage at every call site.  Use `dispatch`
directly when you do not own the types or do not want to enforce exhaustiveness.

## API

| Name | Kind | Description |
|------|------|-------------|
| `Sum[A, B, ...]` | subscript | Returns a new `Sum` subclass with `_variants = (A, B, ...)`. |
| `Sum.match(value, cases, *, default=...)` | classmethod | Exhaustive dispatch; raises `TypeError` if any variant is uncovered and no default is given. |
| `Sum.check(value)` | classmethod | `True` if `value` is an instance of any declared variant. |
