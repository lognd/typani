from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, TypeVar

from typani._exceptions import UnwrapError
from typani.result import Err, Ok, Result

F = TypeVar("F", bound=Callable[..., Any])


# frob:doc docs/result.md#propagation
# frob:ticket T-0009
def propagate(func: F) -> F:
    """Rewrite an ``unwrap()``-raised :class:`UnwrapError` into a returned container.

    Decorate a function that calls ``.unwrap()`` on a :class:`~typani.result.Result`
    or :class:`~typani.option.Option`; on failure the offending container is
    returned from *func* instead of the exception escaping, giving Rust ``?`` /
    Zig ``try`` style early return. Works on plain functions, bound/unbound
    methods, and the inner function of a ``@classmethod``. Any exception other
    than ``UnwrapError`` passes through unchanged.
    """
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except UnwrapError as exc:
                return exc.container

        return async_wrapper  # type: ignore[return-value]

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except UnwrapError as exc:
            return exc.container

    return wrapper  # type: ignore[return-value]


# frob:doc docs/result.md#catch
# frob:ticket T-0009
def catching(
    *exceptions: type[BaseException],
    on_error: Callable[[BaseException], Any],
) -> Callable[[F], F]:
    """Decorator factory: wrap a whole function in :meth:`Result.catch` semantics.

    Equivalent to calling ``Result.catch(lambda: func(*a, **kw), *exceptions,
    on_error=on_error)`` on every call. Supports both sync and async functions.
    """

    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return Ok(await func(*args, **kwargs))
                except tuple(exceptions or (Exception,)) as exc:
                    return Err(on_error(exc))

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return Result.catch(
                lambda: func(*args, **kwargs), *exceptions, on_error=on_error
            )

        return wrapper  # type: ignore[return-value]

    return decorator
