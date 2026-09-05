"""Tests for typani.propagate / typani.catching (sync, async, methods)."""

from __future__ import annotations

import asyncio

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


def test_propagate_same_object_identity() -> None:
    original = Err("bad")

    @propagate
    def fn() -> Result[int, str]:
        original.unwrap()
        raise AssertionError("unreachable")

    assert fn() is original


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
