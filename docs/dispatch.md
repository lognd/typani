<!-- frob:describes src/typani/dispatch.py::dispatch -->
# dispatch

`dispatch(value, cases, *, default=...)` matches a value against a dict of
`{type: handler}` pairs and calls the first matching handler.  It eliminates
repetitive `isinstance` chains without requiring you to change the class hierarchy.

## Basic usage

```python
from typani.dispatch import dispatch

def describe(x: int | str | list) -> str:
    return dispatch(x, {
        int:  lambda n: f"the integer {n}",
        str:  lambda s: f"the string {s!r}",
        list: lambda l: f"a list of {len(l)} items",
    })

describe(42)          # "the integer 42"
describe("hello")     # "the string 'hello'"
describe([1, 2, 3])   # "a list of 3 items"
```

## Matching order

Cases are checked in insertion order.  The first `isinstance(value, key)` match wins.
This matters when a value could match multiple keys -- put more specific types before
more general ones:

```python
class Animal: ...
class Dog(Animal): ...

dispatch(Dog(), {
    Dog:    lambda d: "dog",    # checked first -- matches
    Animal: lambda a: "animal",
})
# returns "dog"

dispatch(Dog(), {
    Animal: lambda a: "animal",  # checked first -- also matches Dog!
    Dog:    lambda d: "dog",
})
# returns "animal"
```

## Default for unmatched types

By default, `dispatch` raises `TypeError` when no case matches.  Pass `default=...`
to return a fallback value instead:

```python
dispatch(3.14, {int: lambda n: n * 2}, default="unknown")
# "unknown"
```

## When to use `dispatch` vs `Sum`

| | `dispatch` | `Sum` |
|---|---|---|
| Declare the closed set of types upfront | No | Yes |
| Raises if a variant is missing | No | Yes |
| Works on types you do not own | Yes | Yes |
| Requires changing the class hierarchy | No | Optional |

Use `dispatch` for open-ended matching where exhaustiveness is not a requirement.
Use `Sum` when you own the variant types and want the compiler to catch missed cases.

## API

| Name | Kind | Description |
|------|------|-------------|
| `dispatch(value, cases, *, default=...)` | function | Iterates `cases` in order; calls the first matching handler.  Raises `TypeError` if no match and no default. |
