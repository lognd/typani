<!-- frob:describes src/typani/error_set.py::ErrorSet -->
# ErrorSet

`ErrorSet` is a Zig-inspired typed error enum where each member carries a human-readable
description string. In Zig, error sets are lightweight, composable, and named -- `ErrorSet`
brings the same idea to Python with the added ability to attach a description to each error.

## Defining an error set

Subclass `ErrorSet` and assign description strings as values:

```python
from typani.error_set import ErrorSet

class NetworkError(ErrorSet):
    Timeout = "Connection timed out after the deadline"
    Refused = "Remote host actively refused the connection"
    DnsFailure = "Could not resolve the hostname"
```

## Accessing descriptions

```python
e = NetworkError.Timeout
e.description   # "Connection timed out after the deadline"
str(e)          # "Timeout: Connection timed out after the deadline"
repr(e)         # "NetworkError.Timeout"
```

## Using with Result

`ErrorSet` members work naturally as the error type in `Result[T, E]`:

```python
from typani.result import Ok, Err, Result

def connect(host: str) -> Result[str, NetworkError]:
    if not host:
        return Err(NetworkError.DnsFailure)
    return Ok(f"connected to {host}")

result = connect("")
if result.is_err:
    print(result.err)   # DnsFailure: Could not resolve the hostname
```

<!-- frob:describes src/typani/error_set.py::merge -->
## Global / merged error sets

In Zig, error sets can be unioned together with the `||` operator.  `ErrorSet`
supports the same idea via `|` directly on the classes:

```python
class ParseError(ErrorSet):
    InvalidJson = "payload is not valid JSON"
    MissingKey  = "required key not present"

AllErrors = NetworkError | ParseError

AllErrors.Timeout.description    # "Connection timed out after the deadline"
AllErrors.InvalidJson.description  # "payload is not valid JSON"
```

The result is **cached and commutative** -- `NetworkError | ParseError` and
`ParseError | NetworkError` return the exact same class object.  Chains flatten
correctly too: `(A | B) | C` is identical to `A | B | C`.

The auto-generated name sorts the inputs alphabetically:
`NetworkError | ParseError` produces `NetworkError_ParseError`.

`|` raises `ValueError` if any error name appears in both sets -- duplicate names
are ambiguous, just as in Zig.

### Custom name with `merge`

Use `merge` when you want a specific name or are combining more than two sets:

```python
from typani.error_set import merge

AppError = merge(NetworkError, ParseError, AuthError, name="AppError")
```

## Why not `StrEnum`?

`enum.StrEnum` (added in Python 3.11) makes members compare equal to their string
value (`NetworkError.Timeout == "Timeout"`). That is convenient for serialisation but
creates a footgun: errors silently compare equal to arbitrary strings, making
exhaustiveness checking unreliable and blurring the boundary between the error domain
and raw data.

`ErrorSet` keeps values as plain strings *internally* (for the description) but never
makes members equal to those strings. Identity and enum-level equality are the only
comparisons that work, which is exactly right when errors are first-class domain
values rather than serialisation tokens.

## Python 3.10 compatibility

`StrEnum` requires Python 3.11+. `ErrorSet` is built on the plain `enum.Enum` API
that has been stable since Python 3.4, so it runs on Python 3.10 and up with no
compatibility shims.

## Iteration and membership

Because `ErrorSet` extends `enum.Enum`, all standard enum operations work:

```python
list(NetworkError)                          # all members
NetworkError["Timeout"]                     # lookup by name
NetworkError.Timeout in list(NetworkError)  # membership test
```

## API

| Name | Kind | Description |
|------|------|-------------|
| `ErrorSet` | `Enum` subclass | Base class for typed error sets. Assign `str` values to members. |
| `.description` | property | Returns the description assigned at definition time. |
| `str(member)` | method | `"Name: description"` |
| `repr(member)` | method | `"ClassName.Name"` |
| `SetA \| SetB` | operator | Cached, commutative merge. Auto-names result alphabetically. Chains flatten. |
| `merge(*sets, name=...)` | function | Merge with a custom name; useful for 3+ sets or explicit naming. |
