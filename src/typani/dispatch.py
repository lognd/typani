from __future__ import annotations

from typing import Any, Callable, TypeVar

R = TypeVar("R")

_MISSING = object()


def dispatch(
    value: object,
    cases: dict[type[Any], Callable[[Any], R]],
    *,
    default: R | object = _MISSING,
) -> R:
    """Match *value* against a dict of ``{type: handler}`` pairs.

    Iterates *cases* in insertion order and calls the first handler whose key
    is a superclass of ``type(value)`` (i.e. ``isinstance(value, key)`` is
    ``True``).  If no case matches:

    * Returns *default* if provided.
    * Raises ``TypeError`` otherwise.

    This eliminates chains of ``if isinstance(x, A): ... elif isinstance(x,
    B): ...`` boilerplate when you need exhaustive type dispatch.

    Example::

        from typani.dispatch import dispatch

        def describe(x: int | str | list[object]) -> str:
            return dispatch(x, {
                int: lambda n: f"number {n}",
                str: lambda s: f"string '{s}'",
                list: lambda l: f"list of {len(l)} items",
            })

    Note that subclasses match their parent keys, so order matters when a
    value could match multiple entries.
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
