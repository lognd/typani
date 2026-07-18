from __future__ import annotations

from typing import Any, Callable, TypeVar

R = TypeVar("R")

_MISSING = object()


# frob:doc docs/dispatch.md#basic-usage
# frob:ticket T-0003
def dispatch(
    value: object,
    cases: dict[type[Any], Callable[[Any], R]],
    *,
    default: R | object = _MISSING,
) -> R:
    """Match *value* against a dict of ``{type: handler}`` pairs.

    Iterates *cases* in insertion order and calls the first handler whose key
    is a superclass of ``type(value)`` (``isinstance(value, key)``).  Returns
    *default* if provided and nothing matches; raises ``TypeError`` otherwise.
    Subclasses match their parent keys, so order matters when a value could
    match multiple entries.  See :doc:`docs/dispatch.md` for a worked example.
    """
    for typ, func in cases.items():
        if isinstance(value, typ):
            return func(value)
    if default is not _MISSING:
        return default  # type: ignore[return-value]
    raise TypeError(
        f"dispatch: no handler for type {type(value).__name__!r} "
        f"and no default provided"
    )
