"""Tests for typani.propagate / typani.catching (sync, async, methods)."""

from __future__ import annotations

import asyncio
import re
from typing import Callable

import pytest

from typani._exceptions import UnwrapError
from typani._propagate import catching, propagate
from typani.option import Nothing, Option
from typani.result import Err, Ok, Result

# --- propagate: sync -------------------------------------------------------


# frob:tests src/typani/_propagate.py::propagate
def test_propagate_returns_err_container() -> None:
    @propagate
    def fn() -> Result[int, str]:
        Err("bad").unwrap()
        raise AssertionError("unreachable")

    r = fn()
    assert r == Err("bad")


def test_propagate_returns_ok_normally() -> None:
    @propagate
    def fn() -> Result[int, str]:
        value = Ok(1).unwrap()
        return Ok(value + 1)

    assert fn() == Ok(2)


def test_propagate_preserves_error_payload() -> None:
    """@propagate's returned container is equal to the original (T-0028: not

    necessarily the same object -- `.traced()` returns a fresh `Err` with
    one more trace entry on every catch).
    """
    original = Err("bad")

    @propagate
    def fn() -> Result[int, str]:
        original.unwrap()
        raise AssertionError("unreachable")

    result = fn()
    assert result == original
    assert len(result.trace) == 1
    assert re.fullmatch(rf"{re.escape(fn.__qualname__)}:\d+", result.trace[0])


def test_propagate_preserves_notes() -> None:
    noted = Err("bad").note("ctx")

    @propagate
    def fn() -> Result[int, str]:
        noted.unwrap()
        raise AssertionError("unreachable")

    result = fn()
    assert result.notes == ("ctx",)


def test_propagate_option() -> None:
    @propagate
    def fn() -> Option[int]:
        Nothing().unwrap()
        raise AssertionError("unreachable")

    assert fn() == Nothing()


def test_propagate_other_exceptions_pass_through() -> None:
    @propagate
    def fn() -> Result[int, str]:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        fn()


def test_unwrap_outside_propagate_escapes() -> None:
    with pytest.raises(UnwrapError):
        Err("bad").unwrap()


def test_propagate_preserves_wrapped() -> None:
    def fn() -> Result[int, str]:
        return Ok(1)

    wrapped = propagate(fn)
    assert wrapped.__wrapped__ is fn  # type: ignore[attr-defined]  # ty: ignore[unresolved-attribute]


class _Widget:
    def load(self) -> Result[int, str]:
        Err("bad").unwrap()
        raise AssertionError("unreachable")

    load = propagate(load)


# frob:tests src/typani/_propagate.py::propagate
def test_propagate_on_method() -> None:
    widget = _Widget()
    assert widget.load() == Err("bad")


# --- propagate: async -------------------------------------------------------


def test_propagate_async() -> None:
    @propagate
    async def fn() -> Result[int, str]:
        Err("bad").unwrap()
        raise AssertionError("unreachable")

    result = asyncio.run(fn())
    assert result == Err("bad")


def test_propagate_async_ok() -> None:
    @propagate
    async def fn() -> Result[int, str]:
        value = Ok(1).unwrap()
        return Ok(value + 1)

    assert asyncio.run(fn()) == Ok(2)


# --- catching: sync ----------------------------------------------------------


# frob:tests src/typani/_propagate.py::catching
def test_catching_ok() -> None:
    @catching(ZeroDivisionError, on_error=lambda e: str(e))
    def divide(a: int, b: int) -> int:
        return a // b

    assert divide(10, 2) == Ok(5)


def test_catching_err() -> None:
    @catching(ZeroDivisionError, on_error=lambda e: str(e))
    def divide(a: int, b: int) -> int:
        return a // b

    result = divide(10, 0)
    assert result.is_err  # type: ignore[attr-defined]  # ty: ignore[unresolved-attribute]


def test_catching_uncaught_exception_propagates() -> None:
    @catching(ZeroDivisionError, on_error=lambda e: str(e))
    def fn() -> int:
        raise ValueError("nope")

    with pytest.raises(ValueError, match="nope"):
        fn()


# --- catching: async -----------------------------------------------------------


def test_catching_async_ok() -> None:
    @catching(ZeroDivisionError, on_error=lambda e: str(e))
    async def divide(a: int, b: int) -> int:
        return a // b

    assert asyncio.run(divide(10, 2)) == Ok(5)


def test_catching_async_err() -> None:
    @catching(ZeroDivisionError, on_error=lambda e: str(e))
    async def divide(a: int, b: int) -> int:
        return a // b

    result = asyncio.run(divide(10, 0))
    assert result.is_err  # type: ignore[attr-defined]  # ty: ignore[unresolved-attribute]


# --- propagate: lexical scope (T-0028) --------------------------------------


# frob:tests src/typani/_propagate.py::propagate
def test_propagate_helper_unwrap_escapes() -> None:
    """An undecorated helper's unwrap must not be attributed to the caller."""

    def helper() -> int:
        return Err("bad").unwrap()  # type: ignore[return-value]

    @propagate
    def fn() -> Result[int, str]:
        value = helper()
        return Ok(value)

    with pytest.raises(UnwrapError):
        fn()


# frob:tests src/typani/_propagate.py::propagate
def test_propagate_nested_decorated_helper_works() -> None:
    """A helper decorated with its own @propagate returns its own container."""

    @propagate
    def helper() -> Result[int, str]:
        Err("bad").unwrap()
        raise AssertionError("unreachable")

    @propagate
    def fn() -> Result[int, str]:
        inner = helper()
        value = inner.unwrap()
        return Ok(value)

    assert fn() == Err("bad")


# frob:tests src/typani/_propagate.py::propagate
def test_propagate_unwrap_inside_lambda_in_body() -> None:
    @propagate
    def fn() -> Result[int, str]:
        thunk = lambda: Err("bad").unwrap()  # noqa: E731
        return Ok(thunk())

    assert fn() == Err("bad")


# frob:tests src/typani/_propagate.py::propagate
def test_propagate_unwrap_inside_comprehension_in_body() -> None:
    @propagate
    def fn() -> Result[int, str]:
        values = [Err("bad").unwrap() for _ in range(1)]
        return Ok(values[0])

    assert fn() == Err("bad")


def test_propagate_async_helper_unwrap_escapes() -> None:
    def helper() -> int:
        return Err("bad").unwrap()  # type: ignore[return-value]

    @propagate
    async def fn() -> Result[int, str]:
        value = helper()
        return Ok(value)

    with pytest.raises(UnwrapError):
        asyncio.run(fn())


def test_propagate_async_nested_decorated_helper_works() -> None:
    @propagate
    async def helper() -> Result[int, str]:
        Err("bad").unwrap()
        raise AssertionError("unreachable")

    @propagate
    async def fn() -> Result[int, str]:
        inner = await helper()
        value = inner.unwrap()
        return Ok(value)

    assert asyncio.run(fn()) == Err("bad")


# --- propagate: on_error hook and partial fallback --------------------------


# frob:tests src/typani/_propagate.py::propagate
def test_propagate_factory_bare_still_works() -> None:
    @propagate()
    def fn() -> Result[int, str]:
        Err("bad").unwrap()
        raise AssertionError("unreachable")

    assert fn() == Err("bad")


# frob:tests src/typani/_propagate.py::propagate
def test_propagate_on_error_hook_called() -> None:
    calls: list[tuple[object, object]] = []

    @propagate(on_error=lambda func, container: calls.append((func, container)))
    def fn() -> Result[int, str]:
        Err("bad").unwrap()
        raise AssertionError("unreachable")

    result = fn()
    assert result == Err("bad")
    assert len(calls) == 1
    assert calls[0][1] == Err("bad")


# frob:tests src/typani/_propagate.py::propagate
def test_propagate_on_error_hook_exception_propagates() -> None:
    def boom(func: object, container: object) -> None:
        raise RuntimeError("hook exploded")

    @propagate(on_error=boom)
    def fn() -> Result[int, str]:
        Err("bad").unwrap()
        raise AssertionError("unreachable")

    with pytest.raises(RuntimeError, match="hook exploded"):
        fn()


# frob:tests src/typani/_propagate.py::propagate
def test_propagate_partial_fallback_unscoped() -> None:
    """A callable with no __code__ (functools.partial) falls back to unscoped."""
    import functools as _functools

    def helper() -> int:
        return Err("bad").unwrap()  # type: ignore[return-value]

    def fn(_unused: int) -> Result[int, str]:
        value = helper()
        return Ok(value)

    partial_fn: Callable[[], Result[int, str]] = _functools.partial(fn, 0)
    wrapped = propagate(partial_fn)
    assert wrapped() == Err("bad")
