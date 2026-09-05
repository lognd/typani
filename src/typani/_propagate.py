from __future__ import annotations

import functools
import inspect
import logging
from types import CodeType
from typing import Any, Callable, TypeVar, overload

import typani.option as _option_module
import typani.result as _result_module
from typani._exceptions import UnwrapError
from typani.result import Err, Ok, Result

F = TypeVar("F", bound=Callable[..., Any])

_log = logging.getLogger("typani.propagate")

# Source files of typani's own pure-Python unwrap/expect/danger_*/swap_*
# implementations, computed once. An `UnwrapError` raised from one of these
# frames is not itself "the decorated function's code" -- it is one level
# removed, called on the decorated function's behalf -- so the scope check
# also accepts that frame when its caller (`f_back`) is owned.
_TYPANI_INTERNAL_FILES: frozenset[str] = frozenset(
    {_result_module.__file__, _option_module.__file__}
)


def _collect_owned_codes(code: CodeType) -> frozenset[CodeType]:
    """Return *code* plus every code object reachable through `co_consts`.

    Recurses into lambdas, comprehensions, and nested `def`s so an unwrap
    lexically inside any of those still counts as "inside" the decorated
    function.
    """
    owned: set[CodeType] = set()
    stack = [code]
    while stack:
        current = stack.pop()
        if current in owned:
            continue
        owned.add(current)
        for const in current.co_consts:
            if isinstance(const, CodeType):
                stack.append(const)
    return frozenset(owned)


def _owned_codes_for(func: Callable[..., Any]) -> frozenset[CodeType] | None:
    """Compute the owned-code set for *func*, or None if it has no `__code__`."""
    code = getattr(func, "__code__", None)
    if code is None:
        _log.debug(
            "propagate: %r has no __code__ (e.g. functools.partial); "
            "falling back to unscoped propagation",
            func,
        )
        return None
    return _collect_owned_codes(code)


def _scope_check(
    exc: UnwrapError, owned: frozenset[CodeType] | None
) -> tuple[bool, Any | None]:
    """Decide whether *exc* is in scope, and return the user-code site frame.

    Returns ``(accepted, site_frame)``. ``site_frame`` is the frame whose
    ``f_lineno`` names the ``unwrap()`` call site that raised -- the
    innermost traceback frame itself for the native backend (which raises
    with no typani frame), or that frame's caller for the pure backend
    (whose innermost frame is typani's own ``unwrap`` implementation).
    ``site_frame`` is ``None`` only under the unscoped `__code__`-less
    fallback, where no lexical site was resolved at all.

    `owned is None` means the callable had no `__code__` at decoration time
    (the unscoped fallback): every `UnwrapError` is accepted, matching the
    pre-T-0028 behaviour.
    """
    if owned is None:
        return True, None

    tb = exc.__traceback__
    if tb is None:  # pragma: no cover - defensive, exceptions always have a tb here
        return False, None
    while tb.tb_next is not None:
        tb = tb.tb_next
    frame = tb.tb_frame

    if frame.f_code in owned:
        return True, frame

    if frame.f_code.co_filename in _TYPANI_INTERNAL_FILES:
        caller = frame.f_back
        if caller is not None and caller.f_code in owned:
            return True, caller

    return False, None


_DEBUG = logging.DEBUG


def _handle(
    exc: UnwrapError,
    owned: frozenset[CodeType] | None,
    func: Callable[..., Any],
    qualname: str,
    on_error: Callable[[Callable[..., Any], Any], Any] | None,
) -> Any:
    """The whole failure path of one `@propagate` hop, inlined for cost.

    Scope check, trace hop, hook and DEBUG log in one call: every helper
    call and attribute lookup here runs once per failed hop, so the pieces
    are inlined rather than layered. Re-raises when the unwrap site is not
    lexically inside *func* (only an unwrap lexically inside *func* propagates).
    """
    site_frame: Any = None
    if owned is not None:
        tb = exc.__traceback__
        while tb is not None and tb.tb_next is not None:
            tb = tb.tb_next
        if tb is None:
            raise exc
        frame = tb.tb_frame
        if frame.f_code in owned:
            site_frame = frame
        elif frame.f_code.co_filename in _TYPANI_INTERNAL_FILES:
            caller = frame.f_back
            if caller is None or caller.f_code not in owned:
                raise exc
            site_frame = caller
        else:
            raise exc
    container = exc.container
    traced = getattr(container, "traced", None)
    if traced is not None:
        site = (
            f"{qualname}:{site_frame.f_lineno}" if site_frame is not None else qualname
        )
        container = traced(site)
    if on_error is not None:
        on_error(func, container)
    if _log.isEnabledFor(_DEBUG):
        _log.debug("propagate: %s returned %r", qualname, container)
    return container


@overload
def propagate(func: F) -> F: ...
@overload
def propagate(
    func: None = None,
    *,
    on_error: Callable[[Callable[..., Any], Any], Any] | None = None,
) -> Callable[[F], F]: ...


# frob:doc docs/result.md#propagation
# frob:ticket T-0028
# frob:waive AFFECT001 reason="T-0030's only propagate() change is the OPAQUE001 functools.partial fix (internal indirection, no API/behavior change); docs/result.md#propagation is touched this diff, but README.md/docs/error_set.md/docs/redesign-0.1.md are out of T-0030's declared file scope"
def propagate(
    func: F | None = None,
    *,
    on_error: Callable[[Callable[..., Any], Any], Any] | None = None,
) -> F | Callable[[F], F]:
    """Rewrite an in-scope ``unwrap()``-raised :class:`UnwrapError` into a return.

    Decorate a function that calls ``.unwrap()`` on a :class:`~typani.result.Result`
    or :class:`~typani.option.Option`; on failure the offending container is
    returned from *func* instead of the exception escaping, giving Rust ``?`` /
    Zig ``try`` style early return. Works on plain functions, bound/unbound
    methods, and the inner function of a ``@classmethod``. Any exception other
    than ``UnwrapError`` passes through unchanged.

    Usable bare (``@propagate``) or as a factory (``@propagate(on_error=fn)``);
    *on_error*, when given, is called as ``on_error(func, container)`` right
    before the container is returned -- exceptions it raises propagate to the
    caller instead of being returned. Every catch is logged at DEBUG via the
    ``"typani.propagate"`` logger, container repr included (so notes show up).

    Scope: only an ``UnwrapError`` raised by code lexically inside *func*
    (including nested `def`s, lambdas, and comprehensions) is caught here. An
    undecorated helper that calls ``.unwrap()`` itself is out of scope -- its
    exception re-raises unchanged, loudly, rather than being silently
    attributed to the outer function. See docs/result.md#propagation.
    """
    if func is None:

        def _decorate(inner: F) -> F:
            """Bind *on_error* statically, not via a runtime `functools.partial`."""
            return propagate(  # type: ignore[call-overload,no-any-return]
                inner,  # ty: ignore[invalid-argument-type]
                on_error=on_error,
            )

        return _decorate

    owned = _owned_codes_for(func)
    qualname = getattr(func, "__qualname__", repr(func))

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except UnwrapError as exc:
                return _handle(exc, owned, func, qualname, on_error)

        return async_wrapper  # type: ignore[return-value]  # ty: ignore[invalid-return-type]

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except UnwrapError as exc:
            return _handle(exc, owned, func, qualname, on_error)

    return wrapper


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

            return async_wrapper  # type: ignore[return-value]  # ty: ignore[invalid-return-type]

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return Result.catch(
                lambda: func(*args, **kwargs), *exceptions, on_error=on_error
            )

        return wrapper  # type: ignore[return-value]  # ty: ignore[invalid-return-type]

    return decorator
